"""Native PostgreSQL only. Fresh local disposable databases; no live URL accepted.

Each scenario uses two independent authenticated sessions and an observer/gate
session. pg_stat_activity/pg_blocking_pids prove overlapping server lock waits.
No implementation changes, no old 53-test suites, no remote service credentials.
"""
import base64
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import uuid
import zlib

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'tests/base-lab/web'
OUT = ROOT / 'tests/native-postgres/result.json'
IDS = json.loads((BASE / 'ids.json').read_text())
PREFIX = 'talabot_native_'
GATE_DRIVER = 'finance-driver:' + IDS['driver']
report = {'pass': False, 'scope': 'new native multi-connection tests only',
          'old_53_rerun': False, 'live': False, 'published': False,
          'environment': {}, 'scenarios': [],
          'open': ['actual iPhone Safari', 'native print dialog', 'hosted Auth/PostgREST']}


def connect(database='postgres', name='native-observer'):
    # Fail closed: environment variables cannot redirect this harness to a live DB.
    assert os.environ.get('PGHOST') == '127.0.0.1'
    assert os.environ.get('PGPORT') == '5432'
    assert database == 'postgres' or database.startswith(PREFIX)
    return psycopg.connect(host='127.0.0.1', port=5432, user='postgres',
                           password=os.environ['PGPASSWORD'], dbname=database,
                           application_name=name, autocommit=True, connect_timeout=5)


def one(c, query, params=()):
    return c.execute(query, params).fetchone()[0]


def create_copy(c, name, template):
    c.execute(sql.SQL('create database {} template {}').format(sql.Identifier(name), sql.Identifier(template)))


def lock(c, key):
    c.execute('select pg_advisory_lock(hashtextextended(%s,0))', (key,))


def unlock(c, key):
    assert one(c, 'select pg_advisory_unlock(hashtextextended(%s,0))', (key,))


def wait_for(c, predicate, label):
    deadline = time.monotonic() + 18
    while time.monotonic() < deadline:
        rows = c.execute("select pid,application_name,state,wait_event_type,wait_event,pg_blocking_pids(pid) from pg_stat_activity where datname=current_database() and application_name like 'native-worker-%' order by application_name").fetchall()
        records = [dict(zip(['pid', 'name', 'state', 'wait_type', 'wait_event', 'blockers'], r)) for r in rows]
        if predicate(records):
            return records
        time.sleep(.025)
    raise AssertionError('server barrier timed out: ' + label + ' ' + str(records))


def snapshot(c, r1):
    result = {
        'orders': one(c, "select jsonb_agg(jsonb_build_object('id',id,'amount',cash_collected,'settled_at',cash_settled_at) order by id) from orders where id in (7001,7002)"),
        'cash_remaining': one(c, "select coalesce(sum(cash_collected),0) from orders where driver_id=%s and status='delivered' and cash_settled_at is null", (IDS['driver'],)),
        'commands': one(c, "select coalesce(jsonb_agg(result order by request),'[]') from finance_private.commands"),
        'settlement_audit': one(c, "select coalesce(jsonb_agg(jsonb_build_object('row_id',row_id,'actor',user_id,'details',details) order by id),'[]') from audit_log where table_name='orders' and details ? 'cash_settled_at'"),
        'wallet_entries': one(c, 'select count(*) from wallet_entries'),
    }
    if r1:
        result.update({
            'receipts': one(c, "select coalesce(jsonb_agg(finance_private.receipt_json(id) order by id),'[]') from finance_private.settlement_receipts"),
            'links': one(c, "select coalesce(jsonb_agg(jsonb_build_object('order',order_id,'receipt',receipt_id,'amount',amount) order by order_id),'[]') from finance_private.settlement_receipt_orders"),
            'times_match': one(c, 'select coalesce(bool_and(o.cash_settled_at=r.at),true) from finance_private.settlement_receipt_orders l join orders o on o.id=l.order_id join finance_private.settlement_receipts r on r.id=l.receipt_id'),
        })
    return result


def assert_clean(s, r1):
    assert s['cash_remaining'] == 100 and all(o['settled_at'] is None for o in s['orders'])
    assert s['commands'] == [] and s['settlement_audit'] == [] and s['wallet_entries'] == 0
    if r1:
        assert s['receipts'] == [] and s['links'] == []


