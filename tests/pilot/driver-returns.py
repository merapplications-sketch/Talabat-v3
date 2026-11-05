"""Only new return cases. Real local GoTrue, PostgREST and PostgreSQL."""
import concurrent.futures
import datetime
import hashlib
import json
import os
import sys
import uuid

import confirmation as cf
import lab

OUT = lab.HERE / 'result-driver-returns.json'
RESULT = {'source': os.environ.get('GITHUB_SHA'), 'live': False, 'checks': []}


def ok(value, name, evidence=None):
    assert value, name
    RESULT['checks'].append({'name': name, 'evidence': evidence, 'pass': True})
    lab.save(OUT, RESULT)
    print('PASS returns ' + name, flush=True)


def args(oid, action, ref=None, amount=None, method=None, key=None):
    return dict(p_order=oid, p_request=key or str(uuid.uuid4()), p_action=action,
                p_ref=ref, p_amount=amount, p_method=method)


def act(role, oid, action, *parts):
    return lab.rpc(lab.bearer(role), 'order_return_action', args(oid, action, *parts))


def view(role, oid):
    return lab.rpc(lab.bearer(role), 'order_return_status', {'p_order': oid})


def expect_denial(role, oid, action, *parts, message=None):
    return cf.denied(lab.bearer(role), 'order_return_action', args(oid, action, *parts), message)


def pickup():
    token = lab.bearer('customer')
    oid = lab.order(token)
    offer = cf.review(oid, 15)
    if offer['needs_customer']:
        cf.confirm(token, oid, offer['revision'])
    else:
        lab.rpc(lab.bearer('merchant'), 'set_order_status', {'p_id': oid, 'p_to': 'preparing'})
    lab.rpc(lab.bearer('admin'), 'admin_assign_driver', {'p_order': oid, 'p_driver': lab.uid('driver1')})
    lab.rpc(lab.bearer('merchant'), 'set_order_status', {'p_id': oid, 'p_to': 'ready'})
    lab.rpc(lab.bearer('driver1'), 'set_order_status', {'p_id': oid, 'p_to': 'pickedup'})
    return oid


def setup():
    lab.wait(lambda: lab.request(3000, '/')[0] == 200, 'rest')
    now = datetime.datetime.now(datetime.timezone.utc)
    cfg = dict(owner_approved=True, timezone='UTC',
               valid_from=(now-datetime.timedelta(hours=1)).isoformat(),
               valid_until=(now+datetime.timedelta(hours=2)).isoformat(),
               open_minute=0, close_minute=1440, max_active=3, daily_orders=20,
               min_lat=38.55, max_lat=38.57, min_lng=68.78, max_lng=68.80,
               weekdays=list(range(1,8)), customers=[lab.uid('customer')],
               drivers=[lab.uid('driver1')], stores=[lab.STORE])
    lab.rpc(lab.bearer('admin'), 'configure_pilot_admission', {'p_config': cfg, 'p_paused': False})


def agreement():
    lab.rpc(lab.bearer('admin'), 'record_return_agreement',
            dict(p_store=lab.STORE, p_request=str(uuid.uuid4()), p_active=True, p_evidence='DEMO signed agreement'))


def cancel(oid, paid=47):
    act('driver1', oid, 'depart', f'pay-{oid}', paid)
    call = args(oid, 'cancel')
    token = lab.bearer('customer')
    first = lab.rpc(token, 'order_return_action', call)
    assert lab.rpc(token, 'order_return_action', call) == first
    return view('driver1', oid)


