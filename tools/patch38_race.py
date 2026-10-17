"""Patch 38 — races with two real sessions on a LOCAL PostgreSQL test database (isolated stand-in data from
sql/test_patch38_setup.sql: the live functions installed locally from the rollback files, then patches 37 and 38).
NOT run on production; not a test of the live database.
  python3 tools/patch38_race.py [dbname]      (creates / replaces that local database; needs psycopg2)"""
import sys, threading, time, subprocess
import psycopg2
DB = sys.argv[1] if len(sys.argv) > 1 else 't38race'
FIN, DRV, OWN = 'f0000000-0000-0000-0000-00000000000f', 'd0000000-0000-0000-0000-00000000000d', 'e0000000-0000-0000-0000-00000000000e'
KEBAB, PIZZA = '50000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000002'
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def conn(user=None):
    c = psycopg2.connect(dbname=DB, user='root', host='/var/run/postgresql'); c.autocommit = False
    if user:
        with c.cursor() as k: k.execute("select set_config('request.jwt.claim.sub', %s, false)", (user,))
        c.commit()
    return c
def q1(sql, args=(), user=None):
    c = conn(user); k = c.cursor(); k.execute(sql, args); r = k.fetchone() if k.description else None; c.commit(); c.close(); return r
def run_file(f, db=None):
    return subprocess.run(['psql', '-U', 'root', '-d', db or DB, '-q', '-v', 'ON_ERROR_STOP=1', '-f', f], capture_output=True, text=True)
def call(c, sql, args=()):
    try:
        with c.cursor() as k: k.execute(sql, args or None); r = k.fetchall() if k.description else None
        return ('ok', r)
    except Exception as e:
        c.rollback(); return ('err', str(e).split('\n')[0])
def race(first_sql, first_args, second_sql, second_args, u1, u2, hold=0.6):
    a, b = conn(u1), conn(u2); out = {}
    r1 = call(a, first_sql, first_args)
    def second():
        out['b'] = call(b, second_sql, second_args)
        if out['b'][0] == 'ok': b.commit()
    th = threading.Thread(target=second); th.start(); time.sleep(hold)
    out['waited'] = th.is_alive()
    if r1[0] == 'ok': a.commit()
    th.join(10); a.close(); b.close(); out['a'] = r1; return out
def order(store, status, cash=None, total=110, method=None):
    """an order of the NEW accounting (created after the start), with its rules snapshot, as place_order would leave it"""
    return q1("""insert into orders(store_id, customer_id, driver_id, status, payment, total, subtotal, discount, commission, driver_payout, cash_collected, pay_rules)
                 values (%s, 'c0000000-0000-0000-0000-000000000001', %s, %s, 'cash', %s, 100, 0, 10, 10, %s,
                         jsonb_build_object('accept_online', true, 'allow_wallet', true, 'allow_points', true, 'settle_method', %s::text)) returning id""",
              (store, DRV, status, total, cash, method))[0]

subprocess.run(['psql', '-U', 'root', '-d', 'postgres', '-q', '-c', 'drop database if exists %s' % DB, '-c', 'create database %s' % DB], check=True, capture_output=True)
r = run_file('sql/test_patch38_setup.sql'); assert r.returncode == 0, r.stderr[-400:]
q1("select set_accounting_start(now())", user=FIN)          # only the orders created by this tool belong to the new records
q1("update stores set owner_id = %s where id = %s", (OWN, KEBAB))

# ---- R6 first (needs an empty record table): rollback vs a record being written at the same moment ----
o = order(PIZZA, 'delivered', cash=110, method='platform_settles')
a = conn(FIN); ra = call(a, "select * from record_driver_settlement(%s, 'driver_to_platform', 50, 'K1', null, 'race-roll-0001')", (DRV,))
sql_rb = open('sql/rollback_patch38.sql').read()
out = {}
def rb():
    c = conn(); out['r'] = call(c, sql_rb.replace('begin;', '', 1).replace('commit;', '')); c.commit() if out['r'][0] == 'ok' else None; c.close()
