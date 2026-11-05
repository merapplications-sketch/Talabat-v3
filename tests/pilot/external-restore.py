"""Encrypted synthetic DB + Storage handoff through GitHub artifact storage.

Two independent runners. Recipient key never leaves the restore runner. The
restore job waits for successful source teardown before downloading its backup.
"""
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import zlib

import lab
import storage

HERE = lab.HERE
WORK = HERE / '.runtime-offsite'
COMPOSE = storage.COMPOSE
RESULT = {'source': os.environ.get('GITHUB_SHA'), 'live': False, 'synthetic_only': True, 'checks': []}
REPOSITORY = 'merapplications-sketch/Talabat-v3'
SCHEMAS = ['public', 'finance_private', 'fulfillment_private', 'pilot_private', 'return_private', 'storage']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(condition, name, detail=None):
    assert condition, name
    RESULT['checks'].append({'name': name, 'pass': True, 'detail': detail})
    print('PASS ' + name, flush=True)


def api(path):
    assert path.startswith('/repos/' + REPOSITORY + '/actions/')
    request = urllib.request.Request('https://api.github.com' + path, headers={
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json',
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def artifact(name, allowed, wait_source=False):
    deadline = time.monotonic() + 720
    run = os.environ['GITHUB_RUN_ID']
    suffix = os.environ['GITHUB_RUN_ATTEMPT']
    while time.monotonic() < deadline:
        if wait_source:
            jobs = api(f'/repos/{REPOSITORY}/actions/runs/{run}/jobs')['jobs']
            source = next((job for job in jobs if job['name'] == 'source'), None)
            if source is None or source['status'] != 'completed':
                time.sleep(5)
                continue
            assert source['conclusion'] == 'success', 'source_job_failed'
            RESULT['source_job_completed_before_download'] = True
        items = api(f'/repos/{REPOSITORY}/actions/runs/{run}/artifacts')['artifacts']
        item = next((item for item in items if item['name'] == name + '-' + suffix and not item['expired']), None)
        if item:
            break
        time.sleep(5)
    else:
        raise TimeoutError('external_artifact_unavailable')
    download = f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{item['id']}/zip"
    request = urllib.request.Request(download, headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN']})
    try:
        urllib.request.build_opener(NoRedirect).open(request, timeout=20)
    except urllib.error.HTTPError as response:
        assert response.code == 302, 'artifact_redirect'
        signed_url = response.headers['Location']
        assert urllib.parse.urlsplit(signed_url).scheme == 'https'
    else:
        raise AssertionError('expected_artifact_signed_redirect')
    # Only the signed URL goes to storage. The GitHub token stays on api.github.com.
    with urllib.request.urlopen(signed_url, timeout=30) as response:
        raw = response.read(3 * 1024 * 1024 + 1)
    assert len(raw) <= 3 * 1024 * 1024
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert set(archive.namelist()) == set(allowed)
        for name in allowed:
            info = archive.getinfo(name)
            assert info.file_size <= 2 * 1024 * 1024
            (WORK / name).write_bytes(archive.read(name))
    return item['id']


def snapshot():
    result = {}
    with lab.db() as database:
        tables = database.execute(
            "select schemaname,tablename from pg_tables where schemaname=any(%s) order by 1,2",
            (SCHEMAS,)).fetchall()
        for schema, table in tables:
            assert schema.replace('_', '').isalnum() and table.replace('_', '').isalnum()
            content = lab.q(database, 'select coalesce(jsonb_agg(v order by v::text)::text,\'[]\') '
                            'from (select to_jsonb(t) v from "' + schema + '"."' + table + '" t) rows')
            result[schema + '.' + table] = {'sha256': hashlib.sha256(content.encode()).hexdigest(),
                                          'rows': lab.q(database, 'select count(*) from "' + schema + '"."' + table + '"')}
        definitions = database.execute("""
            select n.nspname,p.oid::regprocedure::text,pg_get_functiondef(p.oid),p.proacl::text
            from pg_proc p join pg_namespace n on n.oid=p.pronamespace
            where n.nspname=any(%s) and p.prokind='f' order by 1,2
        """, (SCHEMAS,)).fetchall()
        result['functions_and_grants'] = hashlib.sha256(json.dumps(definitions).encode()).hexdigest()
        guards = database.execute("""
            select n.nspname,c.relname,t.tgname,pg_get_triggerdef(t.oid),t.tgenabled
            from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
            where n.nspname=any(%s) and not t.tgisinternal order by 1,2,3
        """, (SCHEMAS,)).fetchall()
        result['triggers'] = hashlib.sha256(json.dumps(guards).encode()).hexdigest()
        policies = database.execute("""
            select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
            from pg_policies where schemaname=any(%s) order by 1,2,3
        """, (SCHEMAS,)).fetchall()
        result['policies'] = hashlib.sha256(json.dumps(policies).encode()).hexdigest()
        permissions = database.execute("""
            select n.nspname,c.relname,c.relrowsecurity,c.relacl::text
            from pg_class c join pg_namespace n on n.oid=c.relnamespace
            where n.nspname=any(%s) and c.relkind in ('r','S') order by 1,2
        """, (SCHEMAS,)).fetchall()
        result['table_sequence_grants_and_rls'] = hashlib.sha256(json.dumps(permissions).encode()).hexdigest()
    return result


def recipient():
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-noenc', '-days', '1',
                    '-subj', '/CN=TALABOT synthetic external restore',
                    '-keyout', str(WORK / 'recipient.key'), '-out', str(HERE / 'offsite-recipient.pem')],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def source():
    RESULT['recipient_artifact_id'] = artifact('pilot-recipient', ['offsite-recipient.pem'])
    spec = importlib.util.spec_from_file_location('driver_returns', HERE / 'driver-returns.py')
    returns = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(returns)
    # Existing fixture builders only. Closed cash/return assertion suites do not run.
    returns.setup()
    returns.agreement()
    order = returns.pickup()
    storage.setup_policy()
    RESULT['no_advance_previous_pass'] = '42110177122/127535342961; SOURCE-FIRST-PASS.json'
    key = lab.uid('driver1') + '/' + str(order) + '/offsite-proof.jpg'
    code, _ = storage.call(lab.bearer('driver1'), 'POST', '/object/proofs/' + key, storage.JPEG, 'image/jpeg')
    assert code in (200, 201), 'synthetic_file_upload'
    with lab.db() as database:
        assert lab.q(database, 'select count(*) from wallet_entries') == 0
        assert lab.q(database, 'select count(*) from finance_private.commands') == 0
        assert lab.q(database, 'select count(*) from orders where cash_collected is not null') == 0
    manifest = {
        'source': os.environ['GITHUB_SHA'], 'run': os.environ['GITHUB_RUN_ID'],
        'snapshot_at': time.time(), 'signature': snapshot(), 'object_key': key,
        'object_sha256': hashlib.sha256(storage.JPEG).hexdigest(),
        'source_machine': hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest(),
    }
    with (WORK / 'database.dump').open('wb') as output:
        subprocess.run(COMPOSE + ['exec', '-T', 'db', 'pg_dump', '-U', 'postgres', '-Fc', 'talabot_pilot'],
                       stdout=output, check=True)
    with (WORK / 'storage.tar').open('wb') as output:
        subprocess.run(COMPOSE + ['exec', '-T', 'storage', 'tar', '-C', '/var/lib/storage', '-cf', '-', '.'],
                       stdout=output, check=True)
    accounts = {name: {field: account[field] for field in ('id', 'email', 'password')}
                for name, account in lab.state()['accounts'].items()}
    (WORK / 'accounts.json').write_text(json.dumps(accounts))
    manifest['files'] = {name: digest(WORK / name) for name in ('database.dump', 'storage.tar', 'accounts.json')}
    (WORK / 'manifest.json').write_text(json.dumps(manifest))
    with tarfile.open(WORK / 'capsule.tar', 'w') as archive:
        for name in (*manifest['files'], 'manifest.json'):
            archive.add(WORK / name, arcname=name)
    encrypted = HERE / 'offsite-encrypted.cms'
    subprocess.run(['openssl', 'cms', '-encrypt', '-binary', '-aes-256-gcm', '-outform', 'DER',
                    '-in', str(WORK / 'capsule.tar'), '-out', str(encrypted), str(WORK / 'offsite-recipient.pem')],
                   check=True)
    assert encrypted.stat().st_size < 2 * 1024 * 1024
    envelope = {'source': manifest['source'], 'run': manifest['run'], 'sha256': digest(encrypted),
                'bytes': encrypted.stat().st_size, 'synthetic_only': True}
    (HERE / 'offsite-envelope.json').write_text(json.dumps(envelope))
    RESULT['encrypted_bytes'] = envelope['bytes']
    RESULT['encrypted_sha256'] = envelope['sha256']
    RESULT['snapshot_at'] = manifest['snapshot_at']
    check(True, 'PostgreSQL dump and actual Storage file encrypted for separate recipient')
    RESULT['pass'] = True


def restore():
    started = time.monotonic()
    RESULT['backup_artifact_id'] = artifact('pilot-encrypted-backup',
                                           ['offsite-encrypted.cms', 'offsite-envelope.json'], wait_source=True)
    envelope = json.loads((WORK / 'offsite-envelope.json').read_text())
    assert envelope['source'] == os.environ['GITHUB_SHA'] and envelope['run'] == os.environ['GITHUB_RUN_ID']
    assert envelope['synthetic_only'] and digest(WORK / 'offsite-encrypted.cms') == envelope['sha256']
    subprocess.run(['openssl', 'cms', '-decrypt', '-binary', '-inform', 'DER',
                    '-in', str(WORK / 'offsite-encrypted.cms'), '-inkey', str(WORK / 'recipient.key'),
                    '-recip', str(HERE / 'offsite-recipient.pem'), '-out', str(WORK / 'capsule.tar')], check=True)
    expected = {'database.dump', 'storage.tar', 'accounts.json', 'manifest.json'}
    with tarfile.open(WORK / 'capsule.tar') as archive:
        assert set(archive.getnames()) == expected
        for name in expected:
            (WORK / name).write_bytes(archive.extractfile(name).read())
    manifest = json.loads((WORK / 'manifest.json').read_text())
    assert manifest['source'] == envelope['source'] and manifest['run'] == envelope['run']
    for name, expected_digest in manifest['files'].items():
        assert digest(WORK / name) == expected_digest
    check(manifest['source_machine'] != hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest(),
          'restore runner has a different kernel boot identity')
    with (WORK / 'database.dump').open('rb') as source_dump:
        subprocess.run(COMPOSE + ['exec', '-T', 'db', 'pg_restore', '-U', 'postgres', '-d', 'talabot_pilot',
                                 '--clean', '--if-exists', '--exit-on-error'], stdin=source_dump, check=True)
    restored = snapshot()
    RESULT['snapshot_differences'] = {key: {'expected': manifest['signature'].get(key), 'actual': restored.get(key)}
                                      for key in set(restored) | set(manifest['signature'])
                                      if restored.get(key) != manifest['signature'].get(key)}
    check(not RESULT['snapshot_differences'],
          'external PostgreSQL snapshot restores rows functions grants policies triggers and RLS',
          {'tables': sum(isinstance(value, dict) for value in manifest['signature'].values())})
    storage.prepare()
    with (WORK / 'storage.tar').open('rb') as source_files:
        subprocess.run(COMPOSE + ['run', '--rm', '--no-deps', '--entrypoint', 'sh', 'storage',
                                 '-c', 'tar -C /var/lib/storage -xf -'], stdin=source_files, check=True)
    subprocess.run(COMPOSE + ['up', '-d', 'auth', 'rest', 'storage'], check=True)
    lab.wait(lambda: lab.request(9999, '/health')[0] == 200, 'restored_auth')
    lab.wait(lambda: storage.call(None, 'GET', '/status')[0] == 200, 'restored_storage', 90)
    accounts = json.loads((WORK / 'accounts.json').read_text())
    runtime = lab.state()
    for name in ('customer', 'outsider'):
        account = accounts[name]
        code, session = lab.request(9999, '/token?grant_type=password',
                                    {'email': account['email'], 'password': account['password']})
        assert code == 200 and session['user']['id'] == account['id'], 'restored_identity'
        runtime['accounts'][name] = {**account, 'access_token': session['access_token'],
                                    'refresh_token': session['refresh_token']}
    lab.save(lab.STATE, runtime)
    code, body = storage.call(lab.bearer('customer'), 'GET', '/object/authenticated/proofs/' + manifest['object_key'])
    check(code == 200 and hashlib.sha256(body).hexdigest() == manifest['object_sha256'],
          'restored authorized customer receives identical actual Storage bytes')
    code, _ = storage.call(lab.bearer('outsider'), 'GET', '/object/authenticated/proofs/' + manifest['object_key'])
    check(code != 200, 'restored Storage rejects unrelated customer')
    corrupted = WORK / 'corrupted.cms'
    corrupted.write_bytes((WORK / 'offsite-encrypted.cms').read_bytes()[:500])
    rejected = subprocess.run(['openssl', 'cms', '-decrypt', '-binary', '-inform', 'DER',
                               '-in', str(corrupted), '-inkey', str(WORK / 'recipient.key'),
                               '-recip', str(HERE / 'offsite-recipient.pem'), '-out', str(WORK / 'rejected.tar')],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    check(rejected.returncode != 0, 'damaged external capsule rejected')
    RESULT['recovery_seconds_including_wait_for_source_teardown'] = round(time.monotonic() - started, 3)
    RESULT['snapshot_age_at_acceptance_seconds'] = round(time.time() - manifest['snapshot_at'], 3)
    RESULT['key_exported'] = False
    RESULT['production_rpo_rto_accepted'] = False
    RESULT['pass'] = True


WORK.mkdir(mode=0o700, exist_ok=True)
stage = sys.argv[1]
try:
    {'recipient': recipient, 'source': source, 'restore': restore}[stage]()
except Exception as error:
    RESULT['pass'] = False
    RESULT['error_type'] = type(error).__name__
    if isinstance(error, AssertionError):
        RESULT['failed_check'] = str(error)
    raise
finally:
    if stage != 'recipient':
        lab.save(HERE / ('result-external-' + stage + '.json'), RESULT)
        encoded = base64.b64encode(zlib.compress(json.dumps(RESULT).encode())).decode()
        print('EXTERNAL_RESULT_ZLIB_BASE64=' + encoded, flush=True)
