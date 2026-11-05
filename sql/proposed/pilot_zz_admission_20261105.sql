-- ISOLATED REVIEW CANDIDATE. Not applied live. No approved participant or pilot defaults.
-- Applying this guard pauses NEW orders until an explicit audited configuration exists.
begin;
create schema if not exists pilot_private;
revoke all on schema pilot_private from public,anon,authenticated;
create table if not exists pilot_private.config(id boolean primary key default true check(id),paused boolean not null default true,value jsonb,actor uuid,at timestamptz not null default now());
insert into pilot_private.config(id)values(true)on conflict do nothing;
create table if not exists pilot_private.config_events(id bigint generated always as identity primary key,actor uuid not null,at timestamptz not null default now(),before_value jsonb,after_value jsonb);
create table if not exists pilot_private.admissions(order_id bigint primary key references orders(id),customer_id uuid not null,store_id uuid not null,at timestamptz not null default now());
alter table pilot_private.config enable row level security;alter table pilot_private.config_events enable row level security;alter table pilot_private.admissions enable row level security;
revoke all on all tables in schema pilot_private from public,anon,authenticated;
create or replace function public.configure_pilot_admission(p_config jsonb default null,p_paused boolean default true)returns jsonb
language plpgsql security definer set search_path=public as $$
declare old_config jsonb;cfg jsonb;tz text;v jsonb;entry text;d integer;begin
 if not is_admin()then raise exception'not_allowed';end if;
 select to_jsonb(c)into old_config from pilot_private.config c where id for update;
 select coalesce(p_config,value)into cfg from pilot_private.config where id;
 if not p_paused then
  if cfg is null or not coalesce((cfg->>'owner_approved')::boolean,false)then raise exception'pilot_config_incomplete';end if;
  tz:=cfg->>'timezone';if not exists(select 1 from pg_timezone_names where name=tz)then raise exception'pilot_config_incomplete';end if;
  if not(cfg?'valid_from'and cfg?'valid_until'and cfg?'open_minute'and cfg?'close_minute'and cfg?'max_active'and cfg?'daily_orders'and cfg?'min_lat'and cfg?'max_lat'and cfg?'min_lng'and cfg?'max_lng')then raise exception'pilot_config_incomplete';end if;
  foreach tz in array array['valid_from','valid_until','open_minute','close_minute','max_active','daily_orders','min_lat','max_lat','min_lng','max_lng']loop
   if cfg->tz='null'::jsonb then raise exception'pilot_config_incomplete';end if;end loop;
  if (cfg->>'valid_from')::timestamptz>=(cfg->>'valid_until')::timestamptz or (cfg->>'open_minute')::int<0 or(cfg->>'close_minute')::int>1440 or(cfg->>'open_minute')::int>=(cfg->>'close_minute')::int
   or(cfg->>'max_active')::int not between 1 and 20 or(cfg->>'daily_orders')::int not between 1 and 500
   or(cfg->>'min_lat')::numeric not between -90 and 90 or(cfg->>'max_lat')::numeric not between -90 and 90 or(cfg->>'min_lat')::numeric>=(cfg->>'max_lat')::numeric
   or(cfg->>'min_lng')::numeric not between -180 and 180 or(cfg->>'max_lng')::numeric not between -180 and 180 or(cfg->>'min_lng')::numeric>=(cfg->>'max_lng')::numeric then raise exception'pilot_config_incomplete';end if;
  foreach tz in array array['customers','drivers','stores','weekdays']loop
   if jsonb_typeof(cfg->tz)is distinct from'array'or jsonb_array_length(cfg->tz)=0 then raise exception'pilot_config_incomplete';end if;
  end loop;
  for v in select value from jsonb_array_elements(cfg->'weekdays')loop d:=v::text::int;if d not between 1 and 7 then raise exception'pilot_config_incomplete';end if;end loop;
  for entry in select value from jsonb_array_elements_text(cfg->'customers')loop
   if not exists(select 1 from profiles where id=entry::uuid and role='customer')then raise exception'pilot_config_incomplete';end if;end loop;
  for entry in select value from jsonb_array_elements_text(cfg->'drivers')loop
   if not exists(select 1 from profiles where id=entry::uuid and role='driver'and driver_status='approved')then raise exception'pilot_config_incomplete';end if;end loop;
  for entry in select value from jsonb_array_elements_text(cfg->'stores')loop
   if not exists(select 1 from stores where id=entry::uuid)then raise exception'pilot_config_incomplete';end if;end loop;
 end if;
 update pilot_private.config set value=cfg,paused=p_paused,actor=auth.uid(),at=now()where id;
 select to_jsonb(c)into v from pilot_private.config c where id;
 insert into pilot_private.config_events(actor,before_value,after_value)values(auth.uid(),old_config,v);return v;
