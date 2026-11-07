ALTER ROLE authenticator SET pgrst.db_pre_request='public.pilot_check_session';
NOTIFY pgrst, 'reload config';
