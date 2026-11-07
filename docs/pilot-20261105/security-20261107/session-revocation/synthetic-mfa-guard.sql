CREATE TABLE security_private.mfa_required_users(user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE, required_at timestamptz NOT NULL DEFAULT now());
ALTER TABLE security_private.mfa_required_users ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON security_private.mfa_required_users FROM PUBLIC,anon,authenticated;
INSERT INTO security_private.mfa_required_users(user_id) VALUES('85fea11e-738c-4221-ac29-51d4ff50d594');
CREATE OR REPLACE FUNCTION public.account_enabled()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
 SELECT EXISTS(SELECT 1 FROM public.profiles p WHERE p.id=auth.uid() AND p.banned_at IS NULL)
 AND NOT EXISTS(SELECT 1 FROM security_private.revoked_sessions r
 WHERE r.user_id=auth.uid() AND r.session_id::text=auth.jwt()->>'session_id')
 AND (NOT EXISTS(SELECT 1 FROM security_private.mfa_required_users m WHERE m.user_id=auth.uid()) OR coalesce(auth.jwt()->>'aal','')='aal2')
$function$
;
