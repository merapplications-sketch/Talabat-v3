-- =============================================================================================
-- ROLLBACK of patch 36 (v57). NOT RUN ANYWHERE. Two levels:
--
-- LEVEL 1 — stop receiving at once, keep everything (no data change except one setting):
--     update lead_settings set value = 0 where key = 'global_hour';   -- every submission answers «busy», nothing created
--   and/or empty CFG in partner.html (the form switches off), and/or remove the Edge Function.
--   Undo: put the previous value back.
--
-- LEVEL 2 — remove patch 36 completely (this file). Stops by itself, changing nothing:
--   * if website requests exist (export them first; then run with: set patch36.drop_leads = 'yes';)
--   * if a banner still links to the partner page (change those banners first)
-- Restores: store_requests as in patch 19/26 (status check, NOT NULL owner / location), banners check without 'partner'
-- (only if patch 36 added it in the simple form), drops lead_* tables and functions.
-- =============================================================================================
begin;
do $$
declare n_leads int; n_ban int := 0; v_name text; v_def text;
begin
  select count(*) into n_leads from store_requests where kind = 'lead';
  if n_leads > 0 and coalesce(current_setting('patch36.drop_leads', true), '') <> 'yes' then
    raise exception 'rollback36: % website requests exist. Export them, then: set patch36.drop_leads = ''yes''; and run again. Nothing changed.', n_leads;
  end if;
  if to_regclass('public.banners') is not null then
    select count(*) into n_ban from banners where link_type = 'partner';
    if n_ban > 0 then raise exception 'rollback36: % banners link to the partner page; change them first. Nothing changed.', n_ban; end if;
    select conname, pg_get_constraintdef(oid) into v_name, v_def from pg_constraint
     where conrelid = 'public.banners'::regclass and contype = 'c' and pg_get_constraintdef(oid) ~ ', ''partner''::text\]';
    if v_name is not null then
      execute format('alter table banners drop constraint %I', v_name);
      execute format('alter table banners add constraint %I %s', v_name, replace(v_def, ', ''partner''::text]', ']'));
    end if;
  end if;
  delete from store_requests where kind = 'lead';
end $$;

drop trigger if exists trg_audit_store_leads on store_requests;
drop function if exists lead_submit(text, text, text, text, text);
drop function if exists lead_set_status(uuid, text, text);
drop function if exists lead_link(uuid, uuid);
drop function if exists lead_cleanup();
drop function if exists lead_setting(text);
drop table if exists lead_attempts;
drop table if exists lead_settings;
drop index if exists store_req_lead_open_phone;
drop index if exists store_req_lead_store;
drop index if exists store_req_kind_status_idx;
alter table store_requests drop constraint if exists store_requests_kind_shape;
alter table store_requests add constraint store_requests_status_check check (status in ('pending', 'approved', 'rejected'));
alter table store_requests alter column user_id set not null;
alter table store_requests alter column lat set not null;
alter table store_requests alter column lng set not null;
alter table store_requests drop column if exists updated_by;
alter table store_requests drop column if exists updated_at;
alter table store_requests drop column if exists kind;
commit;