def test():
    setup()
    legacy = pickup()
    agreement()
    expect_denial('driver1', legacy, 'depart', 'prior-order', 42, message='return_no_agreement')
    expect_denial('customer', legacy, 'cancel', message='return_bad_state')
    lab.rpc(lab.bearer('admin'), 'set_order_status', {'p_id': legacy, 'p_to': 'cancelled'})
    ok(True, 'existing orders cannot gain a retroactive agreement or bypass departure')
    full = pickup()
    expect_denial('customer', full, 'cancel', message='return_bad_state')
    s = cancel(full)
    ok(s['open_claim'] == 47 and s['confirmed_refund'] == 0 and s['delivery_due'] == 15,
       'actual driver prepayment differs from order subtotal; platform delivery recorded once', s)
    expect_denial('customer', full, 'cancel', message='return_bad_state')
    expect_denial('driver1', full, 'receive', 'forged', message='not_allowed')
    expect_denial('merchant', full, 'report_refund', 'too-soon', 47, 'cash', message='return_waiting_receipt')
    cf.denied(lab.bearer('outsider'), 'order_return_status', {'p_order': full}, 'not_allowed')
    cf.denied(lab.bearer('accountant'), 'order_return_status', {'p_order': full}, 'not_allowed')
    assert 'open_claim' not in view('customer', full)
    ok(True, 'receipt, role isolation and customer redaction enforced')
    act('merchant', full, 'receive', 'received-full')
    assert view('driver1', full)['open_claim'] == 47
    act('merchant', full, 'report_refund', 'refund-full', 47, 'cash')
    assert view('driver1', full)['open_claim'] == 47
    expect_denial('merchant', full, 'confirm_refund', 'refund-full', 47, message='not_allowed')
    expect_denial('driver1', full, 'confirm_refund', 'refund-full', 46, message='return_bad_state')
    token = lab.bearer('driver1')
    call = args(full, 'confirm_refund', 'refund-full', 47)
    duplicate = dict(call, p_request=str(uuid.uuid4()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(lambda x: lab.request(3000, '/rpc/order_return_action', x, token),
                                  [call, call, duplicate]))
    assert sorted(code for code, _ in responses) == [200, 200, 400], responses
    assert [v for code, v in responses if code == 200][0] == [v for code, v in responses if code == 200][1]
    cf.denied(token, 'order_return_action', dict(call, p_amount=46), 'request_conflict')
    s = view('driver1', full)
    ok(s['open_claim'] == 0 and s['confirmed_refund'] == 47 and s['delivery_due'] == 15,
       'full refund closes only meal claim; concurrent replay cannot duplicate it', s)

    partial = pickup()
    cancel(partial)
    act('merchant', partial, 'receive', 'received-partial')
    expect_denial('merchant', partial, 'report_refund', 'refund-full', 20, 'transfer')
    expect_denial('merchant', partial, 'report_refund', 'over-refund', 48, 'transfer',
                  message='return_exceeds_claim')
    act('merchant', partial, 'report_refund', 'refund-partial', 20, 'transfer')
    expect_denial('merchant', partial, 'report_refund', 'refund-partial-other', 20, 'transfer')
    act('driver1', partial, 'confirm_refund', 'refund-partial', 20)
    act('merchant', partial, 'report_refund', 'disputed-partial', 10, 'cash')
    act('driver1', partial, 'dispute_refund', 'disputed-partial', 10)
    act('admin', partial, 'refuse_refund', 'support-partial-refusal')
    s = view('driver1', partial)
    ok(s['open_claim'] == 27 and s['confirmed_refund'] == 20 and s['refused_at'] and not s['pending'],
       'partial or disputed amount remains an open claim; reused references and excess denied', s)

    refused = pickup()
    cancel(refused)
    act('merchant', refused, 'receive', 'received-refused')
    refusal = args(refused, 'refuse_refund', 'restaurant-refusal')
    merchant = lab.bearer('merchant')
    first = lab.rpc(merchant, 'order_return_action', refusal)
    assert lab.rpc(merchant, 'order_return_action', refusal) == first
    expect_denial('merchant', refused, 'refuse_refund', 'restaurant-refusal-repeat', message='return_bad_state')
    s = view('driver1', refused)
    with lab.db() as db:
        counts = db.execute('select count(*), sum(amount) from return_private.delivery_due').fetchone()
        effects = db.execute(
            'select (select count(*) from wallet_entries), '
            '(select count(*) from finance_private.commands), '
            '(select count(*) from finance_private.settlement_receipts)').fetchone()
        assert lab.q(db, "select count(*) from orders where id=any(%s) and cash_collected is not null",
                     ([full, partial, refused],)) == 0
    ok(s['open_claim'] == 47 and s['confirmed_refund'] == 0 and counts == (3, 45) and effects == (0, 0, 0),
       'refusal preserves full claim; one delivery entitlement per case and no cash, wallet or settlement effects', s)
    RESULT['pass'] = True
    lab.save(OUT, RESULT)


def restore():
    def signature(name):
        with lab.db(name) as db:
            rows = {}
            for table in ('agreements', 'cases', 'refunds', 'delivery_due', 'commands'):
                value = lab.q(db, f"select jsonb_agg(j order by j::text)::text from "
                                  f"(select to_jsonb(t) j from return_private.{table} t) rows")
                assert value
                rows[table] = hashlib.sha256(value.encode()).hexdigest()
            rows['guards'] = db.execute(
                "select tgname,pg_get_triggerdef(oid),tgenabled from pg_trigger "
                "where tgname='return_order_guard'").fetchall()
            rows['rls'] = db.execute(
                "select relname,relrowsecurity from pg_class where relnamespace="
                "'return_private'::regnamespace and relkind='r' order by relname").fetchall()
            rows['functions'] = db.execute(
                "select p.oid::regprocedure::text,md5(pg_get_functiondef(p.oid)),p.proacl::text "
                "from pg_proc p where pronamespace='return_private'::regnamespace or "
                "(pronamespace='public'::regnamespace and proname in "
                "('order_return_action','order_return_status','record_return_agreement')) order by 1").fetchall()
            return rows
    original = signature('talabot_pilot')
    assert original == signature('talabot_pilot_restore')
    assert len(original['guards']) == 1 and original['guards'][0][2] == 'O'
    assert len(original['rls']) == 5 and all(enabled for _, enabled in original['rls'])
    lab.save(lab.HERE/'result-driver-returns-restore.json',
             {'pass': True, 'live': False, 'signature': original, 'dump_exported': False})
    print('PASS restore of five populated return tables, guard, permissions and RLS', flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore()
    elif len(sys.argv) > 1 and sys.argv[1] == 'ui':
        setup()
        agreement()
        lab.save(lab.HERE / '.runtime-return-ui.json', {'order': pickup()})
    else:
        test()
