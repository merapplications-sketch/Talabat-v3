begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data)values
('90000000-0000-0000-0000-000000003051','{"name":"Synthetic finance actor"}'),
('90000000-0000-0000-0000-000000003052','{"name":"Synthetic second finance actor"}');
insert into staff_members(user_id,perms)values('90000000-0000-0000-0000-000000003051',array['finance']),('90000000-0000-0000-0000-000000003052',array['finance']);
-- Cache marker only: no wallet entry, settlement, order, receipt or money operation.
insert into finance_private.commands(request,actor,operation,target,amount_input,note_input,result)values('90000000-0000-0000-0000-000000003053','90000000-0000-0000-0000-000000003051','wallet_adjust','90000000-0000-0000-0000-000000003051',1,'Synthetic cache only','{"marker":"synthetic-cache"}');
reset role;select set_config('request.jwt.claims','{}',true);

set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003051","role":"authenticated"}',true);
do $$declare s jsonb;r jsonb;e text;begin
s:=finance_command_status('90000000-0000-0000-0000-000000003053');
begin r:=finance_execute('90000000-0000-0000-0000-000000003053','wallet_adjust','90000000-0000-0000-0000-000000003051',1,'Synthetic cache only');exception when raise_exception then e:=sqlerrm;end;
if s is distinct from '{"marker":"synthetic-cache"}'::jsonb or r is distinct from s or e is not null then raise exception 'ASSERT active cache';end if;
perform set_config('test.finance_active',jsonb_build_object('status',s,'execute',r,'error',e)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);

set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003052","role":"authenticated"}',true);
do $$declare s jsonb;r jsonb;e text;begin
s:=finance_command_status('90000000-0000-0000-0000-000000003053');
begin r:=finance_execute('90000000-0000-0000-0000-000000003053','wallet_adjust','90000000-0000-0000-0000-000000003051',1,'Synthetic cache only');exception when raise_exception then e:=sqlerrm;end;
if s is not null or r is not null or e is distinct from 'request_conflict' then raise exception 'ASSERT cross_actor';end if;
perform set_config('test.finance_cross_actor',jsonb_build_object('status',s,'execute',r,'error',e)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set active=false where user_id='90000000-0000-0000-0000-000000003051';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003051","role":"authenticated"}',true);
do $$declare s jsonb;r jsonb;e text;begin
s:=finance_command_status('90000000-0000-0000-0000-000000003053');
begin r:=finance_execute('90000000-0000-0000-0000-000000003053','wallet_adjust','90000000-0000-0000-0000-000000003051',1,'Synthetic cache only');exception when raise_exception then e:=sqlerrm;end;
if s is not null or r is not null or e is distinct from 'not_allowed' then raise exception 'ASSERT inactive';end if;
perform set_config('test.finance_inactive',jsonb_build_object('status',s,'execute',r,'error',e)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set active=true,perms=array[]::text[] where user_id='90000000-0000-0000-0000-000000003051';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003051","role":"authenticated"}',true);
do $$declare s jsonb;r jsonb;e text;begin
s:=finance_command_status('90000000-0000-0000-0000-000000003053');
begin r:=finance_execute('90000000-0000-0000-0000-000000003053','wallet_adjust','90000000-0000-0000-0000-000000003051',1,'Synthetic cache only');exception when raise_exception then e:=sqlerrm;end;
if s is not null or r is not null or e is distinct from 'not_allowed' then raise exception 'ASSERT permission_removed';end if;
perform set_config('test.finance_permission_removed',jsonb_build_object('status',s,'execute',r,'error',e)::text,true);end $$;
reset role;select jsonb_build_object('active',current_setting('test.finance_active')::jsonb,'cross_actor',current_setting('test.finance_cross_actor')::jsonb,'inactive',current_setting('test.finance_inactive')::jsonb,'permission_removed',current_setting('test.finance_permission_removed')::jsonb) as result;rollback;