def check_effect(s, r1, command_count):
    assert s['cash_remaining'] == 0 and all(o['settled_at'] for o in s['orders'])
    assert len(s['commands']) == command_count
    assert sum(x['amount'] for x in s['commands']) == 100
    ids = [str(i) for x in s['commands'] for i in x['orders']]
    assert sorted(ids) == ['7001', '7002']  # exact set, no duplicate settlement
    assert sorted(x['row_id'] for x in s['settlement_audit']) == ['7001', '7002']
    assert all(x['actor'] == IDS['accountant'] for x in s['settlement_audit'])
    assert s['wallet_entries'] == 0
    if r1:
        assert len(s['receipts']) == 1 and s['times_match']
        receipt = s['receipts'][0]
        assert receipt == s['commands'][0]['receipt']
        assert receipt['amount'] == 100 and receipt['currency'] == 'TJS'
        assert receipt['actor'] == IDS['accountant'] and receipt['driver'] == IDS['driver']
        assert receipt['orders'] == [{'id': '7001', 'amount': 57}, {'id': '7002', 'amount': 43}]
        assert len(s['links']) == 2 and sum(x['amount'] for x in s['links']) == 100


def worker(database, number, request, fail, commit_gate):
    with connect(database, 'native-worker-' + str(number)) as c:
        pid = one(c, 'select pg_backend_pid()')
        try:
            with c.transaction():
                c.execute('set local statement_timeout=25000')
                c.execute('set local role authenticated')
                c.execute("select set_config('request.jwt.claim.sub',%s,true)", (IDS['accountant'],))
                c.execute("select set_config('lab.inject_failure',%s,true)", ('yes' if fail else 'no',))
                result = one(c, "select finance_execute(%s,'settle_cash',%s,null,null)", (request, IDS['driver']))
                if commit_gate:
                    c.execute('select pg_advisory_xact_lock(hashtextextended(%s,0))', (commit_gate,))
            return {'pid': pid, 'request': request, 'success': True, 'result': result}
        except psycopg.Error as e:
            return {'pid': pid, 'request': request, 'success': False,
                    'sqlstate': e.sqlstate, 'error': e.diag.message_primary}


def scenario(control, r1, same, fail_stage=None):
    mode = 'R1' if r1 else 'A'
    label = mode + '-' + ('same-key' if same else 'different-keys') + '-' + (fail_stage or 'success')
    database = PREFIX + label.lower().replace('-', '_')
    create_copy(control, database, PREFIX + ('r1' if r1 else 'a'))
    record = {'name': label, 'patches': ['A', 'R1'] if r1 else ['A'], 'same_key': same, 'failure_stage': fail_stage}
    report['scenarios'].append(record)
    with connect(database) as observer:
        assert_clean(snapshot(observer, r1), r1)
        if fail_stage:
            table = {'command': 'commands', 'receipt': 'settlement_receipts', 'link': 'settlement_receipt_orders'}[fail_stage]
            observer.execute("create function finance_private.native_fail() returns trigger language plpgsql as $$ begin if current_setting('lab.inject_failure',true)='yes' then raise exception 'synthetic_native_failure'; end if; return new; end $$")
            observer.execute(sql.SQL('create trigger native_fail before insert on finance_private.{} for each row execute function finance_private.native_fail()').format(sql.Identifier(table)))
        key1 = str(uuid.uuid4())
        key2 = key1 if same else str(uuid.uuid4())
        after_gate = 'native-post-success:' + database if fail_stage else None
        lock(observer, GATE_DRIVER)
        if after_gate:
            lock(observer, after_gate)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        f1 = pool.submit(worker, database, 1, key1, bool(fail_stage), None)
        f2 = None
        try:
            wait_for(observer, lambda rows: any(r['name'] == 'native-worker-1' and r['wait_type'] == 'Lock' for r in rows), 'first waiting for driver gate')
            f2 = pool.submit(worker, database, 2, key2, False, after_gate)
            overlap = wait_for(observer, lambda rows: len(rows) == 2 and all(r['wait_type'] == 'Lock' and r['blockers'] for r in rows), 'both overlapping')
            record['overlap'] = overlap
            assert len(set(r['pid'] for r in overlap)) == 2
            # Same key: second waits for first request lock. Distinct keys: both
            # wait for the same driver lock held by the observer (or its queue).
            first_pid = next(r['pid'] for r in overlap if r['name'] == 'native-worker-1')
            if same:
                assert first_pid in next(r['blockers'] for r in overlap if r['name'] == 'native-worker-2')
            record['before_release'] = snapshot(observer, r1)
            assert_clean(record['before_release'], r1)
            unlock(observer, GATE_DRIVER)
            if fail_stage:
                a = f1.result(timeout=20)
                assert not a['success'] and a['error'] == 'synthetic_native_failure'
                observer_pid = one(observer, 'select pg_backend_pid()')
                record['peer_before_commit'] = wait_for(observer, lambda rows: any(r['name'] == 'native-worker-2' and r['wait_type'] == 'Lock' and observer_pid in r['blockers'] for r in rows), 'peer ready before commit')
                record['after_failed_transaction'] = snapshot(observer, r1)
                assert_clean(record['after_failed_transaction'], r1)
                unlock(observer, after_gate)
            a, b = f1.result(timeout=25), f2.result(timeout=25)
            record['responses'] = [a, b]
            if fail_stage:
                assert not a['success'] and b['success'] and b['result']['amount'] == 100
                expected_commands = 1
            elif same:
                assert a['success'] and b['success'] and a['result'] == b['result']
                expected_commands = 1
            elif r1:
                assert sum(r['success'] for r in (a, b)) == 1
                loser = next(r for r in (a, b) if not r['success'])
                assert loser['error'] == 'nothing_to_settle'
                expected_commands = 1
            else:
                assert a['success'] and b['success']
                assert sorted(r['result']['amount'] for r in (a, b)) == [0, 100]
                expected_commands = 2  # A stores a zero-effect command; R1 refuses it.
            record['final'] = snapshot(observer, r1)
            check_effect(record['final'], r1, expected_commands)
            winner = next(r for r in (a, b) if r['success'] and r['result']['amount'] == 100)
            with observer.transaction():
                observer.execute('set local role authenticated')
                observer.execute("select set_config('request.jwt.claim.sub',%s,true)", (IDS['accountant'],))
                restored = one(observer, 'select finance_command_status(%s)', (winner['request'],))
            assert restored == winner['result']
            assert snapshot(observer, r1) == record['final']
            record['status_read_matches_without_effect'] = True
            record['pass'] = True
            print('PASS ' + label, flush=True)
        finally:
            observer.execute('select pg_advisory_unlock_all()')
            pool.shutdown(wait=True, cancel_futures=True)


