-- =============================================================================================
-- PATCH 35 — UAT batch 1: admin order search over ALL orders (not only the 300 loaded on screen).
-- Run after patch 34. Safe to run again. Read-only: changes no data, no rules, no balances.
--  * Search by order number, customer name, or customer phone (the phone saved with the order).
--  * Same permission as reading orders in the admin panel: admin, or staff with "orders" or "support".
--  * Optional status filter; newest first; at most 100 results.
-- =============================================================================================
create or replace function admin_search_orders(p_q text, p_status text default null, p_limit int default 50)
returns table(id bigint)
language plpgsql stable security definer set search_path = public as $$
declare
  q text := btrim(coalesce(p_q, ''));
  d text := regexp_replace(btrim(coalesce(p_q, '')), '\D', '', 'g');
  n bigint := null;
  lk text;
begin
  if not (has_perm('orders') or has_perm('support')) then raise exception 'not_allowed'; end if;
  if char_length(q) < 1 or char_length(q) > 60 then raise exception 'bad_value'; end if;
  if p_status is not null and p_status not in ('pending','preparing','ready','pickedup','delivered','rejected','cancelled') then raise exception 'bad_value'; end if;
  if q ~ '^#?[0-9]{1,15}$' then n := ltrim(q, '#')::bigint; end if;
  -- the typed text is matched literally (%, _ and \ have no special meaning)
  lk := '%' || replace(replace(replace(q, '\', '\\'), '%', '\%'), '_', '\_') || '%';
  return query
    select o.id from orders o
     where (p_status is null or o.status::text = p_status)
       and ((n is not null and o.id = n)
            or (char_length(d) >= 4 and exists (select 1 from order_customer_phone cp
                  where cp.order_id = o.id and regexp_replace(coalesce(cp.phone, ''), '\D', '', 'g') like '%' || d || '%'))
            or (char_length(q) >= 2 and coalesce(o.customer_name, '') ilike lk))
     order by o.created_at desc
     limit least(greatest(coalesce(p_limit, 50), 1), 100);
end $$;
revoke all on function admin_search_orders(text, text, int) from public, anon;
grant execute on function admin_search_orders(text, text, int) to authenticated;
