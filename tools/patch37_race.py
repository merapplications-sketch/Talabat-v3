"""Patch 37 — races (refunds; courier / store money races: tools/patch38_race.py) with two real sessions on a LOCAL PostgreSQL test database (isolated stand-in data, sql/test_patch37_setup.sql).
NOT run on production. Each race runs first on a LOCAL COPY of the live definitions read on 17 Oct (installed from the rollback files)
to show the gap, then with patch 37 applied locally.
  python3 tools/patch37_race.py [dbname]      (creates / replaces that local database; needs psycopg2)"""
import sys, threading, time, subprocess
import psycopg2
DB = sys.argv[1] if len(sys.argv) > 1 else 't37race'
SUP, FIN, CUS, DRV = '50000000-0000-0000-0000-000000000005', 'f0000000-0000-0000-0000-00000000000f', 'c0000000-0000-0000-0000-00000000000c', 'd0000000-0000-0000-0000-00000000000d'
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
def q1(sql, args=()):
    c = conn(); k = c.cursor(); k.execute(sql, args); r = k.fetchone() if k.description else None; c.commit(); c.close(); return r
def run_file(f):
    subprocess.run(['psql', '-U', 'root', '-d', DB, '-q', '-v', 'ON_ERROR_STOP=1', '-f', f], check=True, capture_output=True)
def call(c, sql, args=()):
    try:
        with c.cursor() as k: k.execute(sql, args); r = k.fetchall() if k.description else None
        return ('ok', r)
    except Exception as e:
        c.rollback(); return ('err', str(e).split('\n')[0])
def race(first_sql, first_args, second_sql, second_args, u1, u2, hold=0.6):
    """session 1 runs its statement and keeps the transaction open; session 2 starts meanwhile; then session 1 commits."""
    a, b = conn(u1), conn(u2); out = {}
    r1 = call(a, first_sql, first_args)
    def second():
        out['b'] = call(b, second_sql, second_args)
        if out['b'][0] == 'ok': b.commit()
    th = threading.Thread(target=second); th.start(); time.sleep(hold)
    out['waited'] = th.is_alive()
    if r1[0] == 'ok': a.commit()
    th.join(10); a.close(); b.close(); out['a'] = r1; return out
def new_order(status, payment, total, wallet=0, cash=None, driver=None):
    oid = q1("insert into orders(customer_id, driver_id, status, payment, total, wallet_used, cash_collected) values (%s,%s,%s,%s,%s,%s,%s) returning id",
             (CUS, driver, status, payment, total, wallet, cash))[0]
    if wallet: q1("insert into wallet_entries(user_id, amount, kind, order_id) values (%s, %s, 'spend', %s)", (CUS, -wallet, oid))
    return oid
def ticket(oid, status='resolved'):
    # a closed ticket can coexist with another one of the same order (one OPEN ticket per order)
    return q1("insert into support_tickets(customer_id, order_id, status) values (%s, %s, %s) returning id", (CUS, oid, status))[0]
def refunded(oid): return float(q1("select coalesce(sum(amount),0) from wallet_entries where order_id = %s and kind = 'refund'", (oid,))[0])

