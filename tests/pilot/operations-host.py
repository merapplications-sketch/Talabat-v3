"""Acceptance of isolated host configuration, role reads and actual SMTP capture.

Uses the existing disposable lab only. Does not run cash/return journeys.
Does not export credentials, user IDs, message bodies or verification links.
"""
import hashlib
import html
import json
import os
import re
import secrets
import subprocess
import urllib.error
import urllib.parse
import urllib.request

import lab

RESULT = {
    'source': os.environ.get('GITHUB_SHA'), 'live': False,
    'target': 'disposable GitHub Actions loopback PostgreSQL/GoTrue/PostgREST/Mailpit',
    'current_host_configuration_mirrored': False, 'external_mailbox_delivery': False,
    'cash_or_return_suites_rerun': False, 'checks': [],
}
OUTPUT = lab.HERE / 'result-operations-host.json'
COMPOSE = ['docker', 'compose', '--env-file', str(lab.HERE / '.runtime.env'),
           '-f', str(lab.HERE / 'compose.yml')]


def ok(condition, name, evidence=None):
    assert condition, name
    RESULT['checks'].append({'name': name, 'pass': True, 'evidence': evidence})
    lab.save(OUTPUT, RESULT)
    print('PASS operations host ' + name, flush=True)


def mail_link(email, kind):
    def find_link():
        with urllib.request.urlopen('http://127.0.0.1:8025/api/v1/messages', timeout=5) as response:
            messages = json.load(response)
        for message in messages.get('messages', []):
            if not any(recipient['Address'] == email for recipient in message.get('To', [])):
                continue
            with urllib.request.urlopen('http://127.0.0.1:8025/api/v1/message/' + message['ID'], timeout=5) as response:
                body = json.load(response)
            for link in re.findall(r'https?://[^\s"<>]+', body.get('HTML') or body.get('Text') or ''):
                link = html.unescape(link)
                url = urllib.parse.urlsplit(link)
                if (url.scheme, url.netloc, url.path) == ('http', '127.0.0.1:9999', '/verify'):
                    if urllib.parse.parse_qs(url.query).get('type') == [kind]:
                        return link
        return None
    return lab.wait(find_link, 'isolated_' + kind + '_mail', 30)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def consume_link(link, expected_type):
    try:
        urllib.request.build_opener(NoRedirect).open(link, timeout=10)
    except urllib.error.HTTPError as response:
        assert response.code in (302, 303), 'verification_redirect_status'
        redirect = urllib.parse.urlsplit(response.headers['Location'])
    else:
        raise AssertionError('expected_verification_redirect')
    assert (redirect.scheme, redirect.netloc, redirect.path) == ('http', '127.0.0.1:8080', '/customer.html')
    fragment = urllib.parse.parse_qs(redirect.fragment)
    assert fragment.get('type') == [expected_type] and fragment.get('access_token'), 'verification_session'
    code, user = lab.request(9999, '/user', token=fragment['access_token'][0])
    assert code == 200, 'verification_user'
    return user['id']


