create or replace function security_private.closure_result104(k text) returns jsonb language sql stable security definer set search_path=pg_catalog as $$
 select jsonb_build_object('status','rejected','key',client_key,'reason',reason,'closed',true,'no_effects',true,'closure_id',closure_id::text,'state_version',state_version)
 from security_private.order_attempt_closures104 where customer_id=auth.uid() and client_key=k
$$;
revoke all on function security_private.closure_result104(text) from public,anon,authenticated;
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
 insert into security_private.order_attempt_closures104(customer_id,client_key,reason) values(auth.uid(),p_key,coalesce(r->>'reason','creation_rejected')) on conflict(customer_id,client_key) do nothing;
 return security_private.closure_result104(p_key);
exception when deadlock_detected or lock_not_available or query_canceled then return jsonb_build_object('status','unresolved','key',p_key,'reason',SQLSTATE);
end$$;
create or replace function public.order_request_status104(p_key text) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$declare r jsonb;begin
 r:=public.order_request_status103(p_key);
 if r->>'status'='unresolved' and r->>'reason'='not_visible' then return coalesce(security_private.closure_result104(p_key),r);end if;return r;
end$$;
revoke all on function public.place_order104(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb),public.order_request_status104(text) from public,anon;
grant execute on function public.place_order104(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb),public.order_request_status104(text) to authenticated;
