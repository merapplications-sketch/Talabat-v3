-- Patch 23: FIX for the phone rules of patch 20 (found by the security self-check: a customer could still erase his number)
--
-- THE BUG: the trigger computed  v_free := (auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin())
-- When 'app.bypass' was never set on the database connection, current_setting(..., true) is NULL, so the whole expression
-- was NULL (false OR NULL OR false = NULL), "not v_free" was NULL, and every rule behind it was skipped:
--   - no phone change while an order is active, once every 24 hours, and no erasing the number.
-- (The phone FORMAT check was not affected.)  The expression is now NULL-safe. Safe to run more than once.
-- You do NOT need to run patch 20 or 22 again: they have been corrected in the files too, for new installations.

create or replace function trg_profile_phone() returns trigger language plpgsql set search_path = public as $$
declare v_p text;
  -- NULL-safe on purpose: current_setting(..., true) is NULL when the setting was never set, and (false OR NULL OR false) is NULL,
  -- which made "not v_free" NULL and silently switched every rule below OFF.
  v_free boolean := (auth.uid() is null) or (coalesce(current_setting('app.bypass', true), '') = '1') or coalesce(is_admin(), false);
begin
  if new.phone is distinct from old.phone then
    if new.phone is null or btrim(new.phone) = '' then
      if old.phone is not null and not v_free then raise exception 'bad_phone'; end if;   -- cannot erase the number to dodge the rules
      new.phone := null; return new;
    end if;
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
    if v_p is distinct from old.phone and old.phone is not null and not v_free and new.role = 'customer' then
      if exists (select 1 from orders where customer_id = new.id and status in ('pending', 'preparing', 'ready', 'pickedup')) then
        raise exception 'phone_locked';
      end if;
      if old.phone_changed_at is not null and old.phone_changed_at > now() - interval '24 hours' then
        raise exception 'phone_cooldown';
      end if;
      new.phone_changed_at := now();
    end if;
  end if;
  return new;
end $$;
drop trigger if exists trg_profile_phone on profiles;
create trigger trg_profile_phone before update of phone on profiles for each row execute function trg_profile_phone();
