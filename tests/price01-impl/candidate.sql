-- Generated PRICE01 isolated candidate. Apply atomically AFTER accepted NULL01.
-- Isolated PRICE01 only. No table/schema/data migration or production key provisioning.
create or replace function security_private.price01_amount(v jsonb) returns numeric
language plpgsql immutable set search_path=pg_catalog as $$declare t text;begin
 if jsonb_typeof(v) is distinct from 'string' then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 t:=v#>>'{}';
 -- Bounded evidence representation, not a monetary rounding rule or price cap.
 if length(t)>128 or t !~ '^-?(0|[1-9][0-9]*)(\.[0-9]+)?$' then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 return t::numeric;
end$$;
create or replace function security_private.price01_normalize(v jsonb) returns jsonb
language plpgsql immutable set search_path=pg_catalog as $$
declare l jsonb;o jsonb;k text;ls jsonb:='[]';os jsonb;tot jsonb;nl jsonb;begin
 if v is null or v='null'::jsonb then raise exception using errcode='P0101',message='price_confirmation_required';end if;
 if octet_length(v::text)>524288 or jsonb_typeof(v) is distinct from 'object' or v->'version' is distinct from '1'::jsonb
 or (select array_agg(key order by key) from jsonb_object_keys(v) key) is distinct from array['lines','totals','version']::text[]
 or jsonb_typeof(v->'lines') is distinct from 'array' or jsonb_typeof(v->'totals') is distinct from 'object'
 then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 if jsonb_array_length(v->'lines') not between 1 and 60 then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 for l in select value from jsonb_array_elements(v->'lines') loop
  if jsonb_typeof(l) is distinct from 'object' or (select array_agg(key order by key) from jsonb_object_keys(l) key) is distinct from array['base_price','happy_hour_discount','item_id','net_items','options','qty','restaurant_discount','unit_price']::text[]
  or jsonb_typeof(l->'item_id') is distinct from 'string' or (l->>'item_id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  or jsonb_typeof(l->'qty') is distinct from 'number' or (l->>'qty')::numeric not between 1 and 50 or (l->>'qty')::numeric<>trunc((l->>'qty')::numeric)
  or jsonb_typeof(l->'options') is distinct from 'array'
  then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
  if jsonb_array_length(l->'options')>40 then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
  os:='[]';
  for o in select value from jsonb_array_elements(l->'options') loop
   if jsonb_typeof(o) is distinct from 'object' or (select array_agg(key order by key) from jsonb_object_keys(o) key) is distinct from array['id','price_delta']::text[]
   or jsonb_typeof(o->'id') is distinct from 'string' or (o->>'id') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
   os:=os||jsonb_build_array(jsonb_build_object('id',o->'id','price_delta',security_private.price01_amount(o->'price_delta')));
  end loop;
  nl:=jsonb_build_object('item_id',l->'item_id','qty',l->'qty','options',os);
  foreach k in array array['base_price','unit_price','restaurant_discount','happy_hour_discount','net_items'] loop nl:=nl||jsonb_build_object(k,security_private.price01_amount(l->k));end loop;
  ls:=ls||jsonb_build_array(nl);
 end loop;
 tot:=v->'totals';
 if (select array_agg(key order by key) from jsonb_object_keys(tot) key) is distinct from array['cash_due','delivery_fee','happy_hour_discount','points_value','promo_discount','restaurant_discount','subtotal','tip','total','wallet_used']::text[] then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 for k in select jsonb_object_keys(tot) loop tot:=jsonb_set(tot,array[k],to_jsonb(security_private.price01_amount(tot->k)));end loop;
 return jsonb_build_object('version',1,'lines',ls,'totals',tot);
end$$;

-- Only persisted line snapshots and the exact discounts used in the existing aggregate.
create or replace function security_private.price01_line(item uuid,q integer,u numeric,snap jsonb,opts jsonb,rd numeric,ad numeric) returns jsonb
language sql immutable set search_path=pg_catalog as $$
select jsonb_build_object('item_id',item,'qty',q,'base_price',trim_scale(u-coalesce((select sum((o->>'p')::numeric) from jsonb_array_elements(snap) o),0))::text,
 'unit_price',trim_scale(u)::text,'restaurant_discount',trim_scale(rd)::text,'happy_hour_discount',trim_scale(ad-rd)::text,'net_items',trim_scale(u*q-ad)::text,
 -- Visit EVERY saved option once. opts supplies ordering only, never filtering.
 -- Unknown IDs and repeated saved entries must survive into the strict comparison.
 'options',coalesce((select jsonb_agg(jsonb_build_object('id',s.o->>'id','price_delta',trim_scale((s.o->>'p')::numeric)::text)
 order by (select min(x.ord) from jsonb_array_elements_text(opts) with ordinality x(id,ord) where x.id=s.o->>'id') nulls last,s.n)
 from jsonb_array_elements(snap) with ordinality s(o,n)),'[]'::jsonb))
$$;
create or replace function security_private.price01_saved(oid bigint,ids uuid[],lines jsonb) returns jsonb
language plpgsql stable set search_path=pg_catalog,public as $$declare o public.orders;ls jsonb;begin
 select * into o from public.orders where id=oid;
 if not found or (select count(*) from public.order_items where order_id=oid)<>cardinality(ids) then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 select jsonb_agg(security_private.price01_line(i.item_id,i.qty,i.price,i.options,
  coalesce((select jsonb_agg(x->'id') from jsonb_array_elements(lines->(a.n::int-1)->'options') x),'[]'::jsonb),
  (lines->(a.n::int-1)->>'restaurant_discount')::numeric,
  (lines->(a.n::int-1)->>'restaurant_discount')::numeric+(lines->(a.n::int-1)->>'happy_hour_discount')::numeric) order by a.n)
 into ls from unnest(ids) with ordinality a(id,n) join public.order_items i on i.id=a.id and i.order_id=oid;
 if jsonb_array_length(ls) is distinct from cardinality(ids) then raise exception using errcode='P0103',message='price_evidence_invalid';end if;
 return jsonb_build_object('version',1,'lines',ls,'totals',jsonb_build_object(
 'subtotal',trim_scale(o.subtotal)::text,'restaurant_discount',trim_scale(o.discount-o.hh_discount)::text,'happy_hour_discount',trim_scale(o.hh_discount)::text,
 'promo_discount',trim_scale(o.promo_discount)::text,'points_value',trim_scale(coalesce(o.points_value,0))::text,'delivery_fee',trim_scale(o.delivery_fee)::text,
 'tip',trim_scale(o.tip)::text,'wallet_used',trim_scale(coalesce(o.wallet_used,0))::text,'cash_due',trim_scale(o.total-coalesce(o.wallet_used,0))::text,'total',trim_scale(o.total)::text));
end$$;
create or replace function security_private.price01_assert(expected jsonb,actual jsonb) returns void
language plpgsql immutable set search_path=pg_catalog as $$begin
 if expected is distinct from security_private.price01_normalize(actual) then
  raise exception using errcode='P0102',message='price_changed',detail=actual::text;
 end if;
end$$;
revoke all on function security_private.price01_amount(jsonb),security_private.price01_normalize(jsonb),security_private.price01_line(uuid,integer,numeric,jsonb,jsonb,numeric,numeric),security_private.price01_saved(bigint,uuid[],jsonb),security_private.price01_assert(jsonb,jsonb) from public,anon,authenticated;

-- TIP-02-NULL-01: isolated overlay AFTER TIP-02. No historical data migration.
CREATE OR REPLACE FUNCTION security_private.create_order103(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public'
 SET extra_float_digits TO '3'
AS $function$
declare v_price_expected jsonb; v_price_lines jsonb; v_price_ids uuid[]:=array[]::uuid[]; v_price_id uuid; v_build_prev text; s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
        v_step numeric; v_mo numeric; v_subst text; v_door boolean; v_gn text; v_gp text;
        v_at timestamptz; v_waived numeric := 0; v_gid uuid; g group_orders; v_request jsonb; v_result jsonb; v_key_id integer; v_secret bytea; v_mac bytea;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if public.account_enabled() is not true then raise exception 'account_blocked'; end if;
  if p_key is null or p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
  --106: a key advisory lock does not refresh a transaction snapshot.
  -- Creation/replay via creation endpoints is supported only with statement snapshots.
  if current_setting('transaction_isolation') not in ('read committed','read uncommitted') then
    return jsonb_build_object('status','unresolved','reason','unsupported_transaction_isolation','key',p_key);
  end if;
  v_request := security_private.request_payload103(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_fee,p_wallet,p_points,p_extra);
  -- Recover committed history before NEW-request parsing/admission; authorize original saved resource.
  v_result := security_private.resolve103(p_key,v_request,true);
  if v_result is not null then return v_result;end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if auth.uid() is not null and public.account_enabled() is not true then raise exception 'account_blocked'; end if;
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;
  -- order options (v50): leave at the door, what to do if a dish is missing, a gift for someone else
  v_door := coalesce((p_extra->>'door')::boolean, false);
  v_subst := coalesce(p_extra->>'subst', 'call');
  if v_subst not in ('call', 'replace', 'remove') then raise exception 'bad_value'; end if;
  -- scheduled delivery time (v51): from 45 minutes (with a little slack for the screen) to 3 days ahead
  if nullif(p_extra->>'at', '') is not null then
    begin v_at := (p_extra->>'at')::timestamptz; exception when others then raise exception 'bad_time'; end;
  end if;
  -- office / group order (v51): only its host can place it, once
  if nullif(p_extra->>'group', '') is not null then
    begin v_gid := (p_extra->>'group')::uuid; exception when others then raise exception 'bad_group'; end;
    select * into g from group_orders where id = v_gid for update;
    if not found or g.host_id is distinct from auth.uid() or g.store_id is distinct from p_store then raise exception 'bad_group'; end if;
  end if;
  if p_extra ? 'gift' and jsonb_typeof(p_extra->'gift') = 'object' then
    v_gn := btrim(coalesce(p_extra->'gift'->>'name', '')); v_gp := norm_phone(p_extra->'gift'->>'phone');
    if char_length(v_gn) not between 2 and 60 or v_gp is null then raise exception 'bad_gift'; end if;
  end if;   -- a negative amount would mean ADDING money: refuse it
  if auth.uid() is null then raise exception 'auth'; end if;
  -- Same lock order as102: group -> caller/key -> profile. Lookup again after waiting.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(auth.uid()::text || ':' || p_key, 0));
  v_result := security_private.resolve103(p_key,v_request,true);
  if v_result is not null then return v_result;end if;
  if exists(select 1 from security_private.order_attempt_closures104 where customer_id=auth.uid() and client_key=p_key) then raise exception 'attempt_closed';end if;
  -- TIP-02: only NEW creation is range-checked; prior-key recovery above is unchanged.
  -- NULL-01 owner decision: explicit NULL is rejected only for NEW creation.
  if p_tip is null or p_tip < 0 or p_tip > 100 or p_tip <> trunc(p_tip) then
    raise exception 'bad_value';
  end if;
  v_price_expected:=security_private.price01_normalize(p_extra->'price01');
  select key_id,secret into v_key_id,v_secret from security_private.order_request_keys103 where active;
  if not found then raise exception 'fingerprint_key_unavailable';end if;
  v_mac := security_private.mac103(v_request,auth.uid(),p_key,v_secret);
  -- Only NEW operations must satisfy mutable admission state/time.
  if v_at is not null and (v_at < now() + interval '40 minutes' or v_at > now() + interval '3 days') then raise exception 'bad_time'; end if;
  if v_gid is not null and (g.status not in ('open','closed') or g.status is null or g.expires_at is null or g.expires_at <= now()) then raise exception 'bad_group'; end if;
  -- No external processor is configured. Only cash may be asserted by a caller;
  -- existing wallet debit logic below alone may mark a fully funded order wallet.
  -- Preserve existing-key recovery above; never rewrite historical payments.
  if p_payment is distinct from 'cash' then raise exception 'payment_not_configured'; end if;
  -- S98: serialize admission for all keys of this account, not just identical keys.
  select * into pr from profiles where id = auth.uid() for update;
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
  v_hh := happy_hour_pct(p_store);                                -- admin-scheduled happy hour (paid by the platform)
  if p_items is null or jsonb_typeof(p_items) is distinct from 'array' then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) = 0 then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) > 60 then raise exception 'bad_value'; end if;

  -- the customer phone is required (stored privately, see order_customer_phone) and the fee is calculated here, never by the app
  if pr.banned_at is not null then raise exception 'account_blocked'; end if;   -- a suspended account cannot order
  v_cphone := norm_phone(pr.phone);
  if v_cphone is null then raise exception 'phone_required'; end if;
  v_dq := delivery_calc(p_store, p_lat, p_lng, auth.uid());
  v_fee := (v_dq->>'fee')::numeric;
  v_pay := case s.fee_type when 'free' then s.fee_base else (v_dq->>'fee_full')::numeric end;   -- courier is always paid; the platform covers free delivery
  v_tip := coalesce(p_tip,0);

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key, leave_at_door, substitution, is_gift, scheduled_for, group_id, request_contract_version)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key, v_door, v_subst, v_gn is not null, v_at, v_gid, 1)
    returning id into v_id;
  exception when unique_violation then
    -- Candidate callers serialize before lookup. A conflicting legacy/other writer
    -- must not bypass request binding or turn an unrelated unique failure into success.
    raise;
  end;
  v_build_prev:=current_setting('talabot.order_building',true);
  perform set_config('talabot.order_building',v_id::text,true);
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);
  if v_gn is not null then insert into order_recipient(order_id, name, phone) values (v_id, v_gn, v_gp); end if;

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
    values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap') returning id into v_price_id;
    v_price_ids:=array_append(v_price_ids,v_price_id);
  end loop;

  -- each line gets the better of the store discount and its own item discount (they do not stack; paid by the restaurant).
  -- A happy hour can only make it better. Owner decision (v48): the RESTAURANT pays it too, like its own offers: it is part of
  -- orders.discount (so revenue and commission are on what the customer pays); orders.hh_discount says how much of it came from the happy hour.
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) = 0), 0)
, jsonb_agg(security_private.price01_line(oi.item_id,oi.qty,oi.price,oi.options,
        p_items->(array_position(v_price_ids,oi.id)-1)->'options',round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2),round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)) order by array_position(v_price_ids,oi.id))
    into v_sub, v_disc, v_all, v_base, v_price_lines
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;
  v_hdisc := v_all - v_disc;
  -- free delivery above the restaurant's own threshold (v51): the restaurant pays the waived fee (orders.fee_waived)
  if coalesce(s.free_delivery_min, 0) > 0 and v_sub - v_disc - v_hdisc >= s.free_delivery_min and v_fee > 0 then
    v_waived := v_fee; v_fee := 0;
  end if;
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc - v_hdisc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc + v_hdisc, delivery_fee = v_fee, fee_waived = v_waived, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo, hh_discount = v_hdisc, hh_pct = v_hh,
    total = greatest(5, v_sub - v_disc - v_hdisc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc - v_hdisc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- POINTS: the customer may pay part of the items with loyalty points (all he can use, decided here, never by the app)
  if coalesce(p_points, 0) > 0 then
    v_rate := loyalty_setting('loyalty_points_per_tjs'); v_min := loyalty_setting('loyalty_min_redeem');
    v_step := greatest(1, loyalty_setting('loyalty_voucher_points'));
    v_mo := coalesce(s.points_min_order, loyalty_setting('loyalty_min_order'));
    perform 1 from profiles where id = auth.uid() for update;          -- two orders at the same moment cannot spend the same points
    v_lb := loyalty_balance(auth.uid());
    if v_lb < v_min then raise exception 'points_min'; end if;
    v_cap := v_sub - v_disc - v_hdisc - v_promo;                       -- points never pay for delivery or the tip
    if v_cap < v_mo then raise exception 'points_min_order'; end if;  -- the order (dishes) must reach the minimum to use points
    v_pts := (floor(least(v_lb, floor(greatest(v_cap, 0) * v_rate)) / v_step) * v_step)::int;   -- whole vouchers only (1000, 2000 ...)
    if v_pts <= 0 or v_pts <> p_points then raise exception 'points_changed'; end if;   -- the customer saw another amount: ask again
    v_pval := round(v_pts / v_rate, 2);
    perform loyalty_spend(auth.uid(), v_pts, v_id);
    update orders set points_used = v_pts, points_value = v_pval,
      total = greatest(5, v_sub - v_disc - v_hdisc - v_promo - v_pval + v_fee + v_tip) where id = v_id;
  end if;

  -- WALLET: the customer may pay all or part of the order from his refund balance (the server decides the amount, never the app)
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  perform security_private.price01_assert(v_price_expected,security_private.price01_saved(v_id,v_price_ids,v_price_lines));
  if v_gid is not null then update group_orders set status = 'placed', order_id = v_id, closed_at = coalesce(closed_at, now()) where id = v_gid; end if;
  perform finance_private.snapshot_cash(v_id);
  perform set_config('talabot.order_building',coalesce(v_build_prev,''),true);
  perform fulfillment_private.register_order(v_id);
  insert into security_private.order_request_fingerprints103(customer_id,client_key,order_id,contract_version,key_id,mac)
  values(auth.uid(),p_key,v_id,1,v_key_id,v_mac);
  -- Re-read after all candidate helpers/triggers/binding insert; no later pricing write is allowed.
  perform security_private.price01_assert(v_price_expected,security_private.price01_saved(v_id,v_price_ids,v_price_lines));
  return jsonb_build_object('status','created','id',v_id::text,'key',p_key,'input_match',true,'contract_version',1);
end $function$;


create or replace function public.place_order103(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare result jsonb;price_detail text;begin
 begin
  return security_private.create_order103(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_key,p_fee,p_wallet,p_points,p_extra);
 exception
  when sqlstate 'P0102' then
   get stacked diagnostics price_detail=PG_EXCEPTION_DETAIL;
   return jsonb_build_object('status','rejected','reason','price_changed','key',p_key,'price_review',price_detail::jsonb);
  when sqlstate 'P0101' or sqlstate 'P0103' then
   return jsonb_build_object('status','rejected','reason',SQLERRM,'key',p_key);
  when deadlock_detected or lock_not_available or query_canceled then
   return jsonb_build_object('status','unresolved','reason',SQLSTATE,'key',p_key);
  when unique_violation then
   -- Another legacy writer may have committed; no blind mutation retry.
   result:=security_private.resolve103(p_key,security_private.request_payload103(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_fee,p_wallet,p_points,p_extra),true);
   return coalesce(result,jsonb_build_object('status','unresolved','reason','unique_conflict','key',p_key));
  when raise_exception then
   if SQLERRM='fingerprint_key_unavailable' then return jsonb_build_object('status','unresolved','reason','fingerprint_key_unavailable','key',p_key);end if;
   -- No request data echoed. Subtransaction rollback is complete before this rejection.
   return jsonb_build_object('status','rejected','reason',case when SQLERRM in ('auth','account_blocked','not_allowed','bad_value','bad_group','bad_time','empty','unavailable','bad_options','too_many_orders','payment_not_configured','address_required','store_unavailable','closed','phone_required','fee_changed','wallet_changed','bad_gift','promo_invalid','promo_offer','points_min','points_changed','points_min_order','cash_allocation_required','cash_allocation_exceeds_fee','pilot_scheduled_unavailable') then SQLERRM else 'creation_rejected' end,'key',p_key);
  when integrity_constraint_violation or data_exception then
   return jsonb_build_object('status','rejected','reason','invalid_request','key',p_key);
 end;
end$$;

create or replace function public.place_order104(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$declare r jsonb;s jsonb;begin
 r:=public.place_order103(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_key,p_fee,p_wallet,p_points,p_extra);
 if r->>'status'<>'rejected' then return r;end if;
 -- An authorization/invalid-key failure cannot mint an actionable closure receipt.
 if auth.uid() is null or public.account_enabled() is not true or p_key is null or p_key !~ '^[A-Za-z0-9_-]{8,64}$' then return r;end if;
 --103's failed subtransaction released its group/profile locks. Only the key lock is taken here.
 -- All authorized candidate writers check this same fence under the same lock before effects.
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text||':'||p_key,0));
 s:=security_private.resolve103(p_key,security_private.request_payload103(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_fee,p_wallet,p_points,p_extra),true);
 if s is not null then return s;end if;
 s:=security_private.closure_result104(p_key);
 if s is not null then return s;end if;
 insert into security_private.order_attempt_closures104(customer_id,client_key,reason) values(auth.uid(),p_key,coalesce(r->>'reason','creation_rejected')) on conflict(customer_id,client_key) do nothing;
 s:=security_private.closure_result104(p_key);
 if r->>'reason'='price_changed' and r ? 'price_review' then s:=s||jsonb_build_object('price_review',r->'price_review');end if;
 return s;
exception when sqlstate 'P1050' then return jsonb_build_object('status','unresolved','key',p_key,'reason','closure_resource_unavailable');
 when deadlock_detected or lock_not_available or query_canceled then return jsonb_build_object('status','unresolved','key',p_key,'reason',SQLSTATE);
end$$;
