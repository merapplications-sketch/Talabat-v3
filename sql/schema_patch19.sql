-- Patch 19: customer support (tickets with messages), second-restaurant requests, customers tab with suspension
-- Run once in Supabase SQL Editor AFTER patch 18, then upload the files. Safe to re-run.
--
-- NEW / CHANGED ROW LEVEL SECURITY
--   support_tickets / ticket_messages : a customer reads only HIS tickets and their messages; the admin reads all.
--       Nobody writes directly (no write policy): create_ticket / ticket_reply / ticket_staff_reply / ticket_set_status decide everything.
--   store_requests : the owner reads his own requests, the admin reads all. Writes only through request_store / decide_store_request.
--   app_texts (support phone and hours) : readable by every signed-in user, written only by the admin through set_text_setting().
--   profiles : banned_at / banned_reason can be changed ONLY by the admin (added to the guard trigger, so a suspended customer cannot lift it himself).
--   admin_customers() / set_customer_ban() : admin only (they return nothing / refuse for everybody else).

------------------------------------------------------------------------------------------------
-- 1) PROFILES: suspension columns + phone check on every self-edit
------------------------------------------------------------------------------------------------
alter table profiles add column if not exists banned_at timestamptz;
alter table profiles add column if not exists banned_reason text;
create index if not exists profiles_created_idx on profiles (created_at desc);

create or replace function guard_profile() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin() then return new; end if;
  if new.role <> old.role or new.driver_status is distinct from old.driver_status
     or new.cash_limit <> old.cash_limit or new.accept_blocked <> old.accept_blocked
     or new.banned_at is distinct from old.banned_at or new.banned_reason is distinct from old.banned_reason then
    raise exception 'not_allowed';
  end if;
  return new;
end $$;

-- a phone written straight into the profile is normalized or refused (patch 18 only checked the RPC)
create or replace function trg_profile_phone() returns trigger language plpgsql set search_path = public as $$
declare v_p text;
begin
  if new.phone is distinct from old.phone then
    if new.phone is null or btrim(new.phone) = '' then new.phone := null; return new; end if;
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
  end if;
  return new;
end $$;
drop trigger if exists trg_profile_phone on profiles;
create trigger trg_profile_phone before update of phone on profiles for each row execute function trg_profile_phone();

drop trigger if exists trg_audit_profiles on profiles;
create trigger trg_audit_profiles after update on profiles for each row
  execute function audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked', 'banned_at', 'banned_reason');

------------------------------------------------------------------------------------------------
-- 2) SUPPORT PHONE / HOURS (shown to customers)
------------------------------------------------------------------------------------------------
create table if not exists app_texts (
  key text primary key check (key in ('support_phone', 'support_hours')),
  value text not null default '' check (char_length(value) <= 60),
  updated_at timestamptz not null default now(),
  updated_by uuid
);
insert into app_texts(key, value) values ('support_phone', ''), ('support_hours', '') on conflict (key) do nothing;
alter table app_texts enable row level security;
drop policy if exists texts_read on app_texts;
create policy texts_read on app_texts for select using (auth.uid() is not null);