def main():
    files = {'bootstrap': BASE / 'bootstrap.sql', 'seed': BASE / 'seed.sql',
             'A': BASE / 'patch-a.sql', 'R1': ROOT / 'sql/proposed/admin_finance_receipts_20261102.sql'}
    report['source_sha'] = os.environ.get('GITHUB_SHA', 'local-uncommitted')
    report['inputs'] = {name: {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for name, p in files.items()}
    with connect() as control:
        report['environment'] = {'server': one(control, 'select version()'),
                                 'server_version_num': one(control, 'show server_version_num'),
                                 'driver': 'psycopg ' + psycopg.__version__,
                                 'isolation': 'read committed; separate native backend PIDs; disposable local databases',
                                 'host': '127.0.0.1', 'runner': os.environ.get('RUNNER_OS', 'local')}
        assert str(report['environment']['server_version_num']).startswith('17')
        # Never drop or reuse an unknown pre-existing database.
        assert one(control, "select count(*) from pg_database where datname like 'talabot_native_%'") == 0
        control.execute(sql.SQL('create database {}').format(sql.Identifier(PREFIX + 'a')))
        with connect(PREFIX + 'a') as c:
            for name in ['bootstrap', 'seed', 'A']:
                c.execute(files[name].read_text(), prepare=False)
            # Synthetic fixture only. Not a real account or grant operation.
            c.execute("insert into staff_members(user_id,perms,active,created_by) values(%s,array['finance'],true,%s)", (IDS['accountant'], IDS['admin']))
            c.execute("insert into orders(id,store_id,customer_id,driver_id,status,payment,cash_collected,done_at) overriding system value values(7002,%s,%s,%s,'delivered','cash',43,now())", (IDS['store'], IDS['customer'], IDS['driver']))
        create_copy(control, PREFIX + 'r1', PREFIX + 'a')
        with connect(PREFIX + 'r1') as c:
            c.execute(files['R1'].read_text(), prepare=False)
        for r1 in [False, True]:
            for same in [True, False]:
                scenario(control, r1, same)
                for stage in (['receipt', 'link'] if r1 else ['command']):
                    scenario(control, r1, same, stage)
        report['pass'] = all(s['pass'] for s in report['scenarios']) and len(report['scenarios']) == 10


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        report['failure'] = {'message': str(error), 'traceback': traceback.format_exc()}
        traceback.print_exc()
    finally:
        data = json.dumps(report, ensure_ascii=False, indent=2, default=str).encode()
        OUT.write_bytes(data + b'\n')
        # Full portable evidence in job logs; no artifact storage charges/secrets.
        print('NATIVE_RESULT_ZLIB_BASE64=' + base64.b64encode(zlib.compress(data)).decode(), flush=True)
    raise SystemExit(0 if report['pass'] else 1)