th = threading.Thread(target=rb); th.start(); time.sleep(0.8); waited = th.is_alive(); a.commit(); a.close(); th.join(15)
cnt = q1("select count(*) from platform_driver_settlements")[0]
still = q1("select to_regprocedure('record_driver_settlement(uuid,text,numeric,text,text,text)') is not null")[0]
ok(ra[0] == 'ok' and waited and out['r'][0] == 'err' and 'rollback_unsafe' in out['r'][1] and cnt == 1 and still,
   'R6 rollback while a settlement is being written: the rollback waits for the lock, then refuses; the record (50) and the functions are kept')

# ---- R1: two finance staff take cash from the same courier at once (holds 110 − 50 = 60) ----
r = race("select * from record_driver_settlement(%s, 'driver_to_platform', 40, 'A', null, 'race-r1-a001')", (DRV,),
         "select * from record_driver_settlement(%s, 'driver_to_platform', 40, 'B', null, 'race-r1-b001')", (DRV,), FIN, FIN)
held = float(q1("select cash_held from driver_position(%s)", (DRV,), user=FIN)[0])
ok(r['waited'] and r['b'][0] == 'err' and 'amount_too_high' in r['b'][1] and held == 20, 'R1 two cash receipts at once → the second waits, then amount_too_high; held 60 → 20')
# ---- R2: the same form sent twice at the same moment (unknown answer, retry) ----
r = race("select * from record_driver_settlement(%s, 'driver_to_platform', 10, 'C', null, 'race-r2-same01')", (DRV,),
         "select * from record_driver_settlement(%s, 'driver_to_platform', 10, 'C', null, 'race-r2-same01')", (DRV,), FIN, FIN)
cnt = q1("select count(*) from platform_driver_settlements where client_key = 'race-r2-same01'")[0]
ok(r['b'][0] == 'ok' and cnt == 1 and r['a'][1][0][0] == r['b'][1][0][0], 'R2 the same form twice at once → ONE record, both answers carry its id')
# ---- R3: two store settlements at once (Pizza net due 90) ----
r = race("select * from record_store_settlement(%s, 60, 'bank', 'B1', null, 'done', 'race-r3-a001')", (PIZZA,),
         "select * from record_store_settlement(%s, 60, 'bank', 'B2', null, 'done', 'race-r3-b001')", (PIZZA,), FIN, FIN)
