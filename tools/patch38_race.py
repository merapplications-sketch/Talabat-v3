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
bal = float(q1("select balance from store_position(%s)", (PIZZA,), user=FIN)[0])
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
# ---- R7: a failing transaction leaves nothing ----
c = conn(FIN); call(c, "select * from record_store_settlement(%s, 5, 'cash', 'X', null, 'done', 'race-r7-a001')", (PIZZA,)); c.rollback(); c.close()
ok(q1("select count(*) from platform_store_settlements where client_key = 'race-r7-a001'")[0] == 0, 'R7 a settlement whose transaction fails / is cancelled leaves no record')
print('\nPATCH38 RACES %d/%d' % (n - len(fails), n)); sys.exit(1 if fails else 0)