create or replace function set_text_setting(p_key text, p_value text) returns void
language plpgsql security definer set search_path = public as $$
declare v_v text := btrim(coalesce(p_value, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_key = 'support_phone' then
    if v_v <> '' then v_v := norm_phone(v_v); if v_v is null then raise exception 'bad_phone'; end if; end if;
  elsif p_key = 'support_hours' then
    if char_length(v_v) > 60 then raise exception 'bad_value'; end if;
  else raise exception 'bad_value';
  end if;
  update app_texts set value = v_v, updated_at = now(), updated_by = auth.uid() where key = p_key;
end $$;
revoke all on function set_text_setting(text, text) from public, anon;
grant execute on function set_text_setting(text, text) to authenticated;
drop trigger if exists trg_audit_texts on app_texts;
create trigger trg_audit_texts after update on app_texts for each row execute function audit_changes('key', 'value');

------------------------------------------------------------------------------------------------
-- 3) SUPPORT TICKETS (conversation between the customer and the administration)
------------------------------------------------------------------------------------------------
create table if not exists support_tickets (
  id bigint generated always as identity primary key,
  customer_id uuid not null references profiles(id) on delete cascade,
  order_id bigint references orders(id) on delete set null,
  reason text not null check (reason in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other')),
  status text not null default 'open' check (status in ('open', 'in_progress', 'resolved', 'rejected')),
  refund_amount numeric check (refund_amount is null or (refund_amount >= 0 and refund_amount <= 100000)),
  admin_note text check (admin_note is null or char_length(admin_note) <= 300),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_customer_at timestamptz not null default now(),
  last_staff_at timestamptz,
  customer_seen_at timestamptz,
  closed_at timestamptz,
  handled_by uuid references profiles(id)
);
create index if not exists tickets_customer_idx on support_tickets (customer_id, created_at desc);
create index if not exists tickets_status_idx on support_tickets (status, updated_at desc);
create unique index if not exists tickets_one_open_per_order on support_tickets (order_id) where order_id is not null and status in ('open', 'in_progress');
create table if not exists ticket_messages (
  id bigint generated always as identity primary key,
  ticket_id bigint not null references support_tickets(id) on delete cascade,
  from_staff boolean not null default false,
  sender_id uuid not null references profiles(id),
  body text not null check (char_length(btrim(body)) between 1 and 500),
  created_at timestamptz not null default now()
);
create index if not exists ticket_msgs_idx on ticket_messages (ticket_id, created_at);
alter table support_tickets enable row level security;
alter table ticket_messages enable row level security;
drop policy if exists tickets_read on support_tickets;
drop policy if exists ticket_msgs_read on ticket_messages;
create policy tickets_read on support_tickets for select using (customer_id = auth.uid() or is_admin());
create policy ticket_msgs_read on ticket_messages for select
  using (is_admin() or exists (select 1 from support_tickets t where t.id = ticket_id and t.customer_id = auth.uid()));
do $$ begin
  begin alter publication supabase_realtime add table support_tickets; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table ticket_messages; exception when duplicate_object then null; end;
end $$;

create or replace function create_ticket(p_order bigint, p_reason text, p_message text) returns bigint
language plpgsql security definer set search_path = public as $$
declare v_o orders; v_id bigint; v_msg text := btrim(coalesce(p_message, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if p_reason is null or p_reason not in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other') then
    raise exception 'bad_value';
  end if;
  if char_length(v_msg) < 5 or char_length(v_msg) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from support_tickets where customer_id = auth.uid() and status in ('open', 'in_progress')) >= 5
     or (select count(*) from support_tickets where customer_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then
    raise exception 'too_many';
  end if;
  if p_order is not null then
    select * into v_o from orders where id = p_order and customer_id = auth.uid();
    if not found then raise exception 'not_allowed'; end if;
    if v_o.status in ('delivered', 'rejected', 'cancelled') and coalesce(v_o.done_at, v_o.created_at) < now() - interval '48 hours' then
      raise exception 'ticket_expired';                    -- reports are accepted for 48 hours after the order ends
    end if;
  end if;
  begin
    insert into support_tickets(customer_id, order_id, reason) values (auth.uid(), p_order, p_reason) returning id into v_id;
  exception when unique_violation then
    raise exception 'ticket_exists';                       -- one open ticket per order
  end;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (v_id, false, auth.uid(), v_msg);
  return v_id;
end $$;
revoke all on function create_ticket(bigint, text, text) from public, anon;
grant execute on function create_ticket(bigint, text, text) to authenticated;

create or replace function ticket_reply(p_ticket bigint, p_body text) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket and customer_id = auth.uid();
  if not found then raise exception 'not_allowed'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  if (select count(*) from ticket_messages where ticket_id = p_ticket and sender_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many';
  end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, false, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_customer_at = now(), customer_seen_at = now() where id = p_ticket;
end $$;
revoke all on function ticket_reply(bigint, text) from public, anon;
grant execute on function ticket_reply(bigint, text) to authenticated;

create or replace function ticket_seen(p_ticket bigint) returns void
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update support_tickets set customer_seen_at = now() where id = p_ticket and customer_id = auth.uid();
end $$;
revoke all on function ticket_seen(bigint) from public, anon;
grant execute on function ticket_seen(bigint) to authenticated;

create or replace function ticket_staff_reply(p_ticket bigint, p_body text) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, true, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         status = case when status = 'open' then 'in_progress' else status end where id = p_ticket;
end $$;
revoke all on function ticket_staff_reply(bigint, text) from public, anon;
grant execute on function ticket_staff_reply(bigint, text) to authenticated;

-- close or reopen a ticket; an approved refund amount is only RECORDED here (it will go to the in-app wallet when that exists)
create or replace function ticket_set_status(p_ticket bigint, p_status text, p_note text default null, p_refund numeric default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_max numeric;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  if p_refund is not null then
    if p_status <> 'resolved' or p_refund < 0 then raise exception 'bad_value'; end if;
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      if p_refund > coalesce(v_max, 0) then raise exception 'bad_value'; end if;   -- never more than the order was worth
    end if;
  end if;
  update support_tickets set status = p_status,
         admin_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''),
         refund_amount = case when p_status = 'resolved' then p_refund else null end,
         updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         closed_at = case when p_status in ('resolved', 'rejected') then now() else null end
   where id = p_ticket;
end $$;
revoke all on function ticket_set_status(bigint, text, text, numeric) from public, anon;
grant execute on function ticket_set_status(bigint, text, text, numeric) to authenticated;

drop trigger if exists trg_audit_tickets on support_tickets;
create trigger trg_audit_tickets after update on support_tickets for each row execute function audit_changes('id', 'status', 'refund_amount');

------------------------------------------------------------------------------------------------
-- 4) REQUEST ANOTHER RESTAURANT (a restaurant owner asks, the admin verifies ownership and approves)
------------------------------------------------------------------------------------------------
create table if not exists store_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  name text not null check (char_length(btrim(name)) between 2 and 80),
  category text not null check (category in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets')),
  phone text not null check (phone ~ '^\+992[0-9]{9}$'),
  address text check (address is null or char_length(address) <= 200),
  lat float8 not null check (lat between -90 and 90),
  lng float8 not null check (lng between -180 and 180),
  note text check (note is null or char_length(note) <= 500),
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  admin_note text check (admin_note is null or char_length(admin_note) <= 300),
  store_id uuid references stores(id) on delete set null,
  created_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by uuid references profiles(id)
);
create index if not exists store_req_user_idx on store_requests (user_id, created_at desc);
create index if not exists store_req_status_idx on store_requests (status, created_at);
alter table store_requests enable row level security;
drop policy if exists store_req_read on store_requests;
create policy store_req_read on store_requests for select using (user_id = auth.uid() or is_admin());
do $$ begin
  begin alter publication supabase_realtime add table store_requests; exception when duplicate_object then null; end;
end $$;

create or replace function request_store(p_name text, p_category text, p_phone text, p_address text, p_lat float8, p_lng float8, p_note text default null) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_id uuid; v_ph text := norm_phone(p_phone); v_name text := btrim(coalesce(p_name, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from profiles where id = auth.uid() and role = 'merchant') then raise exception 'not_allowed'; end if;
  if char_length(v_name) < 2 or char_length(v_name) > 80 or p_category not in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets') then raise exception 'bad_value'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  if char_length(coalesce(p_address, '')) > 200 or char_length(coalesce(p_note, '')) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from store_requests where user_id = auth.uid() and status = 'pending') >= 3
     or (select count(*) from store_requests where user_id = auth.uid() and created_at > now() - interval '1 day') >= 5 then
    raise exception 'too_many';
  end if;
  insert into store_requests(user_id, name, category, phone, address, lat, lng, note)
  values (auth.uid(), v_name, p_category, v_ph, nullif(btrim(coalesce(p_address, '')), ''), p_lat, p_lng, nullif(btrim(coalesce(p_note, '')), ''))
  returning id into v_id;
  return v_id;
end $$;
revoke all on function request_store(text, text, text, text, float8, float8, text) from public, anon;
grant execute on function request_store(text, text, text, text, float8, float8, text) to authenticated;

-- approving creates the restaurant for that owner but keeps it HIDDEN (inactive, closed) until the admin sets the commission and fees
create or replace function decide_store_request(p_id uuid, p_approve boolean, p_note text default null) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_r store_requests; v_store uuid; v_note text := nullif(left(btrim(coalesce(p_note, '')), 300), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select * into v_r from store_requests where id = p_id and status = 'pending' for update;
  if not found then raise exception 'bad_transition'; end if;
  if coalesce(p_approve, false) then
    insert into stores(name, category, phone, address, lat, lng, owner_id, commission_pct, fee_type, fee_base, is_active, is_open)
    values (v_r.name, v_r.category, v_r.phone, v_r.address, v_r.lat, v_r.lng, v_r.user_id, 10, 'fixed', 10, false, false)
    returning id into v_store;
  elsif v_note is null then
    raise exception 'note_required';
  end if;
  update store_requests set status = case when coalesce(p_approve, false) then 'approved' else 'rejected' end,
         admin_note = v_note, store_id = v_store, decided_at = now(), decided_by = auth.uid() where id = p_id;
  return v_store;
end $$;
revoke all on function decide_store_request(uuid, boolean, text) from public, anon;
grant execute on function decide_store_request(uuid, boolean, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 5) CUSTOMERS (admin): list with search and totals, suspension
------------------------------------------------------------------------------------------------
create or replace function admin_customers(p_q text default null, p_limit int default 30, p_offset int default 0)
returns table(id uuid, name text, phone text, email text, created_at timestamptz, orders_count bigint, total_spent numeric,
              last_order_at timestamptz, banned_at timestamptz, banned_reason text)
language sql stable security definer set search_path = public as $$
  select p.id, p.name, p.phone, u.email::text, p.created_at, coalesce(o.cnt, 0), coalesce(o.spent, 0), o.last_at, p.banned_at, p.banned_reason
    from profiles p
    left join auth.users u on u.id = p.id
    left join lateral (select count(*) filter (where x.status = 'delivered') as cnt,
                              coalesce(sum(x.total) filter (where x.status = 'delivered'), 0) as spent,
                              max(x.created_at) as last_at
                         from orders x where x.customer_id = p.id) o on true
   where is_admin() and p.role = 'customer'
     and (coalesce(btrim(p_q), '') = '' or p.name ilike '%' || btrim(p_q) || '%' or p.phone ilike '%' || btrim(p_q) || '%' or u.email ilike '%' || btrim(p_q) || '%')
   order by p.created_at desc
   limit least(greatest(coalesce(p_limit, 30), 1), 50) offset greatest(coalesce(p_offset, 0), 0)
$$;
revoke all on function admin_customers(text, int, int) from public, anon;
grant execute on function admin_customers(text, int, int) to authenticated;

create or replace function set_customer_ban(p_id uuid, p_banned boolean, p_reason text default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_reason text := nullif(left(btrim(coalesce(p_reason, '')), 200), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if not exists (select 1 from profiles where id = p_id and role = 'customer') then raise exception 'not_found'; end if;
  if coalesce(p_banned, false) and (v_reason is null or char_length(v_reason) < 3) then raise exception 'note_required'; end if;
  update profiles set banned_at = case when coalesce(p_banned, false) then now() end,
                      banned_reason = case when coalesce(p_banned, false) then v_reason end where id = p_id;
end $$;
revoke all on function set_customer_ban(uuid, boolean, text) from public, anon;
grant execute on function set_customer_ban(uuid, boolean, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 6) place_order: a suspended customer cannot order (same signature as patch 18)
------------------------------------------------------------------------------------------------
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  -- idempotency: a retry of the SAME attempt (bad network, double tap) returns the order that already exists
  if p_key is not null then
    if p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    if found then return v_id; end if;
  end if;
  -- abuse guard: at most 20 orders per hour per customer
  if (select count(*) from orders where customer_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many_orders';
  end if;
  -- spam / abuse guard: at most 5 unfinished orders per customer
  if (select count(*) from orders where customer_id = auth.uid() and status in ('pending', 'preparing', 'ready', 'pickedup')) >= 5 then
    raise exception 'too_many_orders';
  end if;
  if (p_lat is not null and (p_lat < -90 or p_lat > 90)) or (p_lng is not null and (p_lng < -180 or p_lng > 180)) then
    raise exception 'bad_value';
  end if;
  -- a delivery address (text + map point) is mandatory
  if p_lat is null or p_lng is null or char_length(btrim(coalesce(p_address, ''))) < 3 then
    raise exception 'address_required';
  end if;
  select * into s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  if not s.is_open then raise exception 'closed'; end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) > 60 then raise exception 'bad_value'; end if;
  select * into pr from profiles where id = auth.uid();

  -- the customer phone is required (stored privately, see order_customer_phone) and the fee is calculated here, never by the app
  if pr.banned_at is not null then raise exception 'account_blocked'; end if;   -- a suspended account cannot order
  v_cphone := norm_phone(pr.phone);
  if v_cphone is null then raise exception 'phone_required'; end if;
  v_dq := delivery_calc(p_store, p_lat, p_lng, auth.uid());
  v_fee := (v_dq->>'fee')::numeric;
  v_pay := case s.fee_type when 'free' then s.fee_base else (v_dq->>'fee_full')::numeric end;   -- courier is always paid; the platform covers free delivery
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);

  -- every line is priced by the DATABASE: base price + the chosen options (validated against the item's own option groups)
  for it in select (x->>'item_id')::uuid as item_id,
                   least(50, greatest(1, (x->>'qty')::int)) as qty,
                   left(coalesce(x->>'note', ''), 120) as note,
                   case when jsonb_typeof(x->'options') = 'array' then x->'options' else '[]'::jsonb end as opts
              from jsonb_array_elements(p_items) x loop
    select * into v_item from menu_items where id = it.item_id and store_id = p_store and available and approved;
    if not found then raise exception 'unavailable'; end if;
    pl := price_line(it.item_id, it.opts);
    insert into order_items(order_id, item_id, name, price, qty, note, options)
    values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap');
  end loop;

  -- each line gets the better of the store discount and its own item discount (they do not stack)
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0)) = 0), 0)
    into v_sub, v_disc, v_base
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc, delivery_fee = v_fee, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo,
    total = greatest(5, v_sub - v_disc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;
  return v_id;
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric) to authenticated;
