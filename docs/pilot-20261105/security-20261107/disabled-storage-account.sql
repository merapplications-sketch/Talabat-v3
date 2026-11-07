CREATE OR REPLACE FUNCTION public.account_enabled() RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public' AS $fn$ SELECT EXISTS(SELECT 1 FROM public.profiles WHERE id=auth.uid() AND banned_at IS NULL) $fn$;
REVOKE ALL ON FUNCTION public.account_enabled() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.account_enabled() TO anon, authenticated;
CREATE POLICY pilot_active_storage_account ON storage.objects AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());