end $$;
create or replace function pilot_private.driver_allowed(p_driver uuid)returns boolean
language sql stable security definer set search_path=public as $$select coalesce((select value->'drivers'?p_driver::text from pilot_private.config where id),false)$$;
create or replace function pilot_private.guard_order()returns trigger
language plpgsql security definer set search_path=public as $$
declare c pilot_private.config;local_time timestamp;minute_n int;active_n int;daily_n int;begin
 select *into c from pilot_private.config where id;
 if tg_op='UPDATE'then
  if new.driver_id is distinct from old.driver_id and new.driver_id is not null and exists(select 1 from pilot_private.admissions where order_id=old.id)and not pilot_private.driver_allowed(new.driver_id)then raise exception'pilot_driver_not_invited';end if;
  return new;
 end if;
 if c.paused or c.value is null then raise exception'pilot_paused';end if;
 if not(c.value->'customers'?new.customer_id::text)or not(c.value->'stores'?new.store_id::text)then raise exception'pilot_not_invited';end if;
 if now()<(c.value->>'valid_from')::timestamptz or now()>=(c.value->>'valid_until')::timestamptz then raise exception'pilot_closed';end if;
 local_time:=now()at time zone(c.value->>'timezone');minute_n:=extract(hour from local_time)::int*60+extract(minute from local_time)::int;
 if not(c.value->'weekdays'@>jsonb_build_array(extract(isodow from local_time)::int))or minute_n<(c.value->>'open_minute')::int or minute_n>=(c.value->>'close_minute')::int then raise exception'pilot_closed';end if;
 -- Scheduled orders need a separately reviewed operational plan; no unapproved overnight carry-over.
 if new.scheduled_for is not null then raise exception'pilot_scheduled_unavailable';end if;
 if new.lat is null or new.lng is null or new.lat<(c.value->>'min_lat')::double precision or new.lat>(c.value->>'max_lat')::double precision or new.lng<(c.value->>'min_lng')::double precision or new.lng>(c.value->>'max_lng')::double precision then raise exception'pilot_region';end if;
 perform pg_advisory_xact_lock(hashtextextended('pilot:admission-capacity',0));
 select count(*)into active_n from pilot_private.admissions a join orders o on o.id=a.order_id where o.status in('pending','preparing','ready','pickedup');
 if active_n>=(c.value->>'max_active')::int then raise exception'pilot_capacity';end if;
 select count(*)into daily_n from pilot_private.admissions a where(a.at at time zone(c.value->>'timezone'))::date=local_time::date;
 if daily_n>=(c.value->>'daily_orders')::int then raise exception'pilot_daily_limit';end if;
 return new;
end $$;
create or replace function pilot_private.record_admission()returns trigger
language plpgsql security definer set search_path=public as $$begin
 insert into pilot_private.admissions(order_id,customer_id,store_id)values(new.id,new.customer_id,new.store_id);return new;end $$;
drop trigger if exists pilot_admission_guard on orders;create trigger pilot_admission_guard before insert or update of driver_id on orders for each row execute function pilot_private.guard_order();
drop trigger if exists pilot_admission_record on orders;create trigger pilot_admission_record after insert on orders for each row execute function pilot_private.record_admission();
-- Filter automatic dispatch as well as the assignment trigger; exact current source must be present.
do $$declare body text;begin
 body:=pg_get_functiondef('public.eligible_couriers(bigint,boolean)'::regprocedure);
 if position('and fulfillment_private.unblocked(p_order)'in body)=0 then raise exception'pilot_source_mismatch';end if;
 body:=replace(body,'and fulfillment_private.unblocked(p_order)','and fulfillment_private.unblocked(p_order) and pilot_private.driver_allowed(p.id)');execute body;
end $$;
revoke all on all functions in schema pilot_private from public,anon,authenticated;
revoke all on function public.configure_pilot_admission(jsonb,boolean)from public,anon;
grant execute on function public.configure_pilot_admission(jsonb,boolean)to authenticated;
commit;
