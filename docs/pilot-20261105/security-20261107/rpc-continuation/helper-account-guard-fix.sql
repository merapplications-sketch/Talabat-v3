CREATE OR REPLACE FUNCTION public.has_perm(p text)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ SELECT public.account_enabled() AND EXISTS(SELECT 1 FROM public.profiles u WHERE u.id=auth.uid() AND u.banned_at IS NULL AND (u.role='admin' OR EXISTS(SELECT 1 FROM public.staff_members s WHERE s.user_id=u.id AND s.active AND p=ANY(s.perms)))) $function$;

CREATE OR REPLACE FUNCTION public.is_admin()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ SELECT public.account_enabled() AND EXISTS(SELECT 1 FROM public.profiles WHERE id=auth.uid() AND role='admin' AND banned_at IS NULL) $function$;

CREATE OR REPLACE FUNCTION public.my_perms()
 RETURNS text[]
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ SELECT CASE WHEN NOT public.account_enabled() THEN NULL WHEN NOT EXISTS(SELECT 1 FROM public.profiles WHERE id=auth.uid() AND banned_at IS NULL) THEN NULL WHEN public.is_admin() THEN ARRAY['orders','support','finance','stores','content'] ELSE (SELECT s.perms FROM public.staff_members s WHERE s.user_id=auth.uid() AND s.active AND cardinality(s.perms)>0) END $function$;

CREATE OR REPLACE FUNCTION public.owns_store(s uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select public.account_enabled() AND exists(select 1 from stores st join profiles p on p.id=st.owner_id where st.id=s and st.owner_id=auth.uid() and p.banned_at is null) $function$;
