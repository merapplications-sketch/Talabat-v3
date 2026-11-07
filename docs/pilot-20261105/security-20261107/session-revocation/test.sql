BEGIN;
SET LOCAL statement_timeout='15s';
SELECT set_config('test.uid','85fea11e-738c-4221-ac29-51d4ff50d594',true);
SELECT set_config('test.sid',(SELECT id::text FROM auth.sessions WHERE user_id=current_setting('test.uid')::uuid ORDER BY created_at DESC LIMIT 1),true);
SELECT set_config('test.results','{}',true);
DO $$DECLARE phase text; ok boolean; e text; claims jsonb; hook jsonb; r jsonb; BEGIN
 FOREACH phase IN ARRAY ARRAY['active','banned','reactivated'] LOOP
  PERFORM set_config('request.jwt.claims','{}',true);
  IF phase='banned' THEN UPDATE public.profiles SET banned_at=now() WHERE id=current_setting('test.uid')::uuid; END IF;
  IF phase='reactivated' THEN UPDATE public.profiles SET banned_at=null WHERE id=current_setting('test.uid')::uuid; END IF;
  claims:=jsonb_build_object('sub',current_setting('test.uid'),'role','authenticated','session_id',current_setting('test.sid'));
  PERFORM set_config('request.jwt.claims',claims::text,true);
  ok:=public.account_enabled();
  BEGIN PERFORM public.pilot_check_session();e:='ACCEPTED';EXCEPTION WHEN others THEN e:=sqlerrm;END;
  hook:=public.pilot_session_token_hook(jsonb_build_object('user_id',current_setting('test.uid'),'authentication_method','token_refresh','claims',claims));
  r:=jsonb_build_object('account_enabled',ok,'api_guard',e,'refresh_hook_denied',hook?'error');
  PERFORM set_config('test.results',(current_setting('test.results')::jsonb||jsonb_build_object(phase,r))::text,true);
 END LOOP;
 -- New session identity after reactivation; actual fresh password login is a separate UI test.
 claims:=jsonb_set(claims,'{session_id}',to_jsonb(gen_random_uuid()::text));
 hook:=public.pilot_session_token_hook(jsonb_build_object('user_id',current_setting('test.uid'),'authentication_method','password','claims',claims));
 PERFORM set_config('test.results',(current_setting('test.results')::jsonb||jsonb_build_object('fresh_session_hook_allowed',NOT(hook?'error')) )::text,true);
END $$;
SELECT current_setting('test.results')::jsonb || jsonb_build_object('auth_service_can_call_hook',has_function_privilege('supabase_auth_admin','public.pilot_session_token_hook(jsonb)','execute'),'client_cannot_call_hook',NOT has_function_privilege('authenticated','public.pilot_session_token_hook(jsonb)','execute')) results;
ROLLBACK;