subprocess.run(['psql', '-U', 'root', '-d', 'postgres', '-q', '-c', 'drop database if exists %s' % DB, '-c', 'create database %s' % DB], check=True, capture_output=True)
run_file('sql/test_patch37_setup.sql')            # stand-in schema + the local copy of the live functions
for phase in ('live', 'patch'):
    if phase == 'patch': run_file('sql/schema_patch37.sql')
    P = phase == 'patch'
    # ---- R1: two tickets of one delivered order (cash 100 recorded), 70 each at the same moment ----
    oid = new_order('delivered', 'cash', 100, cash=100, driver=DRV); t1, t2 = ticket(oid, 'in_progress'), ticket(oid)
    r = race("select ticket_set_status(%s,'resolved','a',70)", (t1,), "select ticket_set_status(%s,'resolved','b',70)", (t2,), SUP, SUP)
    tot = refunded(oid)
    if P: ok(r['waited'] and r['b'][0] == 'err' and 'refund_too_high' in r['b'][1] and tot == 70, 'R1 patch: two tickets of one order at once → the second waits, then refund_too_high; total 70 ≤ 100 (%s)' % r['b'][1][:40])
    else: ok(tot == 140, 'R1 local copy of live defs (gap shown): both refunds pass at the same moment → 140 refunded on a 100 order (total %s)' % tot)
    # ---- R2: cancel (automatic wallet return) at the same moment as a refund of the wallet part ----
    oid = new_order('preparing', 'cash', 90, wallet=40); tk = ticket(oid, 'in_progress')
    r = race("update orders set status = 'cancelled' where id = %s", (oid,), "select ticket_set_status(%s,'resolved','w',40)", (tk,), CUS, SUP)
    back = float(q1("select coalesce(sum(amount),0) from wallet_entries where order_id = %s and kind in ('return','refund')", (oid,))[0])
    if P: ok(r['waited'] and r['b'][0] == 'err' and back == 40, 'R2 patch: cancel + refund at once → refund refused after the cancel (%s); customer gets 40 once' % r['b'][1][:40])
    else: ok(back == 80, 'R2 local copy of live defs (gap shown): cancel + refund at once → the wallet part comes back twice (%s for 40 paid)' % back)
    # ---- R2b: refund first, cancel after (order still in progress) — the proposal «refund after the end» is NOT in patch 37 ----
    oid = new_order('preparing', 'cash', 90, wallet=40); tk = ticket(oid, 'in_progress')
    c = conn(SUP); r1 = call(c, "select ticket_set_status(%s,'resolved','w',40)", (tk,)); c.commit() if r1[0] == 'ok' else None; c.close()
    q1("update orders set status = 'cancelled' where id = %s", (oid,))
    back = float(q1("select coalesce(sum(amount),0) from wallet_entries where order_id = %s and kind in ('return','refund')", (oid,))[0])
    ok(back == 80, 'R2b %s (gap shown, needs the proposal / a decision): refund while in progress, then cancel → 80 back for 40 paid' % ('patch 37 alone' if P else 'local copy of live defs'))
    if P:
        run_file('sql/option_refund_after_finish.sql')
        oid = new_order('preparing', 'cash', 90, wallet=40); tk = ticket(oid, 'in_progress')
        r = race("update orders set status = 'cancelled' where id = %s", (oid,), "select ticket_set_status(%s,'resolved','w',40)", (tk,), CUS, SUP)
        back = float(q1("select coalesce(sum(amount),0) from wallet_entries where order_id = %s and kind in ('return','refund')", (oid,))[0])
        oid2 = new_order('preparing', 'cash', 90, wallet=40); tk2 = ticket(oid2, 'in_progress')
        c = conn(SUP); r1 = call(c, "select ticket_set_status(%s,'resolved','w',40)", (tk2,)); c.close()
        ok(back == 40 and r1[0] == 'err' and 'order_not_finished' in r1[1], 'R2b with the PROPOSAL applied locally: refund while in progress → order_not_finished; cancel + refund at once → 40 back once')
        run_file('sql/rollback_option_refund_after_finish.sql')
    # ---- R4: failure mid-way leaves nothing behind ----
    if P:
        oid = new_order('delivered', 'cash', 60, cash=60, driver=DRV); tk = ticket(oid, 'in_progress')
        c = conn(SUP); call(c, "select ticket_set_status(%s,'resolved','x',20)", (tk,)); c.rollback(); c.close()
        ok(refunded(oid) == 0 and q1("select status from support_tickets where id = %s", (tk,))[0] == 'in_progress', 'R4 patch: a refund whose transaction fails leaves the ticket and the wallet unchanged')
print('\nPATCH37 RACES %d/%d' % (n - len(fails), n)); sys.exit(1 if fails else 0)
