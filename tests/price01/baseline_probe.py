"""PRICE-01 baseline evidence ONLY; does not implement or assert a fix.

Uses the accepted TIP02/NULL01 creator on disposable PostgreSQL 17.6 with
synthetic fixtures. Every successful assertion below is a reproduction/control,
never acceptance of checkout price protection. No hosted endpoints.
"""
import copy
import json
import os
import threading
import time
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

assert os.environ.get('PRICE01_ISOLATED') == 'yes'
assert os.environ.get('PGHOST') == '127.0.0.1'
assert os.environ.get('PGDATABASE') == 'postgres'
ns = {'__name__': 'price01_retained_fixture'}
exec(compile(Path('tests/tip02-null01/native.py').read_text(), 'retained_null01', 'exec'), ns)
Base, call, args, ENTRIES, pg = (ns[k] for k in ('NullDecision', 'call', 'args', 'ENTRIES', 'pg'))
BUYER = '10000000-0000-4000-8000-000000000092'
ITEM = '40000000-0000-4000-8000-000000000092'
OPTION = '70000000-0000-4000-8000-000000000092'
GROUP = '80000000-0000-4000-8000-000000000092'
observations = []


class PriceBaseline(Base):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.a.execute('show server_version_num').fetchone()[0], '170006')
        self.upgrade()
        self.policy(200, 200)  # retained synthetic fixture quotas, NOT production policy

    def record(self, scenario, **values):
        observations.append({'scenario': scenario, **values})

    def amount(self, oid):
        return self.a.execute('select subtotal,discount,promo_discount,total,wallet_used from orders where id=%s', (oid,)).fetchone()

    def settle_fixture_admission(self):
        # Synthetic fixture only; avoids unrelated first-cash/open/hourly limits.
        self.consent()
        self.a.execute("update orders set status='delivered',created_at=now()-interval '2 hours'")

    def test_01_changed_price_all_four_entries(self):
        for fn in ENTRIES:
            for target in (30, 10):
                self.a.execute('update menu_items set price=20')
                p = args('price01_'+str(len(observations)))
                original = copy.deepcopy(p)
                shown_total = 22  # independently: synthetic item20 + delivery2, no tip/discount
                self.a.execute('update menu_items set price=%s', (target,))
                r = self.invoke(p, fn)
                oid = r if isinstance(r, int) else r.get('id')
                self.assertIsNotNone(oid, r)
                amount = self.amount(oid)
                self.assertEqual(amount, (target, 0, 0, target+2, 5))
                self.assertNotEqual(amount[3], shown_total)
                self.assertEqual(p, original)
                self.record('base_price_changed', entry=fn, shown_total=shown_total,
                            stored_total=amount[3], wallet_spend=5,
                            protection='FAIL_BASELINE', direction='increase' if target>20 else 'decrease')
                self.settle_fixture_admission()
        self.assertEqual(self.counts(), (8, 8, -40, 8))

    def test_02_selected_option_changes(self):
        self.a.execute('insert into item_option_groups values(%s,%s,\'Synthetic option group\',1,false,0,now())', (GROUP, ITEM))
        self.a.execute('insert into item_options values(%s,%s,\'Synthetic option\',3,true,0)', (OPTION, GROUP))
        for delta in (8, 1):
            p = args('price01_option_'+str(delta)); p[1][0]['options'] = [OPTION]
            self.a.execute('update item_options set price_delta=%s', (delta,))
            r = self.invoke(p); self.assertEqual(r['status'], 'created')
            self.assertEqual(self.amount(r['id'])[3], 22+delta)
            self.assertNotEqual(self.amount(r['id'])[3], 25)
            self.record('selected_option_changed', shown_total=25, stored_total=22+delta,
                        protection='FAIL_BASELINE', direction='increase' if delta>3 else 'decrease')
            self.settle_fixture_admission()

    def test_03_store_and_dish_discount_changes(self):
        for table in ('stores', 'menu_items'):
            for discount in (25, 0):
                self.a.execute('update stores set discount_pct=0')
                self.a.execute('update menu_items set discount_pct=0')
                # Customer saw10%: 20 -2 +2 =20. Server now has25% or0%.
                self.a.execute('update '+table+' set discount_pct=%s', (discount,))
                r = self.invoke(args('price01_discount_'+table+str(discount)))
                self.assertEqual(r['status'], 'created')
                actual = self.amount(r['id'])[3]
                self.assertEqual(actual, Decimal(22)-Decimal(20)*Decimal(discount)/100)
                self.assertNotEqual(actual, 20)
                self.record('discount_changed', dependency=table, shown_total=20, stored_total=actual, protection='FAIL_BASELINE')
                self.settle_fixture_admission()

    def test_04_promo_recalculated_without_consent(self):
        self.a.execute(Path('tests/native103/dependencies.sql').read_text())
        for value in (8, 2):
            code = 'P01_'+str(value)
            self.a.execute('insert into promo_codes values(%s,true,null,null,0,null,\'fixed\',%s)', (code, value))
            self.a.execute('insert into promo_attempts values(%s,true,%s,now())', (BUYER, code))
            p = args('price01_promo_'+str(value)); p[7] = code
            r = self.invoke(p); self.assertEqual(r['status'], 'created')
            self.assertEqual(self.amount(r['id'])[2:4], (value, 22-value))
            self.assertNotEqual(self.amount(r['id'])[3], 17)  # displayed fixed promo5
            self.record('promo_changed', shown_total=17, stored_total=22-value, protection='FAIL_BASELINE')
            self.settle_fixture_admission()

    def test_05_waiting_create_observes_new_price_without_new_consent(self):
        # Independent connections, deterministic profile-lock barrier; no sleep-only race.
        p = args('price01_waiting_create')
        # Fixture owner holds the barrier; customer keeps real restricted grants.
        hold = pg.connect(dbname='candidate103', sslmode='disable')
        hold.execute('select id from profiles where id=%s for update', (BUYER,))
        contender = self.actor(); result = {}
        worker = threading.Thread(target=lambda: result.update(r=self.outcome(contender, p, 'place_order104')))
        try:
            worker.start(); blocked = False
            for _ in range(200):
                blocked = hold.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)', (contender.info.backend_pid,)).fetchone()[0]
                if blocked: break
                time.sleep(.01)
            self.assertTrue(blocked, 'creation must be waiting at profile lock')
            self.a.execute('update menu_items set price=35')
            hold.commit(); worker.join(15); self.assertFalse(worker.is_alive())
            self.assertEqual(result['r']['status'], 'created')
            self.assertEqual(self.amount(result['r']['id'])[3], 37)
            self.assertEqual(self.counts(), (1, 1, -5, 1))
            self.record('price_commits_while_create_waits', shown_total=22, stored_total=37, protection='FAIL_BASELINE')
        finally:
            hold.rollback(); hold.close(); worker.join(16); contender.close()

    def test_06_price_change_after_ack_loss_before_and_after_commit(self):
        from tcp_proxy import CutProxy
        for mode in ('before', 'after'):
            self.a.execute('update menu_items set price=20')
            p = args('price01_ack_'+mode)
            proxy = CutProxy(mode); c = self.actor(port=proxy.port)
            r = call(c, p, 'place_order104'); self.assertEqual(r['status'], 'created')
            proxy.arm = True
            with self.assertRaises((pg.OperationalError, pg.InterfaceError)): c.commit()
            c.close(); proxy.join(); self.assertTrue(proxy.cut)
            for _ in range(100):
                n = self.a.execute('select count(*) from orders where client_key=%s', (p[8],)).fetchone()[0]
                if n == (1 if mode=='after' else 0): break
                time.sleep(.01)
            self.assertEqual(n, 1 if mode=='after' else 0)
            self.a.execute('update menu_items set price=30')
            with self.actor() as check: state = check.execute('select order_request_status104(%s)', (p[8],)).fetchone()[0]
            self.assertEqual(state['status'], 'replayed' if mode=='after' else 'unresolved')
            again = self.invoke(p)
            self.assertEqual(again['status'], 'replayed' if mode=='after' else 'created')
            self.assertEqual(self.amount(again['id'])[3], 22 if mode=='after' else 32)
            self.assertEqual(self.a.execute("select count(*),sum(amount) from wallet_entries where kind='spend' and order_id=%s", (again['id'],)).fetchone(), (1, -5))
            self.record('ack_'+mode+'_commit_then_price_change', displayed_total=22,
                        saved_total=self.amount(again['id'])[3], one_debit=True,
                        protection='HISTORY_CONTROL_PASS' if mode=='after' else 'FAIL_BASELINE')
            self.settle_fixture_admission()

    def test_07_concurrent_retries_replay_original_without_repricing(self):
        p = args('price01_same_key')
        first = self.invoke(p); self.assertEqual(first['status'], 'created')
        self.a.execute('update menu_items set price=40')
        barrier = threading.Barrier(3); results = []; errors = []
        def run():
            try:
                barrier.wait(5)
                results.append(self.invoke(p))
            except Exception as exc: errors.append(type(exc).__name__)
        threads = [threading.Thread(target=run) for _ in range(3)]
        for t in threads: t.start()
        for t in threads: t.join(15); self.assertFalse(t.is_alive())
        self.assertFalse(errors); self.assertEqual(len(results), 3)
        self.assertTrue(all(r['status']=='replayed' and r['id']==first['id'] for r in results))
        self.assertEqual(self.amount(first['id'])[3], 22)
        self.assertEqual(self.counts(), (1, 1, -5, 1))
        self.record('concurrent_replay_after_price_change', saved_total=22, one_order=True, one_debit=True, protection='HISTORY_CONTROL_PASS')

    def test_08_adding_consent_to_saved_payload_changes_v1_fingerprint(self):
        p = args('price01_payload_contract')
        r = self.invoke(p); self.assertEqual(r['status'], 'created')
        before = self.snapshot(); changed = copy.deepcopy(p)
        changed[12] = {'price01': {'version': 1, 'total': '22'}}  # proposed name; not an implemented contract
        reply = self.invoke(changed); self.assertEqual(reply['status'], 'conflict')
        self.assertEqual(reply['reason'], 'idempotency_mismatch'); self.assertEqual(self.snapshot(), before)
        self.record('do_not_append_consent_to_saved_request', protection='HMAC_CONTROL_PASS', outcome='conflict', no_mutation=True)


if __name__ == '__main__':
    names = sorted(n for n in PriceBaseline.__dict__ if n.startswith('test_'))
    if os.environ.get('PRICE01_CASES'):
        selected = os.environ['PRICE01_CASES'].split(',')
        assert set(selected).issubset(names)
        names = selected
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(PriceBaseline(n) for n in names))
    output = {'scope': 'LOCAL PostgreSQL17.6, synthetic schema; BASELINE ONLY; not HTTP/Supabase',
              'source': 'd76269c9f3e5c02fe0be379ac8ba6356e624f9b8',
              'qa_ref': '3c13f5ff9a36638f2e421e17389d1666bae4487b',
              'utc': datetime.now(timezone.utc).isoformat(), 'groups': result.testsRun,
              'reproduction_and_control_assertions_passed': result.wasSuccessful(),
              'price01_fix_implemented': False,
              'errors': [t.id() for t,_ in result.failures+result.errors], 'observations': observations}
    Path(os.environ.get('PRICE01_RESULT', 'price01-baseline.json')).write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str)+'\n')
    raise SystemExit(not result.wasSuccessful())
