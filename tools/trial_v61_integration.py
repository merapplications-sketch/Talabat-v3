"""v61 — ONE integration check of the order path across the four apps, at the database level (local PostgreSQL, isolated
stand-in data from sql/test_patch38_setup.sql = live definitions read 17 Oct + patches 37 and 38). NOT production, NOT the live DB.
Every step is done by the role that does it in the app, through the same server function the app calls (talabat-core.js):
  customer  place_order                      (TLB.placeOrder)          restaurant  set_order_status preparing / ready (TLB.setStatus)
  courier   set_order_status pickedup, record_store_payment, deliver_order (TLB.setStatus / recordStorePayment / deliver)
  finance   driver_position, store_position, record_driver_settlement, record_store_settlement (admin money cards)
  support   ticket_set_status (refund)       admin      set_order_status cancelled
Courier assignment: driver_accept is not part of the local stand-in, so the order is given to the courier directly (as dispatch would).
Money is checked numerically for every party: restaurant due, platform commission, what the courier paid / collected / kept,
what is left for each party — and the courier's pay is never counted twice.
  python3 tools/trial_v61_integration.py [dbname]      (creates / replaces that local database; needs psycopg2)"""
import sys, subprocess, json
import psycopg2
DB = sys.argv[1] if len(sys.argv) > 1 else 't61int'
ADM, FIN, STF, OWN, DRV = ('a0000000-0000-0000-0000-00000000000a', 'f0000000-0000-0000-0000-00000000000f', '70000000-0000-0000-0000-000000000007',
                           'e0000000-0000-0000-0000-00000000000e', 'd0000000-0000-0000-0000-00000000000d')
OWN2 = 'e0000000-0000-0000-0000-0000000000e2'
KEBAB, PIZZA = '50000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000002'
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def call(user, sql, args=()):
    """one request of one app user (own connection, own transaction) → ('ok', rows) or ('err', message)"""
    c = psycopg2.connect(dbname=DB, user='root', host='/var/run/postgresql'); k = c.cursor()
    try:
        k.execute("select set_config('request.jwt.claim.sub', %s, true)", (user or '',))
        k.execute(sql, args or None); r = k.fetchall() if k.description else None; c.commit(); return ('ok', r)
    except Exception as e:
        c.rollback(); return ('err', str(e).split('\n')[0])
    finally: c.close()
def err(r): return r[1] if r[0] == 'err' else 'ok'
def one(user, sql, args=()):
    r = call(user, sql, args); assert r[0] == 'ok', (sql, r); return r[1][0] if r[1] else None
def row(user, sql, args=()):
    """a position row as a dict of floats"""
    c = psycopg2.connect(dbname=DB, user='root', host='/var/run/postgresql'); k = c.cursor()
    k.execute("select set_config('request.jwt.claim.sub', %s, true)", (user,)); k.execute(sql, args or None)
    names = [d[0] for d in k.description]; v = k.fetchone(); c.commit(); c.close(); return {a: float(b) for a, b in zip(names, v)}

subprocess.run(['psql', '-U', 'root', '-d', 'postgres', '-q', '-c', 'drop database if exists %s' % DB, '-c', 'create database %s' % DB], check=True, capture_output=True)
r = subprocess.run(['psql', '-U', 'root', '-d', DB, '-q', '-v', 'ON_ERROR_STOP=1', '-f', 'sql/test_patch38_setup.sql'], capture_output=True, text=True); assert r.returncode == 0, r.stderr[-400:]
# people and agreements (stand-in): a second restaurant owner for Pizza; one customer with 500 in the wallet
one(None, "insert into profiles(id, role, name, phone) values (%s, 'merchant', 'Owner Pizza', '+992900000031')", (OWN2,))
one(None, "update stores set owner_id = %s where id = %s", (OWN2, PIZZA))
CUS = one(None, "insert into profiles(id, role, name, phone) values (gen_random_uuid(), 'customer', 'Trial customer', '+992900000032') returning id::text")[0]
one(None, "insert into wallet_entries(user_id, amount, kind) values (%s, 500, 'adjust')", (CUS,))
ok(call(STF, "select set_store_pay_rules(%s, true, true, true, 'driver_pays')", (KEBAB,))[0] == 'ok'
   and call(STF, "select set_store_pay_rules(%s, true, true, true, 'platform_settles')", (PIZZA,))[0] == 'ok', 'admin (stores staff): Kebab = «courier pays the place», Pizza = «platform settles»')
