-- Explicit, owner-only conversion of EXISTING trusted SQL102 bindings, never historical reconstruction.
create or replace function security_private.convert_bindings102_to103() returns integer language plpgsql security definer set search_path=pg_catalog,public as $$
declare r record;k integer;s bytea;f security_private.order_request_fingerprints103;n integer:=0;begin
 if to_regclass('security_private.order_request_bindings') is null then return 0;end if;
 select key_id,secret into k,s from security_private.order_request_keys103 where active;
 if not found then raise exception 'fingerprint_key_unavailable';end if;
 for r in execute 'select * from security_private.order_request_bindings order by customer_id,client_key for update' loop
  if not exists(select 1 from public.orders where id=r.order_id and customer_id=r.customer_id and client_key=r.client_key) or jsonb_typeof(r.request)<>'array' or jsonb_array_length(r.request)<>12 then raise exception 'binding_conversion_invalid';end if;
  select * into f from security_private.order_request_fingerprints103 where customer_id=r.customer_id and client_key=r.client_key;
  if found then
   if f.order_id<>r.order_id or f.contract_version<>1 or f.mac is distinct from security_private.mac103(r.request,r.customer_id,r.client_key,(select secret from security_private.order_request_keys103 where key_id=f.key_id)) then raise exception 'binding_conversion_conflict';end if;
  else
   insert into security_private.order_request_fingerprints103 values(r.customer_id,r.client_key,r.order_id,1,k,security_private.mac103(r.request,r.customer_id,r.client_key,s));
  end if;
  update public.orders set request_contract_version=1 where id=r.order_id;
  execute 'delete from security_private.order_request_bindings where customer_id=$1 and client_key=$2' using r.customer_id,r.client_key;
  n:=n+1;
 end loop;return n;end$$;
revoke all on function security_private.convert_bindings102_to103() from public,anon,authenticated;