bal = float(q1("select pp_available from store_position(%s)", (PIZZA,), user=FIN)[0])
ok(r['waited'] and r['b'][0] == 'err' and 'amount_too_high' in r['b'][1] and bal == 30, 'R3 two store settlements at once → the second waits, then amount_too_high; balance 90 → 30 (never paid twice)')
# ---- R4: two store-payment forms for one order at once (different keys) ----
o2 = order(KEBAB, 'pickedup', method='driver_pays')
r = race("select * from record_store_payment(%s, 100, 'R4A', null, 'race-r4-a001')", (o2,), "select * from record_store_payment(%s, 100, 'R4B', null, 'race-r4-b001')", (o2,), DRV, DRV)
cnt = q1("select count(*) from driver_store_payments where order_id = %s", (o2,))[0]
ok(r['b'][0] == 'err' and cnt == 1, 'R4 two payment forms for one order at once → one record; the other refused (%s)' % r['b'][1][:50])
# ---- R5: the store confirms while finance disputes ----
pid = q1("select id from driver_store_payments where order_id = %s", (o2,))[0]
r = race("select decide_store_payment(%s, true)", (pid,), "select decide_store_payment(%s, false, 'x')", (pid,), OWN, FIN)
st = q1("select status from driver_store_payments where id = %s", (pid,))[0]
ok(r['waited'] and r['b'][0] == 'err' and 'already_decided' in r['b'][1] and st == 'confirmed', 'R5 confirm and dispute at once → the first decision stands, the second gets already_decided')
# ---- R8: the platform pays a store while the store confirms a courier payment (both paths, one store) ----
o3 = order(KEBAB, 'pickedup', method='driver_pays')
q1("select * from record_store_payment(%s, 100, 'R8', null, 'race-r8-p001')", (o3,), user=DRV)
pid3 = q1("select id from driver_store_payments where order_id = %s", (o3,))[0]
o4 = order(KEBAB, 'delivered', cash=110, method='platform_settles')                       # platform part of Kebab: 90
r = race("select * from record_store_settlement(%s, 90, 'bank', 'R8B', null, 'done', 'race-r8-s001')", (KEBAB,), "select decide_store_payment(%s, true)", (pid3,), FIN, OWN)
pos = q1("select row(cp_paid_confirmed, cp_paid_pending, pp_paid_done, pp_available)::text from store_position(%s)", (KEBAB,), user=FIN)[0]
ok(r['waited'] and r['a'][0] == 'ok' and r['b'][0] == 'ok' and pos == '(200.00,0.00,90.00,0.00)', 'R8 platform settlement + store confirmation at once on one store → serialised (the second waited); courier payment confirmed, platform part paid once %s' % pos)
# ---- R9: the platform pays while the store DISPUTES a courier payment ----
o5 = order(KEBAB, 'pickedup', method='driver_pays'); q1("select * from record_store_payment(%s, 100, 'R9', null, 'race-r9-p001')", (o5,), user=DRV)
pid5 = q1("select id from driver_store_payments where order_id = %s", (o5,))[0]
o6 = order(KEBAB, 'delivered', cash=110, method='platform_settles')
r = race("select decide_store_payment(%s, false, 'x')", (pid5,), "select * from record_store_settlement(%s, 90, 'bank', 'R9B', null, 'done', 'race-r9-s001')", (KEBAB,), OWN, FIN)
pos = q1("select row(cp_paid_disputed, pp_available)::text from store_position(%s)", (KEBAB,), user=FIN)[0]
ok(r['waited'] and r['b'][0] == 'ok' and pos.endswith(',0.00)') and pos.startswith('(100.00'), 'R9 dispute + platform settlement at once → serialised; the dispute does not open a platform payment for courier-paid goods %s' % pos)
# ---- R10: the courier records a payment while the platform pays the same store ----
o7 = order(KEBAB, 'pickedup', method='driver_pays'); o8 = order(KEBAB, 'delivered', cash=110, method='platform_settles')
r = race("select * from record_store_settlement(%s, 90, 'bank', 'R10B', null, 'done', 'race-r10-s001')", (KEBAB,), "select * from record_store_payment(%s, 100, 'R10', null, 'race-r10-p001')", (o7,), FIN, DRV)
pos = q1("select pp_available::text from store_position(%s)", (KEBAB,), user=FIN)[0]
cnt = q1("select count(*) from driver_store_payments where order_id = %s", (o7,))[0]
ok(r['waited'] and r['a'][0] == 'ok' and r['b'][0] == 'ok' and cnt == 1 and pos == '0.00', 'R10 courier payment + platform payment at once → serialised by the store lock; each covers its own orders, nothing paid twice')
# ---- R11: the same key at once with DIFFERENT data ----
r = race("select * from record_driver_settlement(%s, 'platform_to_driver', 5, 'K', null, 'race-r11-k001')", (DRV,), "select * from record_driver_settlement(%s, 'platform_to_driver', 6, 'K', null, 'race-r11-k001')", (DRV,), FIN, FIN)
ok(r['a'][0] == 'ok' and r['b'][0] == 'err' and 'key_reused' in r['b'][1], 'R11 the same key at once with another amount → the second is refused (key_reused), one record')
# ---- R12: «collected 100, payment 100 under dispute» → nothing may be taken from him: both orders in sequence, and at once ----
def r12_setup(tag):
    d = q1("insert into profiles(id, role, name) values (gen_random_uuid(), 'driver', %s) returning id::text", ('R12' + tag,))[0]
    o = q1("""insert into orders(store_id, customer_id, driver_id, status, payment, total, subtotal, discount, commission, driver_payout, cash_collected, pay_rules)
              values (%s, 'c0000000-0000-0000-0000-000000000001', %s, 'pickedup', 'cash', 110, 100, 0, 10, 10, null, '{"settle_method":"driver_pays"}') returning id""", (KEBAB, d))[0]
    q1("select * from record_store_payment(%s, 100, 'R12', null, %s)", (o, 'race-r12-p' + tag + '01'), user=d)
    q1("update orders set status = 'delivered', cash_collected = 100 where id = %s", (o,))      # collected 100, payment 100 pending
    return d, q1("select id from driver_store_payments where order_id = %s", (o,))[0]