ok(call(FIN, "select set_accounting_start(now())")[0] == 'ok', 'admin (finance): the new accounting starts now')

def item(store): return one(None, "select id::text from menu_items where store_id = %s order by price desc limit 1", (store,))[0]
def place(store, qty, pay, wallet=None):
    r = call(CUS, "select place_order(%s, %s::jsonb, 0, %s, 'Rudaki 1', 38.5, 68.7, null, null, 20, %s, null, null)",
             (store, json.dumps([{'item_id': item(store), 'qty': qty}]), pay, wallet))
    assert r[0] == 'ok', r; return r[1][0][0]
def path(store, oid, owner, pay_store, collect):
    """restaurant prepares and hands over; courier picks up, pays the restaurant when the order is «courier pays», delivers"""
    s = [call(owner, "select set_order_status(%s, 'preparing')", (oid,)), call(owner, "select set_order_status(%s, 'ready')", (oid,))]
    one(None, "update orders set driver_id = %s where id = %s", (DRV, oid))            # stand-in for driver_accept
    s.append(call(DRV, "select set_order_status(%s, 'pickedup')", (oid,)))
    if pay_store is not None: s.append(call(DRV, "select * from record_store_payment(%s, %s, %s, null, %s)", (oid, pay_store, 'CHK-%s' % oid, 'trial-dsp-%06d' % oid)))
    s.append(call(DRV, "select deliver_order(%s, %s)", (oid, collect)))
    return [x[1] if x[0] == 'err' else 'ok' for x in s]
DP = "select * from driver_position(%s)"; SP = "select * from store_position(%s)"

# ===== 1. THE OWNER'S EXAMPLE: Kebab, meal 100 + delivery 20, cash =====
o1 = place(KEBAB, 2, 'cash')
o = one(None, "select subtotal, delivery_fee, total, commission, driver_payout, pay_rules->>'courier_pay', pay_rules->>'settle_method' from orders where id = %s", (o1,))
ok([float(x) for x in o[:5]] == [100, 20, 120, 10, 20] and o[5] == 'keeps_fee_from_cash' and o[6] == 'driver_pays',
   'customer: order placed — meal 100, delivery 20, total 120; commission 10 and courier pay 20 recorded; «keeps his pay from the cash» kept on the order')
st = path(KEBAB, o1, OWN, 100, 120)
ok(st == ['ok'] * 5, 'restaurant preparing → ready; courier picks up, records 100 paid to the restaurant, delivers collecting 120 (%s)' % st)
d = row(FIN, DP, (DRV,)); s = row(FIN, SP, (KEBAB,))
ok((d['collected'], d['store_paid'], d['pay_kept'], d['net'], d['can_hand_over'], d['owed_to_courier'], d['ps_pay_due']) == (120, 100, 20, 0, 0, 0, 0),
   'courier: paid the restaurant 100, collected 120, kept his 20 → hand over 0, owed 0, no platform pay due')
ok((s['cp_bill'], s['cp_paid'], s['cp_unpaid'], s['commission'], s['cp_owed_by_store'], s['pp_available']) == (100, 100, 0, 10, 10, 0),
   'restaurant: bill 100 received in full from the courier (nothing left); commission 10 owed BY THE RESTAURANT (not deducted); platform pays nothing')
ok(d['collected'] == s['cp_bill'] + d['pay_kept'] and d['pay_kept'] + d['ps_pay_earned'] == 20,
   'balance of the order: customer 120 = restaurant 100 + courier 20; the courier\'s pay 20 counted once (kept 20, platform-paid 0)')
ok(err(call(FIN, "select * from record_driver_settlement(%s, 'driver_to_platform', 1, 'K', null, 'trial-pds-000001')", (DRV,))).startswith('nothing_due')
   and err(call(FIN, "select * from record_driver_settlement(%s, 'platform_to_driver', 1, 'K', null, 'trial-pds-000002')", (DRV,))).startswith('nothing_due')
   and err(call(FIN, "select * from record_store_settlement(%s, 1, 'cash', 'K', null, 'done', 'trial-pss-000001')", (KEBAB,))).startswith('nothing_due'),
   'finance: nothing to take from the courier, nothing to pay him, nothing to pay the restaurant (no double payment)')
ok(call(OWN, "select count(*) from store_position(%s)", (KEBAB,))[1][0][0] == 1 and call(DRV, "select count(*) from driver_position(%s)", (DRV,))[1][0][0] == 1,
   'the restaurant and the courier each read their own position (merchant / driver apps)')

