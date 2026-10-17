-- =============================================================================================
-- TRANSITION RECONCILIATION — ONE read-only SELECT (one CSV result) to review BEFORE the new accounting start is chosen
-- (patch 38). Works on the CURRENT live schema (no patch needed). Nothing is changed or moved. No names, phones or addresses:
-- couriers appear by id only, stores by name (a business). NOT RUN ANYWHERE. Columns: section | item | n | amount | detail
-- What it shows: what the OLD records still hold when the start is set — they stay with the old cash_balances /
-- settle_driver_cash and are never moved into the new records automatically.
-- =============================================================================================
select * from (
  -- 1) courier cash the old model still counts (delivered cash orders not marked settled)
  select '1 old courier cash' as section, o.driver_id::text as item, count(*) as n, round(sum(o.cash_collected), 2) as amount,
         'from ' || to_char(min(o.done_at) at time zone 'Asia/Dushanbe', 'YYYY-MM-DD') || ' to ' || to_char(max(o.done_at) at time zone 'Asia/Dushanbe', 'YYYY-MM-DD') as detail
    from orders o where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null and o.driver_id is not null
   group by o.driver_id
  union all
  -- 2) cash recorded on orders that are no longer delivered (cancelled / rejected after the courier collected)
  select '2 cash on non-delivered', o.status::text, count(*), round(sum(o.cash_collected), 2), 'settled marks: ' || count(o.cash_settled_at)
    from orders o where o.status <> 'delivered' and o.cash_collected is not null group by o.status
  union all
  -- 3) orders still open now (they would be created BEFORE the start, so they stay with the old records)
  select '3 open orders', o.status::text, count(*), round(sum(o.total), 2),
         'cash: ' || count(*) filter (where o.payment ~ '^(cash|Cash|Наличн)') || ', with wallet: ' || count(*) filter (where coalesce(o.wallet_used, 0) > 0)
    from orders o where o.status in ('pending', 'preparing', 'ready', 'pickedup') group by o.status
  union all
  -- 4) what the old «receive all» marked during the last 30 days (context for the start date)
  select '4 old settlements 30 days', to_char(o.cash_settled_at at time zone 'Asia/Dushanbe', 'YYYY-MM-DD'), count(*), round(sum(o.cash_collected), 2), ''
    from orders o where o.cash_settled_at > now() - interval '30 days' group by 2
  union all
  -- 5) delivered orders per store over the last 30 days (store payables are not recorded anywhere today)
  select '5 store deliveries 30 days', s.name, count(o.id), round(sum(o.subtotal - o.discount), 2),
         'commission ' || round(sum(coalesce(o.commission, 0)), 2) || ', paid by the store (points+cashback+free delivery) '
         || round(sum(coalesce(o.points_value, 0) + coalesce(o.cashback, 0) + coalesce(o.fee_waived, 0)), 2)
         || case when count(*) filter (where o.commission_pct is null) > 0 then ', WITHOUT recorded commission: ' || count(*) filter (where o.commission_pct is null) else '' end
    from orders o join stores s on s.id = o.store_id
   where o.status = 'delivered' and o.done_at > now() - interval '30 days' group by s.name
  union all
  -- 6) payment methods used over the last 30 days (electronic ones have NO capture record today)
  select '6 payment methods 30 days', o.payment, count(*), round(sum(o.total - coalesce(o.wallet_used, 0)), 2), 'status delivered: ' || count(*) filter (where o.status = 'delivered')
    from orders o where o.created_at > now() - interval '30 days' group by o.payment
) x
order by 1, 2;
