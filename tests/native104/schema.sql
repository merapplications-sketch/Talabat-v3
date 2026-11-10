-- Candidate104 overlay. Apply after103, in the SAME transaction; isolated development only.
create or replace function security_private.request_payload103(p_store uuid,p_items jsonb,p_tip numeric,p_payment text,p_address text,p_lat float8,p_lng float8,p_promo text,p_fee numeric,p_wallet numeric,p_points integer,p_extra jsonb) returns jsonb language plpgsql immutable set search_path=pg_catalog set extra_float_digits=3 as $$begin
 return jsonb_build_array(p_store,p_items,p_tip,p_payment,p_address,p_lat,p_lng,p_promo,p_fee,p_wallet,p_points,p_extra);end$$;
revoke all on function security_private.request_payload103(uuid,jsonb,numeric,text,text,float8,float8,text,numeric,numeric,integer,jsonb) from public,anon,authenticated;
create table if not exists security_private.order_attempt_closures104(
 customer_id uuid not null references public.profiles(id),client_key text not null check(client_key ~ '^[A-Za-z0-9_-]{8,64}$'),
 closure_id uuid not null default gen_random_uuid(),state_version integer not null default 1 check(state_version=1),
 reason text not null,closed_at timestamptz not null default clock_timestamp(),primary key(customer_id,client_key),unique(closure_id)
);
alter table security_private.order_attempt_closures104 enable row level security;
revoke all on security_private.order_attempt_closures104 from public,anon,authenticated;
do $$begin if exists(select 1 from pg_roles where rolname='service_role') then execute 'revoke all on security_private.order_attempt_closures104 from service_role';end if;end$$;
