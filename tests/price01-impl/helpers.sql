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
 'options',coalesce((select jsonb_agg(jsonb_build_object('id',x.id,'price_delta',trim_scale((o->>'p')::numeric)::text) order by x.ord)
 from jsonb_array_elements_text(opts) with ordinality x(id,ord) join jsonb_array_elements(snap) o on o->>'id'=x.id),'[]'::jsonb))
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
