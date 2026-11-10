-- SQL103 REVIEW CANDIDATE ONLY. Run transactionally in an authorized isolated target.
-- pgcrypto must be installed in extensions by an authorized operator beforehand.
do $$begin
 if not exists(select 1 from pg_extension e join pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto' and n.nspname='extensions') then raise exception 'pgcrypto_schema_required'; end if;
end$$;
create table if not exists security_private.order_request_keys103(
 key_id integer primary key check(key_id>0),secret bytea not null check(octet_length(secret)>=32),active boolean not null default false
);
create unique index if not exists request103_one_active_key on security_private.order_request_keys103(active) where active;
create table if not exists security_private.order_request_fingerprints103(
 customer_id uuid not null references public.profiles(id),client_key text not null,
 order_id bigint not null unique references public.orders(id),contract_version integer not null check(contract_version=1),
 key_id integer not null references security_private.order_request_keys103(key_id),mac bytea not null check(octet_length(mac)=32),
 primary key(customer_id,client_key)
);
alter table public.orders add column if not exists request_contract_version integer;
-- Null means legacy writer. Marker is atomic with the new order: missing fingerprint never downgrades to legacy.
alter table security_private.order_request_keys103 enable row level security;
alter table security_private.order_request_fingerprints103 enable row level security;
revoke all on security_private.order_request_keys103,security_private.order_request_fingerprints103 from public,anon,authenticated;
-- Reapplication verifies the exact candidate relation shape instead of accepting unknown drift.
do $$declare cols text[];begin
 select array_agg(attname::text||':'||format_type(atttypid,atttypmod)||':'||attnotnull::text order by attnum) into cols from pg_attribute where attrelid='security_private.order_request_keys103'::regclass and attnum>0 and not attisdropped;
 if cols is distinct from array['key_id:integer:true','secret:bytea:true','active:boolean:true'] then raise exception 'request103_schema_drift'; end if;
 select array_agg(attname::text||':'||format_type(atttypid,atttypmod)||':'||attnotnull::text order by attnum) into cols from pg_attribute where attrelid='security_private.order_request_fingerprints103'::regclass and attnum>0 and not attisdropped;
 if cols is distinct from array['customer_id:uuid:true','client_key:text:true','order_id:bigint:true','contract_version:integer:true','key_id:integer:true','mac:bytea:true'] then raise exception 'request103_schema_drift'; end if;
 if (select atttypid from pg_attribute where attrelid='public.orders'::regclass and attname='request_contract_version') <> 'integer'::regtype then raise exception 'request103_schema_drift'; end if;
end$$;
-- Prevent client modification even if target has broad table grants. Definer-owner writes only.
create or replace function security_private.guard_request_marker103() returns trigger language plpgsql set search_path=pg_catalog as $$begin
 if (tg_op='INSERT' and new.request_contract_version is not null) or (tg_op='UPDATE' and new.request_contract_version is distinct from old.request_contract_version) then
  if current_user <> pg_get_userbyid((select relowner from pg_class where oid='security_private.order_request_fingerprints103'::regclass)) then raise exception 'not_allowed'; end if;
  if new.request_contract_version is distinct from 1 then raise exception 'request103_marker_invalid'; end if;
 end if;return new;end$$;
drop trigger if exists request_marker103 on public.orders;
create trigger request_marker103 before insert or update on public.orders for each row execute function security_private.guard_request_marker103();

-- Canonical JSON, not raw jsonb::text (numeric scale must not change fingerprints).
create or replace function security_private.canonical103(v jsonb) returns text language plpgsql immutable strict set search_path=pg_catalog as $$declare out_text text;begin
 case jsonb_typeof(v)
 when 'number' then return trim_scale((v#>>'{}')::numeric)::text;
 when 'array' then select '['||coalesce(string_agg(security_private.canonical103(value),',' order by ord),'')||']' into out_text from jsonb_array_elements(v) with ordinality a(value,ord);return out_text;
 when 'object' then select '{'||coalesce(string_agg(to_jsonb(key)::text||':'||security_private.canonical103(value),',' order by key collate "C"),'')||'}' into out_text from jsonb_each(v);return out_text;
 else return v::text;
 end case;end$$;
create or replace function security_private.mac103(payload jsonb,uid uuid,k text,secret bytea) returns bytea language sql immutable strict set search_path=pg_catalog as $$
 select extensions.hmac(convert_to(security_private.canonical103(jsonb_build_array('TALABOT/order-create',1,uid,k,
 jsonb_set(payload,'{11}',case when payload->11 is null or payload->11='null'::jsonb then '{}'::jsonb else payload->11 end))), 'UTF8'),secret,'sha256')
$$;
-- Pure read path; NULL internally means no visible committed order, never proof of rollback.
create or replace function security_private.resolve103(k text,payload jsonb,verify_input boolean) returns jsonb
language plpgsql security definer set search_path=pg_catalog,public as $$
declare o public.orders;f security_private.order_request_fingerprints103;s bytea;old_binding boolean;begin
 if auth.uid() is null then raise exception 'auth'; end if;
 if public.account_enabled() is not true then raise exception 'account_blocked'; end if;
 if k is null or k !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
 select * into o from public.orders where customer_id=auth.uid() and client_key=k;
 if not found then return null;end if;
 if o.group_id is not null and not exists(select 1 from public.group_orders g where g.id=o.group_id and g.host_id=auth.uid() and g.store_id=o.store_id and g.order_id=o.id) then raise exception 'not_allowed';end if;
 select * into f from security_private.order_request_fingerprints103 where customer_id=auth.uid() and client_key=k;
 if not found then
  old_binding:=false;
  if to_regclass('security_private.order_request_bindings') is not null then execute 'select exists(select 1 from security_private.order_request_bindings where customer_id=$1 and client_key=$2)' into old_binding using auth.uid(),k;end if;
  if o.request_contract_version is not null or old_binding then return jsonb_build_object('status','unresolved','reason','binding_unavailable','key',k);end if;
  return jsonb_build_object('status','historical_recovered','id',o.id::text,'key',k,'input_match',null,'contract_version',null);
 end if;
 if f.order_id<>o.id or f.contract_version<>1 or o.request_contract_version is distinct from 1 then return jsonb_build_object('status','unresolved','reason','binding_inconsistent','key',k);end if;
 if verify_input then
  select secret into s from security_private.order_request_keys103 where key_id=f.key_id;
  if s is null then return jsonb_build_object('status','unresolved','reason','verification_key_unavailable','key',k);end if;
  if f.mac is distinct from security_private.mac103(payload,auth.uid(),k,s) then return jsonb_build_object('status','conflict','reason','idempotency_mismatch','key',k);end if;
 end if;
 return jsonb_build_object('status','replayed','id',o.id::text,'key',k,'input_match',case when verify_input then true else null end,'contract_version',1);
end$$;
create or replace function public.order_request_status103(p_key text) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$begin
 return coalesce(security_private.resolve103(p_key,null,false),jsonb_build_object('status','unresolved','reason','not_visible','key',p_key));end$$;
-- Guard core uniqueness/FK invariants on reapplication; owner must inspect any other catalog drift.
do $$begin
 if not exists(select 1 from pg_constraint where conrelid='security_private.order_request_keys103'::regclass and contype='p' and conkey=array[1]::smallint[])
 or not exists(select 1 from pg_constraint where conrelid='security_private.order_request_fingerprints103'::regclass and contype='p' and conkey=array[1,2]::smallint[])
 or not exists(select 1 from pg_constraint where conrelid='security_private.order_request_fingerprints103'::regclass and contype='u' and conkey=array[3]::smallint[])
 or not exists(select 1 from pg_constraint where conrelid='security_private.order_request_fingerprints103'::regclass and contype='f' and conkey=array[3]::smallint[] and confrelid='public.orders'::regclass)
 or not exists(select 1 from pg_constraint where conrelid='security_private.order_request_fingerprints103'::regclass and contype='f' and conkey=array[5]::smallint[] and confrelid='security_private.order_request_keys103'::regclass)
 then raise exception 'request103_schema_drift';end if;
 if exists(select 1 from pg_roles where rolname='service_role') then
  execute 'revoke all on security_private.order_request_keys103,security_private.order_request_fingerprints103 from service_role';
 end if;
end$$;
create or replace function security_private.guard_request_key103() returns trigger language plpgsql set search_path=pg_catalog as $$begin
 if new.key_id is distinct from old.key_id or new.secret is distinct from old.secret then raise exception 'request_key_immutable';end if;return new;end$$;
drop trigger if exists request_key103 on security_private.order_request_keys103;
create trigger request_key103 before update on security_private.order_request_keys103 for each row execute function security_private.guard_request_key103();
revoke all on function security_private.guard_request_key103() from public,anon,authenticated;
