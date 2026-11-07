CREATE OR REPLACE FUNCTION public.guard_profile()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin() then return new; end if;
  if old.banned_at is not null then raise exception 'not_allowed'; end if;
  if new.role <> old.role or new.driver_status is distinct from old.driver_status
     or new.cash_limit <> old.cash_limit or new.accept_blocked <> old.accept_blocked
     or new.banned_at is distinct from old.banned_at or new.banned_reason is distinct from old.banned_reason
     or new.phone_changed_at is distinct from old.phone_changed_at then
    raise exception 'not_allowed';
  end if;
  return new;
end $function$;