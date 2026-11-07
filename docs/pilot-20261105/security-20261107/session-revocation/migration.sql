CREATE SCHEMA security_private;
REVOKE ALL ON SCHEMA security_private FROM PUBLIC,anon,authenticated;
CREATE TABLE security_private.revoked_sessions (
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 session_id uuid NOT NULL,
 revoked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(user_id,session_id)
);
REVOKE ALL ON security_private.revoked_sessions FROM PUBLIC,anon,authenticated;
CREATE FUNCTION security_private.revoke_on_ban() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 -- Capture on ban and again on unban; never remove the revocation record.
 IF new.banned_at IS DISTINCT FROM old.banned_at AND (new.banned_at IS NOT NULL OR old.banned_at IS NOT NULL) THEN
  INSERT INTO security_private.revoked_sessions(user_id,session_id)
  SELECT s.user_id,s.id FROM auth.sessions s WHERE s.user_id=new.id ON CONFLICT DO NOTHING;
 END IF;
 RETURN new;
END $$;
REVOKE ALL ON FUNCTION security_private.revoke_on_ban() FROM PUBLIC,anon,authenticated;
CREATE TRIGGER trg_revoke_sessions_on_ban AFTER UPDATE OF banned_at ON public.profiles FOR EACH ROW EXECUTE FUNCTION security_private.revoke_on_ban();
CREATE OR REPLACE FUNCTION public.account_enabled() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.profiles p WHERE p.id=auth.uid() AND p.banned_at IS NULL)
 AND NOT EXISTS(SELECT 1 FROM security_private.revoked_sessions r
 WHERE r.user_id=auth.uid() AND r.session_id::text=auth.jwt()->>'session_id')
$$;
CREATE FUNCTION public.pilot_session_token_hook(event jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM public.profiles p WHERE p.id=(event->>'user_id')::uuid AND p.banned_at IS NOT NULL)
 OR EXISTS(SELECT 1 FROM security_private.revoked_sessions r WHERE r.user_id=(event->>'user_id')::uuid AND r.session_id::text=event->'claims'->>'session_id') THEN
  RETURN jsonb_build_object('error',jsonb_build_object('http_code',403,'message','Session revoked. Sign in again.'));
 END IF;
 RETURN jsonb_build_object('claims',event->'claims');
END $$;
REVOKE ALL ON FUNCTION public.pilot_session_token_hook(jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.pilot_session_token_hook(jsonb) TO supabase_auth_admin;
CREATE FUNCTION public.pilot_check_session() RETURNS void
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF auth.role()='authenticated' AND NOT public.account_enabled() THEN
  RAISE SQLSTATE '42501' USING MESSAGE='account_blocked';
 END IF;
END $$;
REVOKE ALL ON FUNCTION public.pilot_check_session() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.pilot_check_session() TO anon,authenticated,service_role;
