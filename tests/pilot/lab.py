"""Free disposable native Auth/PostgREST journey lab; never accepts a live host.

Production SQL is restored from the previously saved catalogue. Only the stub
auth.users header is omitted: real GoTrue migrations supply that schema. Public
SQL/function bodies are unchanged, followed by exact A/R1. Runtime tokens and
logical backup stay ephemeral and are never exported as evidence.
"""
import base64, concurrent.futures, hashlib, hmac, http.client, json, os, pathlib
import secrets, statistics, subprocess, sys, threading, time, traceback, uuid, zlib
import urllib.request, urllib.error
import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / 'tests/pilot'
STATE = HERE / '.runtime.json'
STORE = 'a0000000-0000-4000-8000-000000000005'
ITEM = 'a0000000-0000-4000-8000-000000000006'
LAT, LNG = 38.5598, 68.787


def save(path, value):
    pathlib.Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def state():
    return json.loads(STATE.read_text())


def db(name='talabot_pilot'):
    assert name in ('talabot_pilot', 'talabot_pilot_restore')
    return psycopg.connect(host='127.0.0.1', port=5432, dbname=name, user='postgres',
                          password=state()['password'], autocommit=True, connect_timeout=5)


def q(c, text, params=None):
    return c.execute(text, params).fetchone()[0]


def wait(fn, label, seconds=75):
    end = time.monotonic() + seconds
    last = None
    while time.monotonic() < end:
        try:
            value = fn()
            if value:
                return value
        except Exception as e:
            last = type(e).__name__
        time.sleep(.5)
    raise RuntimeError('wait_timeout:' + label + ':' + str(last))


