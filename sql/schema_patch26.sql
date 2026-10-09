-- ============================================================
-- schema_patch26.sql : staff roles (RBAC) for the admin panel
-- * Super admin (profiles.role = 'admin') keeps everything.
-- * Staff get ONLY the permissions listed in staff_members.perms:
--     orders   - see all orders, assign a courier, cancel/reject, prep time, order phones
--     support  - tickets + replies + capped refunds, customers list, ban, ratings, read customer profiles
--     finance  - courier cash balances + settle, manual wallet adjust, wallet read
--     stores   - view/create/edit stores (NOT delete, NOT commission/discount), menu + item approval
--     content  - banners, promo codes, texts, About/Privacy pages
-- * NEVER delegated (admin only): owners, roles, app settings, staff management, audit log,
--   commission/discount changes, store-request decisions, customer phone override.
-- Safe to run twice.
-- ============================================================
begin;

create table if not exists staff_members (
  user_id    uuid primary key references profiles(id) on delete cascade,
  perms      text[] not null default '{}',
  active     boolean not null default true,
  created_by uuid references profiles(id),
  created_at timestamptz not null default now(),
  constraint staff_perms_valid check (perms <@ array['orders','support','finance','stores','content']::text[])
);
alter table staff_members enable row level security;
drop policy if exists staff_read on staff_members;
create policy staff_read on staff_members for select to public using (user_id = auth.uid() or is_admin());
-- no insert/update/delete policy: only the SECURITY DEFINER functions below can change this table
revoke insert, update, delete on staff_members from anon, authenticated;

create or replace function has_perm(p text) returns boolean
language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (
    exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms)))
$$;

-- what the signed-in user may do in the admin panel: null = nothing, all five for super admin
create or replace function my_perms() returns text[]
language sql stable security definer set search_path = public as $$
  select case
    when auth.uid() is null then null
    when exists(select 1 from profiles where id = auth.uid() and role = 'admin') then array['orders','support','finance','stores','content']
    else (select s.perms from staff_members s where s.user_id = auth.uid() and s.active and cardinality(s.perms) > 0)
  end
$$;

create or replace function staff_list() returns table(user_id uuid, email text, name text, perms text[], active boolean, created_at timestamptz)
language sql stable security definer set search_path = public as $$
  select s.user_id, u.email::text, p.name, s.perms, s.active, s.created_at
    from staff_members s join profiles p on p.id = s.user_id left join auth.users u on u.id = s.user_id
   where is_admin() order by s.created_at
$$;

create or replace function staff_set(p_email text, p_perms text[], p_active boolean default true) returns void
language plpgsql security definer set search_path = public as $$
declare u uuid; v_role user_role; v_perms text[];
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if coalesce(btrim(p_email), '') = '' or char_length(p_email) > 120 or p_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then raise exception 'bad_value'; end if;
  select array(select distinct x from unnest(coalesce(p_perms, '{}')) x order by x) into v_perms;
  if not (v_perms <@ array['orders','support','finance','stores','content']::text[]) then raise exception 'bad_value'; end if;
  if cardinality(v_perms) = 0 and coalesce(p_active, true) then raise exception 'bad_value'; end if;
  select id into u from auth.users where lower(email) = lower(btrim(p_email));
  if u is null then raise exception 'user_not_found'; end if;
  select role into v_role from profiles where id = u;
  if v_role is null then raise exception 'user_not_found'; end if;
  if v_role = 'admin' then raise exception 'bad_value'; end if;                      -- admins already have everything
  if u = auth.uid() then raise exception 'bad_value'; end if;
  if (select count(*) from staff_members) >= 30 and not exists(select 1 from staff_members where user_id = u) then raise exception 'too_many'; end if;
  insert into staff_members(user_id, perms, active, created_by) values (u, v_perms, coalesce(p_active, true), auth.uid())
  on conflict (user_id) do update set perms = excluded.perms, active = excluded.active;
  insert into audit_log(user_id, action, table_name, row_id, details)
  values (auth.uid(), 'STAFF_SET', 'staff_members', u::text, jsonb_build_object('perms', v_perms, 'active', coalesce(p_active, true)));
