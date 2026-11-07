-- PROPOSAL ONLY. Not applied. Same signature and ACL; no historical row rewrite.
-- Read-only catalog check confirmed app/message/context/ua are nullable text.
CREATE OR REPLACE FUNCTION public.report_client_error(p_app text, p_message text, p_context text DEFAULT NULL::text, p_ua text DEFAULT NULL::text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
declare
  v_app text := case when p_app in ('customer','merchant','driver','admin') then p_app else 'unknown' end;
  v_message text := case when p_message ~ '^(runtime|promise):(Error|TypeError|RangeError|ReferenceError|SyntaxError|URIError|EvalError|AbortError|NetworkError)$' then p_message else 'client_error' end;
  v_context text := case when p_context ~ '^(core|admin|customer|merchant|driver|mobile|finance|returns|receipt|sdk|unknown|external)(:[0-9]{1,7}:[0-9]{1,7})?$' then p_context else 'unknown' end;
begin
  if auth.uid() is null then return; end if;
  if (select count(*) from public.client_errors where user_id=auth.uid() and at>now()-interval '1 hour') >= 10 then return; end if;
  delete from public.client_errors where at<now()-interval '30 days';
  insert into public.client_errors(user_id,app,message,context,ua)
    values(auth.uid(),v_app,v_message,v_context,NULL);
end $function$;