def request(port, path, data=None, token=None, method=None):
    assert port in (3000, 9999)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request('http://127.0.0.1:' + str(port) + path,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            result = json.loads(raw)
        except Exception:
            result = {'message': raw.decode(errors='replace')[:160]}
        return e.code, result


def rpc(token, fn, args=None, expect=200):
    code, value = request(3000, '/rpc/' + fn, args or {}, token)
    if code != expect and not (expect == 200 and code == 204):
        # No tokens/passwords in error messages or results.
        raise AssertionError(fn + ': HTTP ' + str(code) + ' ' + str(value)[:350])
    return value


def bearer(name):
    return state()['accounts'][name]['access_token']


def uid(name):
    return state()['accounts'][name]['id']


def jwt(role):
    s = state()
    enc = lambda obj: base64.urlsafe_b64encode(json.dumps(obj, separators=(',', ':')).encode()).decode().rstrip('=')
    head = enc({'alg': 'HS256', 'typ': 'JWT'})
    body = enc({'role': role, 'iss': 'supabase', 'aud': 'authenticated', 'iat': int(time.time()), 'exp': int(time.time()) + 7200})
    sig = base64.urlsafe_b64encode(hmac.new(s['jwt'].encode(), (head + '.' + body).encode(), hashlib.sha256).digest()).decode().rstrip('=')
    return head + '.' + body + '.' + sig


def register(name, number, admin=False):
    password = 'Synthetic-only-' + secrets.token_hex(12)
    email = name + '@synthetic.invalid'
    data = {'email': email, 'password': password, 'data': {'name': 'DEMO ' + name, 'phone': '+9929' + str(number).zfill(8), 'role': 'admin'}}
    if admin:
        code, value = request(9999, '/admin/users', {'email': email, 'password': password, 'email_confirm': True, 'user_metadata': data['data']}, jwt('service_role'))
        assert code in (200, 201), ('create_synthetic_user', code, str(value)[:100])
    else:
        code, value = request(9999, '/signup', data)
        assert code in (200, 201), ('signup', code, str(value)[:100])
    code, session = request(9999, '/token?grant_type=password', {'email': email, 'password': password})
    assert code == 200 and session.get('access_token'), ('password_signin', code)
    return {'id': session['user']['id'], 'email': email, 'password': password,
            'access_token': session['access_token'], 'refresh_token': session['refresh_token']}


def prepare_env():
    assert not STATE.exists(), 'Do not overwrite an unresolved runtime'
    s = {'password': secrets.token_hex(24), 'jwt': secrets.token_hex(32), 'accounts': {}}
    save(STATE, s)
    os.chmod(STATE, 0o600)
    (HERE / '.runtime.env').write_text('LAB_PASSWORD=' + s['password'] + '\nLAB_JWT_SECRET=' + s['jwt'] + '\n')
    os.chmod(HERE / '.runtime.env', 0o600)


def prepare_db():
    def alive():
        with db() as c:
            return q(c, 'select 1')
    wait(alive, 'native_db')
    with db() as c:
        c.execute('create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;create extension pg_stat_statements')
        c.execute("create role authenticator login noinherit password '" + state()['password'] + "'")
        c.execute('grant anon,authenticated,service_role to authenticator')


def prepare_app():
    wait(lambda: request(9999, '/health')[0] == 200, 'gotrue')
    source = (ROOT / 'tests/base-lab/web/bootstrap.sql').read_text()
    source = source[source.index('CREATE OR REPLACE FUNCTION auth.uid()'):]
    with db() as c:
        c.execute(source, prepare=False)
        c.execute('create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user()')
        c.execute((ROOT / 'tests/base-lab/web/patch-a.sql').read_text(), prepare=False)
        c.execute((ROOT / 'sql/proposed/admin_finance_receipts_20261102.sql').read_text(), prepare=False)
        for patch in sorted((ROOT / 'sql/proposed').glob('pilot_*.sql')):
            c.execute(patch.read_text(), prepare=False)
    s = state()
    for i, name in enumerate(['admin', 'accountant', 'merchant', 'customer', 'outsider', 'driver1', 'driver2', 'joiner'], 1):
        s['accounts'][name] = register(name, i)
        save(STATE, s)
    with db() as c:
        # Explicit synthetic fixture provisioning; never sent to hosted Supabase.
        s['untrusted_metadata_role'] = q(c, 'select role::text from profiles where id=%s', (uid('customer'),))
        c.execute("update profiles set role='admin' where id=%s", (uid('admin'),))
        c.execute("update profiles set role='merchant' where id=%s", (uid('merchant'),))
        c.execute("update profiles set role='driver',driver_status='approved' where id in (%s,%s)", (uid('driver1'), uid('driver2')))
        c.execute("insert into staff_members(user_id,perms,active,created_by) values(%s,array['finance'],true,%s)", (uid('accountant'), uid('admin')))
        c.execute("insert into stores(id,owner_id,name,category,lat,lng,commission_pct,fee_base) values(%s,%s,'DEMO pilot','rest',%s,%s,20,15)", (STORE, uid('merchant'), LAT, LNG))
        c.execute("insert into menu_items(id,store_id,name,price) values(%s,%s,'DEMO dish',25)", (ITEM, STORE))
    save(STATE, s)


def order(token, key=None, wallet=None, qty=2):
    return rpc(token, 'place_order', {'p_store': STORE, 'p_items': [{'item_id': ITEM, 'qty': qty, 'options': []}],
                                    'p_payment': 'cash', 'p_address': 'DEMO Rudaki 1', 'p_lat': LAT, 'p_lng': LNG,
                                    'p_key': key or 'pilot_' + uuid.uuid4().hex, 'p_fee': 15, 'p_wallet': wallet})


def journey(customer='customer', key=None, race=False):
    t = bearer(customer)
    oid = order(t, key)
    m = bearer('merchant')
    rpc(m, 'set_prep_time', {'p_id': oid, 'p_min': 12})
    rpc(m, 'set_order_status', {'p_id': oid, 'p_to': 'preparing'})
    if race:
        with db() as c:
            for n in ['driver1', 'driver2']:
                c.execute("insert into order_offers(order_id,driver_id,mode,expires_at) values(%s,%s,'broadcast',now()+interval '10 minutes') on conflict(order_id,driver_id) do update set state='pending',expires_at=excluded.expires_at", (oid, uid(n)))
        gate = threading.Barrier(2)
        def accept(name):
            gate.wait()
            return name, request(3000, '/rpc/driver_accept', {'p_id': oid}, bearer(name))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            responses = list(ex.map(accept, ['driver1', 'driver2']))
        winners = [n for n, (code, v) in responses if code == 200 and v is True]
        assert len(winners) == 1, ('driver_race', responses)
        driver = winners[0]
    else:
        driver = 'driver1'
        rpc(bearer('admin'), 'admin_assign_driver', {'p_order': oid, 'p_driver': uid(driver)})
        responses = None
    rpc(m, 'set_order_status', {'p_id': oid, 'p_to': 'ready'})
    d = bearer(driver)
    rpc(d, 'set_order_status', {'p_id': oid, 'p_to': 'pickedup'})
    rpc(d, 'driver_ping', {'p_online': True})
    rpc(d, 'driver_location', {'p_lat': LAT, 'p_lng': LNG, 'p_acc': 11})
    pos = rpc(t, 'order_courier_position', {'p_order': oid})
    assert pos and pos[0]['acc'] == 11
    rpc(d, 'deliver_order', {'p_id': oid, 'p_cash': 65, 'p_note': None, 'p_photo': None})
    with db() as c:
        row = c.execute('select subtotal,total,commission,driver_payout,cash_collected,status,prep_time from orders where id=%s', (oid,)).fetchone()
        assert row == (50, 65, 10, 15, 65, 'delivered', 12), row
    return {'order': oid, 'driver': driver, 'race': responses, 'totals': [float(x) if hasattr(x, 'as_tuple') else x for x in row]}


def integration():
    wait(lambda: request(3000, '/')[0] == 200, 'postgrest')
    result = {'source': os.environ.get('GITHUB_SHA'), 'engine': 'native PostgreSQL + real GoTrue and PostgREST; synthetic only',
              'old_53_or_ten_concurrency_rerun': False, 'checks': [], 'live': False, 'open': ['actual hardware Safari/Android', 'native printer', 'real SMTP/SMS', 'Realtime websocket service', 'hosted deployment configuration']}
    skip = set(filter(None, os.environ.get('PILOT_SKIP', '').split(',')))
    def case(name, fn):
        if name in skip:
            result['checks'].append({'name': name, 'status': 'previously_passed_not_rerun'})
            return
        try:
            evidence = fn()
            result['checks'].append({'name': name, 'pass': True, 'evidence': evidence})
            print('PASS ' + name, flush=True)
        except Exception as e:
            result['checks'].append({'name': name, 'pass': False, 'error': str(e), 'traceback': traceback.format_exc()})
            print('FAIL ' + name + ': ' + str(e), flush=True)
        save(HERE / 'result-integration.json', result)

    def authentication():
        assert state()['untrusted_metadata_role'] == 'customer'
        s = state()['accounts']['customer']
        code, refreshed = request(9999, '/token?grant_type=refresh_token', {'refresh_token': s['refresh_token']})
        assert code == 200 and refreshed.get('access_token')
        assert request(9999, '/token?grant_type=password', {'email': s['email'], 'password': 'wrong-synthetic-password'})[0] == 400
        assert request(3000, '/profiles?select=id', token=bearer('customer')[:-5] + 'wrong')[0] == 401
        return {'real_signup_password_refresh': True, 'untrusted_metadata_admin_ignored': True, 'forged_JWT_rejected': True, 'SMTP_tested': False}
    case('auth_signup_login_refresh_and_forgery', authentication)

    def onboarding():
        rpc(bearer('joiner'), 'apply_as_driver')
        with db() as c:
            assert c.execute('select role::text,driver_status from profiles where id=%s', (uid('joiner'),)).fetchone() == ('driver', 'pending')
        code, err = request(3000, '/rpc/driver_accept', {'p_id': 999999}, bearer('joiner'))
        assert code >= 400 and err['message'] == 'not_approved'
        return {'current_flow': 'email/password customer identity -> apply_as_driver -> same UUID driver pending -> admin approval', 'pending_cannot_accept': True}
    case('current_driver_joining_gate', onboarding)

    def address_privacy():
        code, _ = request(3000, '/addresses', {'user_id': uid('customer'), 'label': 'home', 'street': 'DEMO Rudaki 1', 'lat': LAT, 'lng': LNG}, bearer('customer'))
        assert code in (200, 201)
        assert request(3000, '/addresses?select=*&user_id=eq.' + uid('customer'), token=bearer('outsider')) == (200, [])
        code, _ = request(3000, '/addresses', {'user_id': uid('outsider'), 'label': 'home', 'street': 'DEMO', 'lat': LAT, 'lng': LNG}, bearer('customer'))
        assert code >= 400
        return {'own_write': True, 'cross_identity_read_write_denied': True}
    case('address_RLS', address_privacy)

    def catalog():
        assert request(3000, '/stores?select=id,name,is_open', token=bearer('customer'))[0] == 200
        assert request(3000, '/menu_items?select=id,price&store_id=eq.' + STORE, token=bearer('customer'))[1][0]['price'] == 25
        with db() as c:
            c.execute('update menu_items set available=false where id=%s', (ITEM,))
        try:
            code, err = request(3000, '/rpc/place_order', {'p_store': STORE, 'p_items': [{'item_id': ITEM, 'qty': 1, 'price': .01}], 'p_address': 'DEMO', 'p_lat': LAT, 'p_lng': LNG, 'p_payment': 'cash', 'p_key': 'unavailable_check'}, bearer('customer'))
            assert code >= 400 and err['message'] == 'unavailable'
        finally:
            with db() as c:
                c.execute('update menu_items set available=true where id=%s', (ITEM,))
        rpc(bearer('merchant'), 'set_store_open', {'p_store': STORE, 'p_open': False})
        try:
            code, err = request(3000, '/rpc/place_order', {'p_store': STORE, 'p_items': [{'item_id': ITEM, 'qty': 1}], 'p_address': 'DEMO', 'p_lat': LAT, 'p_lng': LNG, 'p_payment': 'cash', 'p_key': 'closed_store_check'}, bearer('customer'))
            assert code >= 400 and err['message'] == 'closed'
        finally:
            rpc(bearer('merchant'), 'set_store_open', {'p_store': STORE, 'p_open': True})
        with db() as c:
            assert q(c, "select count(*) from orders where client_key in ('unavailable_check','closed_store_check')") == 0
        return {'availability_and_open_checked_by_server': True, 'failed_order_has_no_partial_rows': True}
    case('catalog_prices_availability_and_atomic_refusal', catalog)

    def unsupported_payment():
        observations = []
        for method in ['card', 'apple', 'wallet']:
            payload = {'p_store': STORE, 'p_items': [{'item_id': ITEM, 'qty': 1}], 'p_address': 'DEMO payment', 'p_lat': LAT, 'p_lng': LNG, 'p_payment': method, 'p_key': 'unsupported_' + method}
            code, value = request(3000, '/rpc/place_order', payload, bearer('outsider'))
            row = {'method': method, 'status': code, 'result': value}
            if code == 200:
                with db() as c:
                    row['stored'] = c.execute('select payment,wallet_used,total from orders where id=%s', (value,)).fetchone()
                rpc(bearer('outsider'), 'set_order_status', {'p_id': value, 'p_to': 'cancelled'})
            observations.append(row)
        save(HERE / 'result-payment-guard.json', {'observations': observations, 'live': False})
        assert all(o['status'] >= 400 and o['result'].get('message') == 'payment_not_configured' for o in observations), 'unsupported payments accepted without debit: ' + json.dumps(observations, default=str)
        with db() as c:
            old = q(c, "insert into orders(store_id,customer_id,payment,client_key,status,total) values(%s,%s,'card','legacy_payment_key','cancelled',40) returning id", (STORE, uid('outsider')))
        code, recovered = request(3000, '/rpc/place_order', {'p_store': STORE, 'p_items': [], 'p_key': 'legacy_payment_key', 'p_payment': 'card'}, bearer('outsider'))
        assert code == 200 and recovered == old
        return observations
    case('unsupported_payment_refusal', unsupported_payment)

    def main_journey():
        value = journey(race=True)
        oid = value['order']
        key = str(uuid.uuid4())
        # Receive headers (SQL COMMIT completed), drop the response body, then
        # recover through a separate authenticated status request over REST.
        cn = http.client.HTTPConnection('127.0.0.1', 3000, timeout=20)
        payload = {'p_request': key, 'p_operation': 'settle_cash', 'p_target': uid(value['driver']), 'p_amount': None, 'p_note': None}
        cn.request('POST', '/rpc/finance_execute', json.dumps(payload), {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + bearer('accountant')})
        response = cn.getresponse()
        assert response.status == 200, ('finance_execute_headers', response.status, response.read().decode()[:250])
        cn.close()  # body intentionally never decoded by submitting client
        stored = rpc(bearer('accountant'), 'finance_command_status', {'p_request': key})
        assert stored['receipt']['request'] == key and stored['amount'] == 65
        assert stored['receipt']['orders'] == [{'id': str(oid), 'amount': 65}]
        receipts = rpc(bearer(value['driver']), 'finance_settlement_receipts', {'p_order_ids': [str(oid)]})
        assert receipts[0]['receipt'] == stored['receipt']
        assert rpc(bearer('outsider'), 'finance_settlement_receipts', {'p_order_ids': [str(oid)]}) == []
        with db() as c:
            assert q(c, 'select count(*) from finance_private.commands where request=%s', (key,)) == 1
            assert q(c, 'select count(*) from finance_private.settlement_receipts where request=%s', (key,)) == 1
        code, err = request(3000, '/rpc/deliver_order', {'p_id': oid, 'p_cash': 65}, bearer(value['driver']))
        assert code >= 400 and err['message'] == 'bad_transition'
        value['stored_receipt'] = stored['receipt']
        value['lost_response_body_status_read_only'] = True
        return value
    case('real_REST_order_to_receipt_and_lost_body', main_journey)

    def order_idempotency():
        k = 'pilot_retry_' + uuid.uuid4().hex
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            ids = list(ex.map(lambda _: order(bearer('customer'), k), range(2)))
        assert ids[0] == ids[1]
        # A new session/connection and browser restart retain the same request key.
        assert order(bearer('customer'), k) == ids[0]
        rpc(bearer('customer'), 'set_order_status', {'p_id': ids[0], 'p_to': 'cancelled'})
        return {'key': k, 'order': ids[0], 'concurrent_and_after_reconnect': True}
    case('order_creation_retry_and_reconnect', order_idempotency)

    def role_privacy():
        t = bearer('outsider')
        assert request(3000, '/orders?select=id&customer_id=eq.' + uid('customer'), token=t) == (200, [])
        assert request(3000, '/profiles?select=id&role=eq.driver', token=t) == (200, [])
        assert request(3000, '/wallet_entries?select=id&user_id=eq.' + uid('customer'), token=t) == (200, [])
        code, err = request(3000, '/rpc/finance_execute', {'p_request': str(uuid.uuid4()), 'p_operation': 'settle_cash', 'p_target': uid('driver1')}, t)
        assert code >= 400 and err['message'] == 'not_allowed'
        anonymous = request(3000, '/orders?select=id', token=None)
        assert anonymous == (200, []) or anonymous[0] in (401, 403)
        with db() as c:
            row = c.execute('select id from orders where customer_id=%s limit 1', (uid('customer'),)).fetchone()
        assert request(3000, '/order_items?select=*&order_id=eq.' + str(row[0]), token=t) == (200, [])
        code, err = request(3000, '/rpc/set_order_status', {'p_id': row[0], 'p_to': 'delivered'}, t)
        assert code >= 400
        return {'anonymous_and_cross_customer_rows_hidden': True, 'ungranted_command_and_transition_denied': True}
    case('REST_role_and_order_privacy', role_privacy)

    def cancellation():
        with db() as c:
            c.execute("insert into wallet_entries(user_id,amount,kind,note) values(%s,20,'adjust','synthetic fixture')", (uid('customer'),))
        before = rpc(bearer('customer'), 'wallet_balance')
        oid = order(bearer('customer'), wallet=20)
        rpc(bearer('customer'), 'set_order_status', {'p_id': oid, 'p_to': 'cancelled'})
        assert rpc(bearer('customer'), 'wallet_balance') == before
        code, _ = request(3000, '/rpc/set_order_status', {'p_id': oid, 'p_to': 'cancelled'}, bearer('customer'))
        assert code >= 400 and rpc(bearer('customer'), 'wallet_balance') == before
        oid2 = order(bearer('customer'))
        rpc(bearer('merchant'), 'reject_order', {'p_id': oid2, 'p_reason': 'out_of_stock', 'p_note': None})
        with db() as c:
            assert q(c, 'select cancel_reason from orders where id=%s', (oid2,)) == 'out_of_stock'
        return {'pending_cancel_wallet_return_once': True, 'merchant_rejection_reason_persisted': True, 'driver_advance_compensation_policy': 'open_not_invented'}
    case('cancel_reject_wallet_recovery', cancellation)

    def client_monitor():
        rpc(bearer('customer'), 'report_client_error', {'p_app': 'customer', 'p_message': 'SYNTHETIC outage probe', 'p_context': 'pilot', 'p_ua': 'lab'})
        assert request(3000, '/client_errors?select=message', token=bearer('outsider')) == (200, [])
        assert request(3000, '/client_errors?select=message', token=bearer('admin'))[1]
        return {'error_log_persists_and_is_private': True, 'external_uptime_alert_receiver_configured': False}
    case('client_error_monitoring_store', client_monitor)

    def refund_race():
        # Distinct closed tickets on one delivered order: there is no duplicate
        # ticket uniqueness conflict to conceal a cross-ticket refund cap race.
        oid = order(bearer('outsider'))
        with db() as c:
            c.execute("update orders set status='delivered',done_at=now() where id=%s", (oid,))
            tickets = [q(c, "insert into support_tickets(customer_id,order_id,reason,status) values(%s,%s,'missing_items','resolved') returning id", (uid('outsider'), oid)) for _ in range(2)]
            c.execute("create function public.pilot_refund_barrier() returns trigger language plpgsql as $$begin if new.kind='refund' then perform pg_advisory_xact_lock(517551);end if;return new;end$$;create trigger pilot_refund_barrier before insert on wallet_entries for each row execute function public.pilot_refund_barrier()")
            c.execute('select pg_advisory_lock(517551)')
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            futures = [pool.submit(request, 3000, '/rpc/ticket_set_status', {'p_ticket': ticket, 'p_status': 'resolved', 'p_note': 'synthetic cap race', 'p_refund': 40}, bearer('admin')) for ticket in tickets]
            # With missing order lock both transactions reach the insert gate;
            # with the fix one waits on the order, while one waits at this gate.
            try:
                wait(lambda: q(c, "select count(*) from pg_stat_activity where datname=current_database() and wait_event_type='Lock' and query like 'WITH pgrst_source%%'") >= 2, 'two_refund_requests_waiting', 15)
                locks = c.execute("select pid,wait_event_type,wait_event,pg_blocking_pids(pid) from pg_stat_activity where datname=current_database() and wait_event_type='Lock'").fetchall()
            finally:
                c.execute('select pg_advisory_unlock(517551)')
            responses = [f.result(timeout=20) for f in futures]
            pool.shutdown()
            total = q(c, "select coalesce(sum(amount),0) from wallet_entries where order_id=%s and kind='refund'", (oid,))
            c.execute('drop trigger pilot_refund_barrier on wallet_entries;drop function public.pilot_refund_barrier()')
            evidence = {'order_total': 65, 'refund_requested_each': 40, 'responses': responses, 'refund_total': total, 'locks': locks}
            save(HERE / 'result-refund-race.json', evidence)
            assert total <= 65, json.dumps(evidence, default=str)
            assert total == 40 and sum(code in (200,204) for code, _ in responses) == 1
            assert any(code >= 400 and value.get('message') == 'refund_too_high' for code,value in responses)
            # Same ticket retry is also forbidden by the preserved existing rule.
            winner = tickets[next(i for i,(code,_) in enumerate(responses) if code in (200,204))]
            code,value = request(3000, '/rpc/ticket_set_status', {'p_ticket':winner,'p_status':'resolved','p_note':'synthetic retry','p_refund':40}, bearer('admin'))
            assert code >= 400 and value['message'] == 'already_refunded'
        return evidence
    case('cross_ticket_refund_cap_under_contention', refund_race)

    def refund_failure():
        oid = order(bearer('outsider'))
        with db() as c:
            c.execute("update orders set status='delivered',done_at=now() where id=%s", (oid,))
            ticket = q(c,"insert into support_tickets(customer_id,order_id,reason) values(%s,%s,'missing_items') returning id",(uid('outsider'),oid))
            c.execute("create function public.pilot_refund_fail() returns trigger language plpgsql as $$begin if new.kind='refund' then raise exception 'synthetic_refund_store_failure';end if;return new;end$$;create trigger pilot_refund_fail before insert on wallet_entries for each row execute function public.pilot_refund_fail()")
            try:
                code,value=request(3000,'/rpc/ticket_set_status',{'p_ticket':ticket,'p_status':'resolved','p_note':'synthetic storage failure','p_refund':10},bearer('admin'))
                assert code >= 400 and value['message']=='synthetic_refund_store_failure'
                assert c.execute('select status,refund_amount from support_tickets where id=%s',(ticket,)).fetchone()==('open',None)
                assert q(c,'select count(*) from wallet_entries where ticket_id=%s',(ticket,))==0
                assert q(c,"select count(*) from audit_log where table_name='support_tickets' and row_id=%s",(str(ticket),))==0
            finally:
                c.execute('drop trigger pilot_refund_fail on wallet_entries;drop function public.pilot_refund_fail()')
        return {'ticket_close_and_refund_rolled_back_together':True}
    case('refund_storage_failure_atomicity',refund_failure)

    def expanded_privacy():
        s=state();s['accounts']['merchant2']=register('merchant2',900,admin=True);save(STATE,s)
        second_store='a0000000-0000-4000-8000-000000000007'
        with db()as c:
            c.execute("update profiles set role='merchant' where id=%s",(uid('merchant2'),))
            c.execute("insert into stores(id,owner_id,name,category) values(%s,%s,'DEMO second merchant','rest')",(second_store,uid('merchant2')))
        oid=order(bearer('customer'))
        checks=[]
        def hidden(actor,resource):
            code,value=request(3000,resource,token=bearer(actor));assert (code==200 and value==[])or code in (401,403);checks.append({'actor':actor,'resource':resource,'status':code,'hidden':True})
        for actor in ['outsider','merchant2','driver2']:
            hidden(actor,'/orders?select=id,address& id=eq.'.replace(' ','')+str(oid))
            hidden(actor,'/order_items?select=*&order_id=eq.'+str(oid))
        for actor in ['merchant','merchant2','driver2']:
            hidden(actor,'/addresses?select=*&user_id=eq.'+uid('customer'))
        hidden('customer','/stores?select=owner_id,commission_pct')
        code,value=request(3000,'/profiles?id=eq.'+uid('driver2'),{'driver_status':'blocked','role':'admin'},bearer('driver2'),method='PATCH')
        assert code>=400 and value['message']=='not_allowed';checks.append({'driver_role_self_escalation_denied':True})
        code,value=request(3000,'/rpc/finance_execute',{'p_request':str(uuid.uuid4()),'p_operation':'settle_cash','p_target':uid('driver2')},bearer('admin'))
        assert code>=400 and value['message']=='not_allowed';checks.append({'admin_without_finance_grant_denied_through_real_REST':True})
        code,value=request(3000,'/orders?id=eq.'+str(oid),{'status':'delivered'},bearer('customer'),method='PATCH')
        assert code>=400;checks.append({'direct_order_write_denied':True})
        rpc(bearer('customer'),'set_order_status',{'p_id':oid,'p_to':'cancelled'})
        return checks
    case('merchant_driver_and_direct_write_isolation',expanded_privacy)

    def one_driver_race():
        orders=[order(bearer('customer')),order(bearer('outsider'))]
        for oid in orders:rpc(bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'})
        with db()as c:
            for oid in orders:c.execute("insert into order_offers(order_id,driver_id,mode,expires_at) values(%s,%s,'broadcast',now()+interval '10 minutes') on conflict(order_id,driver_id) do update set state='pending',expires_at=excluded.expires_at",(oid,uid('driver2')))
            c.execute('begin');c.execute('select id from orders where id=any(%s) order by id for update',(orders,))
            pool=concurrent.futures.ThreadPoolExecutor(max_workers=2)
            futures=[pool.submit(request,3000,'/rpc/driver_accept',{'p_id':oid},bearer('driver2'))for oid in orders]
            try:
                # Independent autocommit observer avoids PostgreSQL's transaction-cached activity snapshot.
                with db() as observer:
                    wait(lambda:q(observer,"select count(*) from pg_stat_activity where datname=current_database() and wait_event_type='Lock' and query like 'WITH pgrst_source%%'")>=2,'same_driver_two_accepts',15)
                locks=c.execute("select pid,wait_event_type,wait_event,pg_blocking_pids(pid) from pg_stat_activity where datname=current_database() and wait_event_type='Lock'").fetchall()
            finally:c.execute('commit')
            replies=[f.result(timeout=20)for f in futures];pool.shutdown()
            assigned=q(c,'select count(*) from orders where id=any(%s) and driver_id=%s',(orders,uid('driver2')))
            evidence={'orders':orders,'assigned_to_same_driver':assigned,'responses':replies,'locks':locks};save(HERE/'result-driver-race.json',evidence)
            assert assigned==1,json.dumps(evidence,default=str)
        for oid in orders:rpc(bearer('admin'),'set_order_status',{'p_id':oid,'p_to':'cancelled'})
        return evidence
    case('one_driver_cannot_accept_two_active_orders',one_driver_race)
    def two_driver_claim():
        oid=order(bearer('customer'))
        rpc(bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'})
        with db() as c:
            for name in ['driver1','driver2']:
                c.execute("insert into order_offers(order_id,driver_id,mode,expires_at) values(%s,%s,'broadcast',now()+interval '10 minutes') on conflict(order_id,driver_id) do update set state='pending',expires_at=excluded.expires_at",(oid,uid(name)))
        barrier=threading.Barrier(2)
        def accept(name):
            barrier.wait()
            return name,request(3000,'/rpc/driver_accept',{'p_id':oid},bearer(name))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:replies=list(pool.map(accept,['driver1','driver2']))
        winners=[name for name,(code,value)in replies if code==200 and value is True]
        assert len(winners)==1,replies
        with db() as c:
            assert str(q(c,'select driver_id from orders where id=%s',(oid,)))==uid(winners[0])
            assert q(c,"select count(*) from order_offers where order_id=%s and state='accepted'",(oid,))==1
        rpc(bearer('admin'),'set_order_status',{'p_id':oid,'p_to':'cancelled'})
        return {'order':oid,'responses':replies,'one_assigned_driver_and_accepted_offer':True}
    case('driver_claim_two_drivers_one_order_after_profile_lock',two_driver_claim)
    result['pass'] = all(x.get('pass', x.get('status') == 'previously_passed_not_rerun') for x in result['checks'])
    save(HERE / 'result-integration.json', result)
    if not result['pass']:
        raise SystemExit(1)


def load():
    stages = [int(n) for n in os.environ.get('PILOT_LOAD_STAGES', '10,25,50').split(',')]
    total_journeys = sum(stages)
    assert stages in ([10,25,50], [50])
    result = {'source': os.environ.get('GITHUB_SHA'), 'live': False, 'engine': 'native PostgreSQL17.6 + GoTrue2.197 + PostgREST14.18 / GitHub Linux VM',
              'scope': str(total_journeys) + ' single-order journeys; concurrency ' + str(stages) + '; no real WAN, Realtime or device', 'stages': []}
    metrics, metric_lock = [], threading.Lock()
    s = state()
    for i in range(total_journeys):
        for kind in ['loadc', 'loadd']:
            name = kind + str(i)
            s['accounts'][name] = register(name, 100 + i + (1000 if kind == 'loadd' else 0), admin=True)
        save(STATE, s)
    with db() as c:
        c.execute("update profiles set role='driver',driver_status='approved',online=false where id=any(%s::uuid[])", ([uid('loadd' + str(i)) for i in range(total_journeys)],))
        # A realistic retained catalogue/history size, isolated only. Historical
        # orders are >48h old and settled; they never enter this lab's finance.
        c.execute("insert into orders(store_id,customer_id,status,payment,subtotal,total,created_at,done_at,cash_collected,cash_settled_at) select %s,%s,'delivered','cash',25,40,now()-interval '3 days',now()-interval '3 days',0,now()-interval '3 days' from generate_series(1,10000)", (STORE, uid('outsider')))
        c.execute('analyze;select pg_stat_statements_reset()')
    def measured(token, fn, args):
        t = time.perf_counter()
        code, value = request(3000, '/rpc/' + fn, args, token)
        with metric_lock:
            metrics.append({'fn': fn, 'ms': (time.perf_counter() - t) * 1000, 'status': code})
        if code not in (200, 204):
            raise AssertionError(fn + ' ' + str(code) + ' ' + str(value)[:120])
        return value
    def trip(i):
        customer, driver = bearer('loadc' + str(i)), bearer('loadd' + str(i))
        measured(customer, 'delivery_quote', {'p_store': STORE, 'p_lat': LAT, 'p_lng': LNG})
        oid = measured(customer, 'place_order', {'p_store': STORE, 'p_items': [{'item_id': ITEM, 'qty': 2}], 'p_address': 'DEMO load', 'p_lat': LAT, 'p_lng': LNG, 'p_payment': 'cash', 'p_key': 'load_order_' + str(i), 'p_fee': 15})
        measured(bearer('merchant'), 'set_prep_time', {'p_id': oid, 'p_min': 10})
        measured(bearer('merchant'), 'set_order_status', {'p_id': oid, 'p_to': 'preparing'})
        measured(bearer('admin'), 'admin_assign_driver', {'p_order': oid, 'p_driver': uid('loadd' + str(i))})
        measured(bearer('merchant'), 'set_order_status', {'p_id': oid, 'p_to': 'ready'})
        measured(driver, 'set_order_status', {'p_id': oid, 'p_to': 'pickedup'})
        measured(driver, 'driver_ping', {'p_online': True})
        for n in range(3):
            if n:
                time.sleep(3.05)
            measured(driver, 'driver_location', {'p_lat': LAT + n * .0001, 'p_lng': LNG, 'p_acc': 12})
            position = measured(customer, 'order_courier_position', {'p_order': oid})
            assert position
        measured(driver, 'deliver_order', {'p_id': oid, 'p_cash': 65, 'p_note': None})
        return oid
    def pct(values, p):
        values = sorted(values)
        return round(values[min(len(values) - 1, int((len(values) - 1) * p))], 2) if values else None
    offset = 0
    for concurrency in stages:
        t = time.perf_counter()
        start = len(metrics)
        successes, failures = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            futs = [pool.submit(trip, i) for i in range(offset, offset + concurrency)]
            for f in concurrent.futures.as_completed(futs):
                try:
                    successes.append(f.result())
                except Exception as e:
                    failures.append(str(e))
        duration = time.perf_counter() - t
        rows = metrics[start:]
        values = [x['ms'] for x in rows]
        result['stages'].append({'concurrency': concurrency, 'journeys_completed': len(successes), 'journey_failures': failures, 'duration_s': round(duration, 2), 'requests': len(rows), 'rps': round(len(rows) / duration, 2), 'http_error_rate': sum(x['status'] >= 400 for x in rows) / len(rows), 'p50_ms': pct(values, .5), 'p95_ms': pct(values, .95), 'p99_ms': pct(values, .99), 'max_ms': round(max(values), 2)})
        print('LOAD ' + json.dumps(result['stages'][-1]), flush=True)
        offset += concurrency
        save(HERE / 'result-load.json', result)
    with db() as c:
        stats = c.execute("select calls,round(total_exec_time::numeric,2),round(mean_exec_time::numeric,3),rows,left(query,300) from pg_stat_statements where query not like '%pg_stat_statements%' order by total_exec_time desc limit 12").fetchall()
        result['db_top_queries'] = [dict(zip(['calls', 'total_ms', 'mean_ms', 'rows', 'normalized_query'], row)) for row in stats]
        result['db_counters'] = dict(zip(['commits', 'rollbacks', 'blocks_read', 'blocks_hit', 'deadlocks', 'temp_bytes'], c.execute("select xact_commit,xact_rollback,blks_read,blks_hit,deadlocks,temp_bytes from pg_stat_database where datname=current_database()").fetchone()))
        result['confirmed_delivered'] = q(c, "select count(*) from orders where client_key like 'load_order_%%' and status='delivered'")
        result['driver_double_active'] = q(c, "select count(*) from (select driver_id from orders where status in ('preparing','ready','pickedup') and driver_id is not null group by driver_id having count(*)>1) x")
    result['pass'] = result['confirmed_delivered'] == total_journeys and all(not x['journey_failures'] and x['http_error_rate'] == 0 for x in result['stages'])
    result['production_capacity_claim'] = False
    save(HERE / 'result-load.json', result)
    if not result['pass']:
        raise SystemExit(1)


def restore():
    tables = ['profiles', 'stores', 'menu_items', 'orders', 'order_items', 'order_events', 'audit_log', 'wallet_entries', 'loyalty_ledger', 'finance_private.commands', 'finance_private.settlement_receipts', 'finance_private.settlement_receipt_orders', 'auth.users']
    hashes = {}
    for name in ['talabot_pilot', 'talabot_pilot_restore']:
        with db(name) as c:
            hashes[name] = {}
            for table in tables:
                # Hash sensitive auth rows inside the isolated runtime, never export them.
                value = q(c, 'select coalesce(jsonb_agg(v order by v::text)::text,\'[]\') from (select to_jsonb(t) v from ' + table + ' t) x')
                hashes[name][table] = {'rows': q(c, 'select count(*) from ' + table), 'sha256': hashlib.sha256(value.encode()).hexdigest()}
            definitions = c.execute("select p.oid::regprocedure::text,pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','finance_private','auth') and p.prokind='f' order by p.oid::regprocedure::text").fetchall()
            hashes[name]['function_definitions'] = {'count': len(definitions), 'sha256': hashlib.sha256(json.dumps(definitions).encode()).hexdigest()}
    assert hashes['talabot_pilot'] == hashes['talabot_pilot_restore']
    value = {'pass': True, 'scope': 'isolated native logical pg_dump/pg_restore including actual auth schema and receipt rows', 'tables': hashes, 'backup_bytes': (HERE / 'backup.dump').stat().st_size, 'live_backup_or_R2_storage_tested': False, 'backup_exported': False}
    save(HERE / 'result-restore.json', value)
    print('PASS backup_restore_exact_table_hashes', flush=True)


def driver_fixture():
    wait(lambda:request(3000,'/')[0]==200,'rest')
    oid=order(bearer('outsider'))
    rpc(bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'})
    rpc(bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':uid('driver1')})
    save(HERE/'.runtime-driver-order.json',{'id':oid})


def export():
    data = {p.name: json.loads(p.read_text()) for p in HERE.glob('result*.json')}
    data['source_sha'] = os.environ.get('GITHUB_SHA')
    data['container_images'] = subprocess.check_output(['docker', 'images', '--digests', '--format', '{{.Repository}}:{{.Tag}} {{.Digest}}'], text=True).splitlines()
    if any('error' in key for key in data):
        import re
        logs = subprocess.run(['docker', 'compose', '--env-file', str(HERE / '.runtime.env'), '-f', str(HERE / 'compose.yml'), 'logs', '--no-color', '--tail=45', 'auth'], capture_output=True, text=True).stdout
        for value in [state()['password'], state()['jwt']]:
            logs = logs.replace(value, '[REDACTED]')
        logs = re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[JWT_REDACTED]', logs)
        data['sanitized_auth_diagnostics'] = logs
        try:
            with db() as c:
                data['auth_relations'] = c.execute("select schemaname,tablename from pg_tables where schemaname='auth' order by tablename").fetchall()
        except Exception:
            pass
    raw_text = json.dumps(data, ensure_ascii=False, default=str)
    if STATE.exists():
        runtime = state()
        values = [runtime['password'], runtime['jwt']]
        values.extend(v for a in runtime['accounts'].values() for k,v in a.items() if k in ('password','access_token','refresh_token'))
        for value in values:
            raw_text = raw_text.replace(value, '[REDACTED]')
    raw = raw_text.encode()
    print('PILOT_RESULT_ZLIB_BASE64=' + base64.b64encode(zlib.compress(raw)).decode(), flush=True)


if __name__ == '__main__':
    functions = {'env': prepare_env, 'db': prepare_db, 'app': prepare_app, 'integration': integration, 'load': load, 'restore': restore, 'driver_fixture':driver_fixture, 'export': export}
    try:
        functions[sys.argv[1]]()
    except Exception as e:
        save(HERE / ('result-error-' + sys.argv[1] + '.json'), {'pass': False, 'stage': sys.argv[1], 'error': str(e), 'traceback': traceback.format_exc()})
        raise