# ===== 2. «platform settles»: Pizza, meal 100 + delivery 20, cash =====
o2 = place(PIZZA, 1, 'cash')
ok(path(PIZZA, o2, OWN2, None, 120) == ['ok'] * 4 and err(call(DRV, "select * from record_store_payment(%s, 100, 'X', null, 'trial-dsp-x00001')", (o2,))).startswith('not_driver_pays'),
   'Pizza order through all apps; the courier cannot record a restaurant payment on a «platform settles» order')
d = row(FIN, DP, (DRV,)); s = row(FIN, SP, (PIZZA,))
ok((d['can_hand_over'], d['pay_kept'], d['ps_pay_due']) == (120, 20, 20) and (s['pp_net_due'], s['pp_available'], s['commission']) == (90, 90, 10),
   'platform settles: courier hands over 120 (keeps nothing on this order), his pay 20 paid by the platform; restaurant due 90 (100 − commission 10)')
r1 = call(FIN, "select * from record_driver_settlement(%s, 'driver_to_platform', 120, 'KASSA-1', null, 'trial-pds-000003')", (DRV,))
r2 = call(FIN, "select * from record_driver_settlement(%s, 'platform_to_driver', 20, 'PAY-1', null, 'trial-pds-000004')", (DRV,))
r3 = call(FIN, "select * from record_store_settlement(%s, 90, 'bank', 'BANK-1', null, 'done', 'trial-pss-000002')", (PIZZA,))
d = row(FIN, DP, (DRV,)); s = row(FIN, SP, (PIZZA,))
ok(r1[0] == r2[0] == r3[0] == 'ok' and (d['can_hand_over'], d['owed_to_courier'], d['ps_pay_due'], s['pp_available']) == (0, 0, 0, 0),
   'finance: receives 120 from the courier, pays him 20, pays Pizza 90 → everyone at 0; the platform keeps 120 − 20 − 90 = 10 = the commission')

# ===== 3. wallet + refund + cancel (SC: cancel first, then refund) on a «courier pays» order =====
o3 = place(KEBAB, 2, 'cash', 30)
ok(float(one(None, "select wallet_used from orders where id = %s", (o3,))[0]) == 30, 'customer: 30 from the wallet, 90 in cash')
ok(path(KEBAB, o3, OWN, 100, 90) == ['ok'] * 5, 'the order through all apps: the courier pays 100, collects 90')
d = row(FIN, DP, (DRV,))
ok((d['net'], d['owed_to_courier'], d['can_hand_over']) == (-30, 30, 0), 'courier: collected 90, paid 100, kept 20 → the platform owes him 30 (the wallet part it received)')
tk = one(None, "insert into support_tickets(customer_id, order_id, status) values (%s, %s, 'in_progress') returning id", (CUS, o3))[0]
ok(call(ADM, "select set_order_status(%s, 'cancelled')", (o3,))[0] == 'ok', 'admin cancels the delivered order (allowed today; «no cancel after delivery» not adopted)')
back = lambda: float(one(None, "select coalesce(sum(amount), 0) from wallet_entries where order_id = %s and kind in ('return', 'refund')", (o3,))[0])
ok(back() == 30, '… the wallet 30 comes back automatically')
ok(err(call(ADM, "select ticket_set_status(%s, 'resolved', 'r', 91)", (tk,))).startswith('refund_too_high')
   and call(ADM, "select ticket_set_status(%s, 'resolved', 'r', 90)", (tk,))[0] == 'ok' and back() == 120,
   'support: the collected cash 90 stays refundable after the cancel (91 refused, 90 ok) → 120 back for 120 paid')
d = row(FIN, DP, (DRV,)); s = row(FIN, SP, (KEBAB,))
ok((d['collected'], d['net'], d['owed_to_courier']) == (330, -30, 30) and (s['cp_bill'], s['cp_paid'], s['cp_unpaid']) == (200, 200, 0),
   'the cancel erases neither the cash the courier collected nor his payment to the restaurant (courier owed 30 unchanged; restaurant bill 200 paid 200)')
ok(s['gross'] == 100 and s['commission'] == 10, 'restaurant revenue / commission count delivered orders only (the existing formula): order 3 is no longer in them — an open decision, listed')
print('\nTRIAL v61 INTEGRATION %d/%d' % (n - len(fails), n)); sys.exit(1 if fails else 0)
