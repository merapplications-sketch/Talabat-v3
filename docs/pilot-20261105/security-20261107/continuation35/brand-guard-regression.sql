-- Synthetic brand/store only; no orders, wallets, receipts, credentials or external calls.
begin; set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values ('90000000-0000-0000-0000-000000003521','{"name":"ASVS35 brand owner"}'),('90000000-0000-0000-0000-000000003522','{"name":"ASVS35 foreign owner"}');
insert into brands(id,name,owner_id) values('90000000-0000-0000-0000-000000003523','ASVS35 rollback brand','90000000-0000-0000-0000-000000003521');
insert into stores(id,name,category,owner_id,brand_id) values
('90000000-0000-0000-0000-000000003524','ASVS35 rollback branch A','rest','90000000-0000-0000-0000-000000003521','90000000-0000-0000-0000-000000003523'),
('90000000-0000-0000-0000-000000003525','ASVS35 rollback branch B','rest','90000000-0000-0000-0000-000000003521','90000000-0000-0000-0000-000000003523');
set local role authenticated;
select set_config('test.brand_result','{}',true);
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003521","role":"authenticated","aal":"aal2"}',true);
do $$declare n int;v uuid;r jsonb;begin
 select count(*) into n from brand_stats('90000000-0000-0000-0000-000000003523',30);if n<>2 then raise exception 'ASSERT positive stats';end if;
 v:=branch_create('90000000-0000-0000-0000-000000003523','positive','synthetic address',38.56,68.79,'+992900000001');
 r:=brand_sync_menu('90000000-0000-0000-0000-000000003524','90000000-0000-0000-0000-000000003525');
 perform set_config('test.brand_result',jsonb_build_object('active_stats',n,'active_create',v is not null,'active_sync',r)::text,true);
end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003522","role":"authenticated","aal":"aal2"}',true);
do $$declare n int;e text;begin
 select count(*) into n from brand_stats('90000000-0000-0000-0000-000000003523',30);if n<>0 then raise exception 'ASSERT foreign stats';end if;
 begin perform branch_create('90000000-0000-0000-0000-000000003523','foreign','synthetic address',38.56,68.79,'+992900000001');exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT foreign create';end if;
 e:=null;begin perform brand_sync_menu('90000000-0000-0000-0000-000000003524','90000000-0000-0000-0000-000000003525');exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT foreign sync';end if;
 perform set_config('test.brand_result',(current_setting('test.brand_result')::jsonb||jsonb_build_object('foreign_denied',true))::text,true);
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000003521';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003521","role":"authenticated","aal":"aal2"}',true);
do $$declare n int;e text;v uuid;r jsonb;begin
 if account_enabled() then raise exception 'ASSERT disabled fixture';end if;
 select count(*) into n from brand_stats('90000000-0000-0000-0000-000000003523',30);
 begin v:=branch_create('90000000-0000-0000-0000-000000003523','banned','synthetic address',38.56,68.79,'+992900000001');exception when others then e:=sqlerrm;end;
 perform set_config('test.brand_result',(current_setting('test.brand_result')::jsonb||jsonb_build_object('banned_enabled',false,'banned_stats',n,'banned_create_accepted',v is not null,'banned_create_error',e))::text,true);
 e:=null;begin r:=brand_sync_menu('90000000-0000-0000-0000-000000003524','90000000-0000-0000-0000-000000003525');exception when others then e:=sqlerrm;end;
 perform set_config('test.brand_result',(current_setting('test.brand_result')::jsonb||jsonb_build_object('banned_sync_result',r,'banned_sync_error',e))::text,true);
end $$;

reset role;select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=null where id='90000000-0000-0000-0000-000000003521';
insert into security_private.revoked_sessions(user_id,session_id) values('90000000-0000-0000-0000-000000003521','90000000-0000-0000-0000-000000003526');
insert into security_private.mfa_required_users(user_id) values('90000000-0000-0000-0000-000000003521');
set local role authenticated;
do $test$
declare c record;n int;e text;v uuid;r jsonb;outcomes jsonb:='[]';
begin
 for c in select * from (values
 ('reenabled_revoked','90000000-0000-0000-0000-000000003526','aal2',false),
 ('required_mfa_aal1','90000000-0000-0000-0000-000000003527','aal1',false),
 ('new_active_aal2','90000000-0000-0000-0000-000000003527','aal2',true)) as q(label,sid,aal,allowed)
 loop
  perform set_config('request.jwt.claims',jsonb_build_object('sub','90000000-0000-0000-0000-000000003521','session_id',c.sid,'role','authenticated','aal',c.aal)::text,true);
  if account_enabled() is distinct from c.allowed then raise exception 'ASSERT fixture state %',c.label;end if;
  select count(*) into n from brand_stats('90000000-0000-0000-0000-000000003523',30);
  if (c.allowed and n<>3) or (not c.allowed and n<>0) then raise exception 'ASSERT session stats %',c.label;end if;
  e:=null;v:=null;begin v:=branch_create('90000000-0000-0000-0000-000000003523',c.label,'synthetic address',38.56,68.79,'+992900000001');exception when others then e:=sqlerrm;end;
  if (c.allowed and (v is null or e is not null)) or (not c.allowed and (v is not null or e is distinct from 'account_blocked')) then raise exception 'ASSERT session create %',c.label;end if;
  e:=null;r:=null;begin r:=brand_sync_menu('90000000-0000-0000-0000-000000003524','90000000-0000-0000-0000-000000003525');exception when others then e:=sqlerrm;end;
  if (c.allowed and (r is null or e is not null)) or (not c.allowed and (r is not null or e is distinct from 'account_blocked')) then raise exception 'ASSERT session sync %',c.label;end if;
  outcomes:=outcomes||jsonb_build_array(jsonb_build_object('case',c.label,'allowed',c.allowed,'stats_rows',n,'create_accepted',v is not null,'sync_accepted',r is not null));
 end loop;
 perform set_config('test.brand_result',(current_setting('test.brand_result')::jsonb||jsonb_build_object('session_cases',outcomes))::text,true);
end $test$;

reset role;select current_setting('test.brand_result')::jsonb result;
rollback;