end $$;

create or replace function staff_remove(p_user uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  delete from staff_members where user_id = p_user;
  if not found then raise exception 'not_found'; end if;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'STAFF_REMOVE', 'staff_members', p_user::text, '{}'::jsonb);
end $$;

revoke all on function staff_set(text, text[], boolean), staff_remove(uuid), staff_list() from public, anon;
grant execute on function staff_set(text, text[], boolean), staff_remove(uuid), staff_list() to authenticated;
grant execute on function has_perm(text), my_perms() to anon, authenticated;

-- ---- functions: the "is_admin()" check becomes "has_perm(...)" only where listed ----
CREATE OR REPLACE FUNCTION public.ticket_staff_reply(p_ticket bigint, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, true, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         status = case when status = 'open' then 'in_progress' else status end where id = p_ticket;
end $function$
;

CREATE OR REPLACE FUNCTION public.ticket_set_status(p_ticket bigint, p_status text, p_note text DEFAULT NULL::text, p_refund numeric DEFAULT NULL::numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_max numeric; v_cred numeric; v_prev numeric; v_ref numeric := case when p_refund is null then null else round(p_refund, 2) end;
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  if p_status = 'rejected' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;   -- the customer must be told why
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  select amount into v_cred from wallet_entries where ticket_id = p_ticket and kind = 'refund';
  if v_ref is not null then
    if p_status <> 'resolved' or v_ref < 0 then raise exception 'bad_value'; end if;
    if v_ref > 0 and v_cred is not null then raise exception 'already_refunded'; end if;   -- one refund per ticket
    if v_ref > 0 and v_t.order_id is null then raise exception 'refund_needs_order'; end if;  -- a refund needs an order to be measured against
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      select coalesce(sum(amount), 0) into v_prev from wallet_entries where order_id = v_t.order_id and kind = 'refund';
      if v_ref + v_prev > coalesce(v_max, 0) then raise exception 'refund_too_high'; end if;   -- never more than the order was worth, over all its tickets
    end if;
  end if;
  update support_tickets set status = p_status,
         admin_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''),
         refund_amount = coalesce(v_cred, case when p_status = 'resolved' and v_ref > 0 then v_ref end),
         updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         closed_at = case when p_status in ('resolved', 'rejected') then now() else null end
   where id = p_ticket;
  -- the approved refund goes to the customer's wallet in the same moment (atomic with closing the ticket)
  if v_ref > 0 and v_cred is null then
    insert into wallet_entries(user_id, amount, kind, ticket_id, order_id, note, created_by)
    values (v_t.customer_id, v_ref, 'refund', p_ticket, v_t.order_id, left(coalesce(p_note, ''), 200), auth.uid());
  end if;
end $function$
;

CREATE OR REPLACE FUNCTION public.ticket_refund_room(p_ticket bigint)
 RETURNS TABLE(order_total numeric, refunded numeric, room numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.total,
         coalesce(w.sum_refunded, 0),
         greatest(0, o.total - coalesce(w.sum_refunded, 0))
    from support_tickets t
    join orders o on o.id = t.order_id
    left join lateral (select sum(x.amount) as sum_refunded from wallet_entries x where x.order_id = o.id and x.kind = 'refund') w on true
   where t.id = p_ticket and has_perm('support')
$function$
;

CREATE OR REPLACE FUNCTION public.admin_customers(p_q text DEFAULT NULL::text, p_limit integer DEFAULT 30, p_offset integer DEFAULT 0)
 RETURNS TABLE(id uuid, name text, phone text, email text, created_at timestamp with time zone, orders_count bigint, total_spent numeric, last_order_at timestamp with time zone, banned_at timestamp with time zone, banned_reason text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.id, p.name, p.phone, u.email::text, p.created_at, coalesce(o.cnt, 0), coalesce(o.spent, 0), o.last_at, p.banned_at, p.banned_reason
    from profiles p
    left join auth.users u on u.id = p.id
    left join lateral (select count(*) filter (where x.status = 'delivered') as cnt,
                              coalesce(sum(x.total) filter (where x.status = 'delivered'), 0) as spent,
                              max(x.created_at) as last_at
                         from orders x where x.customer_id = p.id) o on true
   where has_perm('support') and p.role = 'customer'
     and (coalesce(btrim(p_q), '') = '' or p.name ilike '%' || btrim(p_q) || '%' or p.phone ilike '%' || btrim(p_q) || '%' or u.email ilike '%' || btrim(p_q) || '%')
   order by p.created_at desc
   limit least(greatest(coalesce(p_limit, 30), 1), 50) offset greatest(coalesce(p_offset, 0), 0)
$function$
;

CREATE OR REPLACE FUNCTION public.set_customer_ban(p_id uuid, p_banned boolean, p_reason text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_reason text := nullif(left(btrim(coalesce(p_reason, '')), 200), '');
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if not exists (select 1 from profiles where id = p_id and role = 'customer') then raise exception 'not_found'; end if;
  if coalesce(p_banned, false) and (v_reason is null or char_length(v_reason) < 3) then raise exception 'note_required'; end if;
  perform set_config('app.bypass', '1', true);   -- guard_profile blocks non-admins; this function has already checked the permission and the target
  update profiles set banned_at = case when coalesce(p_banned, false) then now() end,
                      banned_reason = case when coalesce(p_banned, false) then v_reason end where id = p_id;
  perform set_config('app.bypass', '', true);
end $function$
;

CREATE OR REPLACE FUNCTION public.resolve_rating(p_order bigint, p_note text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  update ratings set handled_at = now(), handled_by = auth.uid(), handled_note = nullif(left(btrim(coalesce(p_note, '')), 300), '')
   where order_id = p_order and handled_at is null;
  if not found then raise exception 'not_found'; end if;
end $function$
;

CREATE OR REPLACE FUNCTION public.reopen_rating(p_order bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  update ratings set handled_at = null, handled_by = null, handled_note = null where order_id = p_order;
end $function$
;

CREATE OR REPLACE FUNCTION public.admin_assign_driver(p_order bigint, p_driver uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_name text; v_phone text;
begin
  if not has_perm('orders') then raise exception 'not_allowed'; end if;
  select name, phone into v_name, v_phone from profiles where id = p_driver and role = 'driver' and driver_status = 'approved';
  if not found then raise exception 'not_approved'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  update orders set driver_id = p_driver, driver_name = v_name
   where id = p_order and driver_id is null and status in ('preparing', 'ready');
  if not found then raise exception 'bad_transition'; end if;
  update order_offers set state = case when driver_id = p_driver then 'accepted' else 'cancelled' end
   where order_id = p_order and state = 'pending';
  insert into order_driver_phone(order_id, phone) values (p_order, norm_phone(v_phone))
    on conflict (order_id) do update set phone = excluded.phone;
end $function$
;

CREATE OR REPLACE FUNCTION public.set_prep_time(p_id bigint, p_min integer)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not exists(select 1 from orders o where o.id = p_id and o.status in ('pending','preparing')
                and (owns_store(o.store_id) or has_perm('orders'))) then
    raise exception 'not_allowed';
  end if;
  update orders set prep_time = least(90, greatest(5, p_min)) where id = p_id;
end $function$
;

CREATE OR REPLACE FUNCTION public.cash_balances()
 RETURNS TABLE(driver_id uuid, balance numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.driver_id, coalesce(sum(o.cash_collected), 0)::numeric
    from orders o
   where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null
     and o.driver_id is not null and (has_perm('finance') or o.driver_id = auth.uid())
   group by o.driver_id
$function$
;

CREATE OR REPLACE FUNCTION public.settle_driver_cash(p_driver uuid)
 RETURNS numeric
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare tot numeric;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  select coalesce(sum(cash_collected), 0) into tot from orders
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  update orders set cash_settled_at = now()
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  return tot;
end $function$
;

CREATE OR REPLACE FUNCTION public.wallet_adjust(p_user uuid, p_amount numeric, p_note text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_a numeric := round(coalesce(p_amount, 0), 2); v_note text := btrim(coalesce(p_note, ''));
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if v_a = 0 or abs(v_a) > 100000 or char_length(v_note) < 3 or char_length(v_note) > 200 then raise exception 'bad_value'; end if;
  perform 1 from profiles where id = p_user and role = 'customer' for update;
  if not found then raise exception 'not_found'; end if;
  if v_a < 0 and wallet_balance(p_user) + v_a < 0 then raise exception 'insufficient_funds'; end if;
  insert into wallet_entries(user_id, amount, kind, note, created_by) values (p_user, v_a, 'adjust', v_note, auth.uid());
end $function$
;

CREATE OR REPLACE FUNCTION public.set_store_open(p_store uuid, p_open boolean)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (owns_store(p_store) or has_perm('stores')) then raise exception 'not_allowed'; end if;
  update stores set is_open = p_open where id = p_store;
end $function$
;

CREATE OR REPLACE FUNCTION public.update_my_store(p_store uuid, p_description text, p_cover text, p_logo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (owns_store(p_store) or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if (p_cover is not null and char_length(p_cover) > 700000) or (p_logo is not null and char_length(p_logo) > 700000) then
    raise exception 'bad_value';
  end if;
  update stores
     set description = left(coalesce(p_description, description), 300),
         cover_url   = coalesce(p_cover, cover_url),
         logo_url    = coalesce(p_logo, logo_url)
   where id = p_store;
end $function$
;

CREATE OR REPLACE FUNCTION public.guard_item_approval()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if new.approved and not old.approved and auth.uid() is not null and not has_perm('stores')
     and current_setting('app.bypass', true) is distinct from '1' then
    raise exception 'not_allowed';
  end if;
  return new;
end $function$
;

CREATE OR REPLACE FUNCTION public.item_approval()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is not null and not has_perm('stores')
     and exists(select 1 from stores where id = new.store_id and category = 'pharmacy') then
    new.approved := false;   -- pharmacy items appear only after admin approval
  end if;
  return new;
end $function$
;

CREATE OR REPLACE FUNCTION public.store_private()
 RETURNS TABLE(id uuid, owner_id uuid, commission_pct numeric, max_discount_pct numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.owner_id, s.commission_pct, s.max_discount_pct
    from stores s where has_perm('stores') or s.owner_id = auth.uid()
$function$
;

CREATE OR REPLACE FUNCTION public.set_text_setting(p_key text, p_value text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_v text := btrim(coalesce(p_value, ''));
begin
  if not has_perm('content') then raise exception 'not_allowed'; end if;
  if p_key = 'support_phone' then
    if v_v <> '' then v_v := norm_phone(v_v); if v_v is null then raise exception 'bad_phone'; end if; end if;
  elsif p_key = 'support_hours' then
    if char_length(v_v) > 60 then raise exception 'bad_value'; end if;
  else raise exception 'bad_value';
  end if;
  update app_texts set value = v_v, updated_at = now(), updated_by = auth.uid() where key = p_key;
end $function$
;

CREATE OR REPLACE FUNCTION public.set_page(p_slug text, p_lang text, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_b text := coalesce(p_body, '');
begin
  if not has_perm('content') then raise exception 'not_allowed'; end if;
  if p_slug not in ('about', 'privacy') or p_lang not in ('ru', 'en') or char_length(v_b) > 20000 then raise exception 'bad_value'; end if;
  if p_lang = 'ru' then
    update app_pages set body_ru = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  else
    update app_pages set body_en = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  end if;
end $function$
;

CREATE OR REPLACE FUNCTION public.can_see_order(o bigint)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select exists(select 1 from orders r where r.id = o and (
     r.customer_id = auth.uid() or r.driver_id = auth.uid() or owns_store(r.store_id) or (has_perm('orders') or has_perm('support'))
     or (r.driver_id is null and r.status in ('preparing', 'ready') and exists(
          select 1 from order_offers f where f.order_id = r.id and f.driver_id = auth.uid()
             and f.state = 'pending' and f.expires_at > now())))) $function$
;

CREATE OR REPLACE FUNCTION public.order_contacts(p_order bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_o orders; v_cp text; v_dp text; v_active boolean;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into v_o from orders where id = p_order;
  if not found then return '{}'::jsonb; end if;
  v_active := v_o.status in ('preparing', 'ready', 'pickedup');
  select phone into v_cp from order_customer_phone where order_id = p_order;
  select phone into v_dp from order_driver_phone where order_id = p_order;
  if (has_perm('orders') or has_perm('support')) then return jsonb_build_object('customer_phone', v_cp, 'driver_phone', v_dp); end if;
  return jsonb_build_object(
    'customer_phone', case when v_active and v_o.driver_id = auth.uid() then v_cp end,
    'driver_phone', case when v_active and v_o.driver_id is not null and (v_o.customer_id = auth.uid() or owns_store(v_o.store_id)) then v_dp end);
end $function$
;

CREATE OR REPLACE FUNCTION public.contacts_for(p_ids bigint[])
 RETURNS TABLE(order_id bigint, customer_phone text, driver_phone text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select t.i, cp.phone, dp.phone
    from unnest(case when cardinality(p_ids) > 200 then p_ids[1:200] else p_ids end) as t(i)
    left join order_customer_phone cp on cp.order_id = t.i
    left join order_driver_phone dp on dp.order_id = t.i
   where (has_perm('orders') or has_perm('support'))
$function$
;

CREATE OR REPLACE FUNCTION public.wallet_balance(p_user uuid DEFAULT NULL::uuid)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(w.amount), 0)::numeric
    from wallet_entries w
   where w.user_id = coalesce(p_user, auth.uid())
     and (coalesce(p_user, auth.uid()) = auth.uid() or (has_perm('support') or has_perm('finance')))
$function$
;

CREATE OR REPLACE FUNCTION public.set_order_status(p_id bigint, p_to order_status)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; ok boolean := false;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if is_admin() then ok := true;
  elsif has_perm('orders') and p_to in ('cancelled','rejected') then ok := o.status in ('pending','preparing','ready','pickedup');
  elsif o.customer_id = auth.uid() then ok := (o.status = 'pending' and p_to = 'cancelled');
  elsif owns_store(o.store_id) then
    ok := (o.status = 'pending' and p_to in ('preparing','rejected')) or (o.status = 'preparing' and p_to = 'ready');
  elsif o.driver_id = auth.uid() then
    ok := (o.status = 'ready' and p_to = 'pickedup');
  end if;
  if not ok then raise exception 'bad_transition'; end if;
  update orders set status = p_to,
    done_at = case when p_to in ('delivered','rejected','cancelled') then now() else null end where id = p_id;
end $function$
;

-- ---- policies ----
drop policy if exists "tickets_read" on public.support_tickets;
create policy "tickets_read" on public.support_tickets for SELECT to public
  using (((customer_id = auth.uid()) OR has_perm('support')));

drop policy if exists "ticket_msgs_read" on public.ticket_messages;
create policy "ticket_msgs_read" on public.ticket_messages for SELECT to public
  using ((has_perm('support') OR (EXISTS ( SELECT 1
   FROM support_tickets t
  WHERE ((t.id = ticket_messages.ticket_id) AND (t.customer_id = auth.uid()))))));

drop policy if exists "ratings_read" on public.ratings;
create policy "ratings_read" on public.ratings for SELECT to public
  using (((customer_id = auth.uid()) OR has_perm('support')));

drop policy if exists "offers_read" on public.order_offers;
create policy "offers_read" on public.order_offers for SELECT to public
  using (((driver_id = auth.uid()) OR has_perm('orders')));

drop policy if exists "stores_read" on public.stores;
create policy "stores_read" on public.stores for SELECT to public
  using ((is_active OR (owner_id = auth.uid()) OR has_perm('stores')));

drop policy if exists "items_read" on public.menu_items;
create policy "items_read" on public.menu_items for SELECT to public
  using (((available AND approved AND (EXISTS ( SELECT 1
   FROM stores s
  WHERE ((s.id = menu_items.store_id) AND s.is_active)))) OR owns_store(store_id) OR has_perm('stores')));

drop policy if exists "items_write" on public.menu_items;
create policy "items_write" on public.menu_items for ALL to public
  using ((owns_store(store_id) OR has_perm('stores')))
  with check ((owns_store(store_id) OR has_perm('stores')));

drop policy if exists "iog_write" on public.item_option_groups;
create policy "iog_write" on public.item_option_groups for ALL to public
  using ((EXISTS ( SELECT 1
   FROM menu_items m
  WHERE ((m.id = item_option_groups.item_id) AND (owns_store(m.store_id) OR has_perm('stores'))))))
  with check ((EXISTS ( SELECT 1
   FROM menu_items m
  WHERE ((m.id = item_option_groups.item_id) AND (owns_store(m.store_id) OR has_perm('stores'))))));

drop policy if exists "io_write" on public.item_options;
create policy "io_write" on public.item_options for ALL to public
  using ((EXISTS ( SELECT 1
   FROM (item_option_groups g
     JOIN menu_items m ON ((m.id = g.item_id)))
  WHERE ((g.id = item_options.group_id) AND (owns_store(m.store_id) OR has_perm('stores'))))))
  with check ((EXISTS ( SELECT 1
   FROM (item_option_groups g
     JOIN menu_items m ON ((m.id = g.item_id)))
  WHERE ((g.id = item_options.group_id) AND (owns_store(m.store_id) OR has_perm('stores'))))));

drop policy if exists "store_req_read" on public.store_requests;
create policy "store_req_read" on public.store_requests for SELECT to public
  using (((user_id = auth.uid()) OR has_perm('stores')));

drop policy if exists "banners_read" on public.banners;
create policy "banners_read" on public.banners for SELECT to public
  using (((is_active AND ((starts_at IS NULL) OR (starts_at <= now())) AND ((ends_at IS NULL) OR (ends_at >= now()))) OR has_perm('content')));

drop policy if exists "banners_admin" on public.banners;
create policy "banners_admin" on public.banners for ALL to public
  using (has_perm('content'))
  with check (has_perm('content'));

drop policy if exists "promo_admin" on public.promo_codes;
create policy "promo_admin" on public.promo_codes for ALL to public
  using (has_perm('content'))
  with check (has_perm('content'));

drop policy if exists "wallet_read" on public.wallet_entries;
create policy "wallet_read" on public.wallet_entries for SELECT to public
  using (((user_id = auth.uid()) OR (has_perm('support') or has_perm('finance'))));

-- staff may read customers (support) / couriers (orders, finance) — never other roles, never write
drop policy if exists profiles_staff_read on profiles;
create policy profiles_staff_read on profiles for select to public
  using ((role = 'customer' and has_perm('support')) or (role = 'driver' and (has_perm('orders') or has_perm('finance'))));

-- stores: staff may create and edit (commission/discount are still blocked by validate_store for non-admins); only admin deletes
drop policy if exists stores_staff_ins on stores;
create policy stores_staff_ins on stores for insert to public with check (has_perm('stores'));
drop policy if exists stores_staff_upd on stores;
create policy stores_staff_upd on stores for update to public using (has_perm('stores')) with check (has_perm('stores'));

commit;