def main():
    lab.wait(lambda: lab.request(3000, '/')[0] == 200, 'isolated_rest')
    lab.wait(lambda: lab.request(9999, '/health')[0] == 200, 'isolated_auth')
    code, settings = lab.request(9999, '/settings')
    ok(code == 200 and settings['external']['email'] and not settings['mailer_autoconfirm'],
       'Auth email enabled and explicit confirmation required')
    configuration = json.loads(subprocess.check_output(COMPOSE + ['config', '--format', 'json'], text=True))
    services = configuration['services']
    auth = services['auth']['environment']
    rest = services['rest']['environment']
    ok(auth['GOTRUE_SMTP_HOST'] == 'mailpit'
       and auth['GOTRUE_EXTERNAL_ANONYMOUS_USERS_ENABLED'] == 'false'
       and rest['PGRST_DB_SCHEMAS'] == 'public'
       and rest['PGRST_DB_ANON_ROLE'] == 'anon',
       'isolated SMTP, anonymous signup and exposed REST schema settings')
    ok(all(port.get('host_ip') == '127.0.0.1' for service in services.values() for port in service.get('ports', [])),
       'all declared lab service ports bind to loopback')

    expected_profiles = {
        'customer': {'customer'}, 'outsider': {'outsider'}, 'merchant': {'merchant'},
        'driver1': {'driver1'}, 'accountant': {'accountant', 'driver1', 'driver2'},
        'admin': set(lab.state()['accounts']),
    }
    for actor, allowed in expected_profiles.items():
        code, profiles = lab.request(3000, '/profiles?select=id,role', token=lab.bearer(actor))
        ok(code == 200 and {row['id'] for row in profiles} == {lab.uid(name) for name in allowed},
           actor + ' sees exactly its allowed profile scope', {'visible_profiles': len(profiles)})
        access = lab.rpc(lab.bearer(actor), 'finance_access')
        ok(access['execute'] == (actor == 'accountant'),
           actor + ' finance capability follows explicit synthetic staff grant')
    code, profiles = lab.request(3000, '/profiles?select=id')
    ok((code == 200 and profiles == []) or code in (401, 403), 'anonymous profile read discloses no identities')
    ok(lab.request(3000, '/profiles?select=id', token=lab.bearer('customer') + 'invalid')[0] == 401,
       'invalid role token rejected by REST')

    request = urllib.request.Request('http://127.0.0.1:3000/cases?select=order_id', headers={
        'Authorization': 'Bearer ' + lab.bearer('admin'), 'Accept-Profile': 'return_private',
    })
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as error:
        ok(error.code == 406 and json.load(error)['code'] == 'PGRST106',
           'REST refuses private schema selection even for administrator token')
    else:
        raise AssertionError('private_schema_exposed')

    with lab.db() as database:
        private_tables = database.execute("""
            select n.nspname,c.relname,c.relrowsecurity,
              has_table_privilege('anon',c.oid,'SELECT'),
              has_table_privilege('authenticated',c.oid,'SELECT')
            from pg_class c join pg_namespace n on n.oid=c.relnamespace
            where n.nspname in ('finance_private','fulfillment_private','pilot_private','return_private')
              and c.relkind='r' order by 1,2
        """).fetchall()
        ok(bool(private_tables) and all(row[2] and not row[3] and not row[4] for row in private_tables),
           'private tables retain RLS and deny direct client SELECT', {'tables': len(private_tables)})
        definitions = database.execute("""
            select n.nspname,p.proname,pg_get_functiondef(p.oid)
            from pg_proc p join pg_namespace n on n.oid=p.pronamespace
            where n.nspname in ('finance_private','fulfillment_private','pilot_private','return_private')
              and p.prokind='f' order by 1,2,p.oid::regprocedure::text
        """).fetchall()
        RESULT['isolated_private_definitions_sha256'] = hashlib.sha256(json.dumps(definitions).encode()).hexdigest()
        ok(lab.q(database, 'select count(*) from orders') == 0,
           'host acceptance creates no orders or cash return journeys')

    email = 'ops-' + secrets.token_hex(5) + '@synthetic.invalid'
    password = 'Synthetic-only-' + secrets.token_hex(16)
    code, signup = lab.request(9999, '/signup?redirect_to=https%3A%2F%2Funtrusted.invalid%2F',
                              {'email': email, 'password': password})
    ok(code in (200, 201) and not signup.get('access_token'), 'fresh signup remains unconfirmed')
    signup_id = signup.get('id') or signup['user']['id']
    code, _ = lab.request(9999, '/token?grant_type=password', {'email': email, 'password': password})
    ok(code == 400, 'unconfirmed signup cannot obtain password session')
    link = mail_link(email, 'signup')
    ok(consume_link(link, 'signup') == signup_id,
       'actual confirmation SMTP message reaches Mailpit and redirects only to allowed app')

    customer = lab.state()['accounts']['customer']
    code, _ = lab.request(9999, '/recover?redirect_to=https%3A%2F%2Funtrusted.invalid%2F',
                          {'email': customer['email']})
    ok(code == 200, 'recovery request accepted on isolated Auth')
    ok(consume_link(mail_link(customer['email'], 'recovery'), 'recovery') == customer['id'],
       'actual recovery SMTP message reaches Mailpit and verifies same identity with safe redirect')
    RESULT['pass'] = True


try:
    main()
except Exception as error:
    RESULT['pass'] = False
    RESULT['error_type'] = type(error).__name__
    # Assertion labels are controlled here, never message bodies or tokens.
    if isinstance(error, AssertionError):
        RESULT['failed_check'] = str(error)
    raise
finally:
    lab.save(OUTPUT, RESULT)
