-- Isolated candidate. NO production quota defaults or live policy values.
create table if not exists security_private.closure_policy105(
 singleton boolean primary key check(singleton),
 max_rows bigint not null check(max_rows>0),
 max_account_rows bigint not null check(max_account_rows>0 and max_account_rows<=max_rows),
 max_reason_bytes integer not null check(max_reason_bytes>0),
 epoch bigint not null default 0
);
alter table security_private.closure_policy105 enable row level security;
revoke all on security_private.closure_policy105 from public,anon,authenticated;
do $$begin if exists(select 1 from pg_roles where rolname='service_role') then execute 'revoke all on security_private.closure_policy105 from service_role';end if;end$$;
create or replace function security_private.guard_closure105() returns trigger language plpgsql security definer set search_path=pg_catalog as $$
declare p security_private.closure_policy105;begin
 if TG_OP<>'INSERT' then raise exception using errcode='P1051',message='closure_immutable';end if;
 -- Locks only closure writers AFTER the failed creation subtransaction released group/profile locks.
 -- Existing closure replay is read-only and bypasses admission; it can never reopen a key.
 update security_private.closure_policy105 set epoch=epoch+1 where singleton returning * into p;
 if not found then raise exception using errcode='P1050',message='closure_resource_unavailable';end if;
 if octet_length(NEW.reason)>p.max_reason_bytes
 or (select count(*) from security_private.order_attempt_closures104)>=p.max_rows
 or (select count(*) from security_private.order_attempt_closures104 where customer_id=NEW.customer_id)>=p.max_account_rows
 then raise exception using errcode='P1050',message='closure_resource_unavailable';end if;
 return NEW;
end$$;
revoke all on function security_private.guard_closure105() from public,anon,authenticated;
drop trigger if exists closure_budget105 on security_private.order_attempt_closures104;
create trigger closure_budget105 before insert or update or delete on security_private.order_attempt_closures104 for each row execute function security_private.guard_closure105();
drop trigger if exists closure_no_truncate105 on security_private.order_attempt_closures104;
create trigger closure_no_truncate105 before truncate on security_private.order_attempt_closures104 for each statement execute function security_private.guard_closure105();

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
 s:=security_private.closure_result104(p_key);
 if s is not null then return s;end if;
 insert into security_private.order_attempt_closures104(customer_id,client_key,reason) values(auth.uid(),p_key,coalesce(r->>'reason','creation_rejected')) on conflict(customer_id,client_key) do nothing;
 return security_private.closure_result104(p_key);
exception when sqlstate 'P1050' then return jsonb_build_object('status','unresolved','key',p_key,'reason','closure_resource_unavailable');
 when deadlock_detected or lock_not_available or query_canceled then return jsonb_build_object('status','unresolved','key',p_key,'reason',SQLSTATE);
end$$;
create or replace function public.order_request_status104(p_key text) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$declare r jsonb;begin
 r:=public.order_request_status103(p_key);
 if r->>'status'='unresolved' and r->>'reason'='not_visible' then return coalesce(security_private.closure_result104(p_key),r);end if;return r;
end$$;
revoke all on function public.place_order104(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb),public.order_request_status104(text) from public,anon;
grant execute on function public.place_order104(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb),public.order_request_status104(text) to authenticated;
