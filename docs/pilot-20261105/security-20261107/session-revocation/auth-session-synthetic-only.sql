CREATE OR REPLACE FUNCTION security_private.revoke_on_ban() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF new.banned_at IS DISTINCT FROM old.banned_at
 AND (new.banned_at IS NOT NULL OR old.banned_at IS NOT NULL) THEN
  INSERT INTO security_private.revoked_sessions(user_id,session_id)
  SELECT s.user_id,s.id FROM auth.sessions s WHERE s.user_id=new.id
  ON CONFLICT DO NOTHING;
  -- Dedicated synthetic account only. Protected accounts are excluded.
  IF new.id='85fea11e-738c-4221-ac29-51d4ff50d594'::uuid THEN
   DELETE FROM auth.sessions WHERE user_id=new.id;
  END IF;
 END IF;
 RETURN new;
END $$;