def taken(d): return float(q1("select coalesce(sum(amount),0) from platform_driver_settlements where driver_id = %s and direction = 'driver_to_platform'", (d,))[0])
# a) dispute first, then try to take 100
d, pid = r12_setup('a')
q1("select decide_store_payment(%s, false, 'x')", (pid,), user=OWN)
c = conn(FIN); ra = call(c, "select * from record_driver_settlement(%s, 'driver_to_platform', 100, 'R12a', null, 'race-r12-sa01')", (d,)); c.commit(); c.close()
pos = q1("select row(store_paid_confirmed, store_paid_disputed, cash_held, can_hand_over, advance_due)::text from driver_position(%s)", (d,), user=FIN)[0]
ok(ra[0] == 'err' and 'nothing_due' in ra[1] and taken(d) == 0 and pos == '(0.00,100.00,100.00,0.00,0.00)',
   'R12a dispute, then «take 100» → refused (nothing_due); disputed 100 is neither a confirmed store payment nor an advance; taken 0 %s' % pos)
# b) try to take first (pending reserve), then dispute, then try again
d, pid = r12_setup('b')
c = conn(FIN); rb1 = call(c, "select * from record_driver_settlement(%s, 'driver_to_platform', 100, 'R12b', null, 'race-r12-sb01')", (d,)); c.commit(); c.close()
q1("select decide_store_payment(%s, false, 'x')", (pid,), user=OWN)
c = conn(FIN); rb2 = call(c, "select * from record_driver_settlement(%s, 'driver_to_platform', 100, 'R12b', null, 'race-r12-sb02')", (d,)); c.commit(); c.close()
ok(rb1[0] == 'err' and rb2[0] == 'err' and taken(d) == 0, 'R12b «take 100» while pending → refused; after the dispute → still refused; taken 0')
# c) at the same moment, both orders
for first in ('dispute', 'take'):
    d, pid = r12_setup('c' + first[0])
    take = ("select * from record_driver_settlement(%s, 'driver_to_platform', 100, 'R12c', null, %s)", (d, 'race-r12-sc' + first[0] + '1'))
    disp = ("select decide_store_payment(%s, false, 'x')", (pid,))
    r = race(*(disp + take + (OWN, FIN)) if first == 'dispute' else (take + disp + (FIN, OWN)), hold=0.5)
    ok(taken(d) == 0 and ((r['b'][0] == 'err' and 'nothing_due' in r['b'][1]) if first == 'dispute' else (r['a'][0] == 'err' and 'nothing_due' in r['a'][1])) and (r['waited'] if first == 'dispute' else True),
       'R12c at once (%s first) → the cash receipt is refused, taken 0%s' % (first, '; it waited for the dispute (shared courier lock)' if first == 'dispute' else ''))
# ---- R7: a failing transaction leaves nothing ----
c = conn(FIN); call(c, "select * from record_store_settlement(%s, 5, 'cash', 'X', null, 'done', 'race-r7-a001')", (PIZZA,)); c.rollback(); c.close()
ok(q1("select count(*) from platform_store_settlements where client_key = 'race-r7-a001'")[0] == 0, 'R7 a settlement whose transaction fails / is cancelled leaves no record')
print('\nPATCH38 RACES %d/%d' % (n - len(fails), n)); sys.exit(1 if fails else 0)
