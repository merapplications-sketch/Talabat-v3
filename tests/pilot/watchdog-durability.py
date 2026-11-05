"""Targeted failure/retry tests. Only loopback HTTP and temporary files."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from threading import Thread
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('watchdog', ROOT / 'ops/pilot-watchdog.py')
watchdog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watchdog)
RESULT = {'source': os.environ.get('GITHUB_SHA'), 'live': False, 'checks': [],
          'real_on_call_delivery': False, 'human_acknowledgement': False,
          'real_escalation': False, 'receiver': 'loopback HTTP with durable SQLite idempotency ledger'}


class Receiver(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(self.server.health)
        self.end_headers()
        self.wfile.write(b'synthetic health')

    def do_POST(self):
        event = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        identifier = self.headers['Idempotency-Key']
        assert identifier == event['id']
        with sqlite3.connect(self.server.ledger) as db:
            db.execute('insert into attempts(event_id) values(?)', (identifier,))
            if self.server.mode == 'unavailable':
                self.send_response(503)
                self.end_headers()
                return
            if self.server.mode == 'redirect':
                self.send_response(302)
                self.send_header('Location', self.server.url + '/should-not-follow')
                self.end_headers()
                return
            db.execute('insert or ignore into deliveries values(?, ?)', (identifier, json.dumps(event, sort_keys=True)))
            assert db.execute('select payload from deliveries where id=?', (identifier,)).fetchone()[0] == json.dumps(event, sort_keys=True)
        # The sink's committed row is the synthetic delivery itself. Reopening
        # SQLite on every request makes response-loss retries use durable state.
        if self.server.mode == 'lost_reply':
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        receipt = {'event_id': identifier, 'status': 'delivered', 'receipt_id': 'fixture-' + identifier}
        if self.server.mode == 'wrong_receipt':
            receipt['event_id'] = 'different-event'
        body = json.dumps(receipt).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        ledger = root / 'receiver.db'
        with sqlite3.connect(ledger) as db:
            db.executescript('create table deliveries(id text primary key, payload text); create table attempts(event_id text);')
        with ThreadingHTTPServer(('127.0.0.1', 0), Receiver) as server:
            server.ledger, server.health, server.mode = ledger, 503, 'ok'
            server.url = 'http://127.0.0.1:' + str(server.server_port)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            config = {'endpoints': [{'name': 'fixture', 'url': server.url, 'timeout_s': 2}],
                      'delivery': {'url_env': 'TALABOT_TEST_RECEIVER', 'timeout_s': 2}}
            (root / 'config.json').write_text(json.dumps(config))
            with patch.dict(os.environ, {'TALABOT_TEST_RECEIVER': server.url}):
                try:
                    yield root, server, config
                finally:
                    server.shutdown()


def invoke(root):
    return subprocess.run([sys.executable, str(ROOT / 'ops/pilot-watchdog.py'),
                           '--config', str(root / 'config.json'), '--state', str(root / 'state.json'),
                           '--outbox', str(root / 'outbox.jsonl')], capture_output=True, text=True)


def counts(root):
    with sqlite3.connect(root / 'receiver.db') as db:
        return [db.execute('select count(*) from ' + table).fetchone()[0] for table in ('attempts', 'deliveries')]


def journal(root):
    return json.loads((root / 'state.json').read_text())


def outbox(root):
    return [json.loads(line) for line in (root / 'outbox.jsonl').read_text().splitlines()]


def record(name, evidence):
    RESULT['checks'].append({'name': name, 'pass': True, 'evidence': evidence})
    print('PASS ' + name, flush=True)


def main():
    with fixture() as (root, receiver, config):
        (root / 'outbox.jsonl').mkdir()
        assert invoke(root).returncode != 0
        saved = journal(root)['events'][0]
        assert not saved['exported'] and saved['receipt'] is None and counts(root) == [0, 0]
        identifier = saved['event']['id']
        (root / 'outbox.jsonl').rmdir()
        receiver.mode = 'unavailable'
        retry = invoke(root)
        assert retry.returncode == 1
        assert journal(root)['events'][0]['event']['id'] == identifier
        assert journal(root)['events'][0]['receipt'] is None
        receiver.mode = 'ok'
        delivered = invoke(root)
        assert delivered.returncode == 0 and json.loads(delivered.stdout)['pending_delivery'] == 0
        assert journal(root)['events'][0]['event']['id'] == identifier
        assert invoke(root).returncode == 0 and counts(root) == [2, 1] and len(outbox(root)) == 1
        record('outbox failure after state commit retains same event until receiver succeeds', {'attempts': 2, 'deliveries': 1})
        receiver.health = 200
        assert invoke(root).returncode == 0 and invoke(root).returncode == 0
        assert counts(root) == [3, 2] and [e['type'] for e in outbox(root)] == ['incident', 'recovery']
        record('recovery delivered once after incident, confirmed events not resent', {'attempts': 3, 'deliveries': 2})

    with fixture() as (root, receiver, config):
        receiver.mode = 'lost_reply'
        assert invoke(root).returncode == 1 and counts(root) == [1, 1]
        identifier = journal(root)['events'][0]['event']['id']
        assert journal(root)['events'][0]['receipt'] is None
        receiver.mode = 'ok'
        assert invoke(root).returncode == 0 and counts(root) == [2, 1]
        assert journal(root)['events'][0]['event']['id'] == identifier
        assert invoke(root).returncode == 0 and counts(root) == [2, 1]
        record('receiver commits delivery then loses reply, restart retries same key without duplicate', {'attempts': 2, 'deliveries': 1})

    for failure in ('before_journal', 'after_export', 'after_receipt'):
        with fixture() as (root, receiver, config):
            original = watchdog.atomic_json
            def fail_write(path, value):
                records = value['events']
                should_fail = {
                    'before_journal': True,
                    'after_export': bool(records) and records[0]['exported'],
                    'after_receipt': bool(records) and records[0]['receipt'] is not None,
                }[failure]
                if should_fail:
                    raise OSError('injected durable write failure')
                original(path, value)
            with patch.object(watchdog, 'atomic_json', fail_write):
                try:
                    watchdog.run_once(config, root / 'state.json', root / 'outbox.jsonl')
                except OSError:
                    pass
                else:
                    raise AssertionError('failure not injected')
            assert counts(root)[1] == (1 if failure == 'after_receipt' else 0)
            assert invoke(root).returncode == 0 and counts(root)[1] == 1 and len(outbox(root)) == 1
            assert invoke(root).returncode == 0
            record(failure + ' write failure safely retried', {'attempts': counts(root)[0], 'deliveries': 1})

    with fixture() as (root, receiver, config):
        with ThreadPoolExecutor(max_workers=2) as pool:
            runs = list(pool.map(lambda _: invoke(root), range(2)))
        assert all(run.returncode == 0 for run in runs)
        assert counts(root) == [1, 1] and len(outbox(root)) == 1
        record('two concurrent processes share one journal and create one delivery', {'attempts': 1, 'deliveries': 1})

    with fixture() as (root, receiver, config):
        receiver.mode = 'wrong_receipt'
        assert invoke(root).returncode == 1 and journal(root)['events'][0]['receipt'] is None
        receiver.health = 200
        receiver.mode = 'unavailable'
        assert invoke(root).returncode == 1 and counts(root) == [2, 1]
        receiver.mode = 'ok'
        assert invoke(root).returncode == 0 and counts(root) == [4, 2]
        assert [e['type'] for e in outbox(root)] == ['incident', 'recovery']
        record('wrong receipt remains pending and recovery cannot overtake incident', {'attempts': 4, 'deliveries': 2})

    with fixture() as (root, receiver, config):
        receiver.mode = 'redirect'
        assert invoke(root).returncode == 1 and counts(root) == [1, 0]
        assert journal(root)['events'][0]['receipt'] is None
        receiver.mode = 'ok'
        assert invoke(root).returncode == 0 and counts(root) == [2, 1]
        record('redirect is not followed or treated as delivery', {'attempts': 2, 'deliveries': 1})

    with fixture() as (root, receiver, config):
        previous = {'fixture': {'healthy': False, 'observed_at': 1, 'latency_ms': 1, 'error': 'HTTPError'}}
        legacy = {'type': 'incident', 'endpoint': 'fixture', 'at': 1, 'id': 'legacy-event'}
        (root / 'state.json').write_text(json.dumps(previous))
        (root / 'outbox.jsonl').write_text(json.dumps(legacy) + '\n')
        receiver.health = 200
        run = invoke(root)
        assert run.returncode == 0 and json.loads(run.stdout)['legacy_unconfirmed'] == 1
        assert outbox(root)[0] == legacy and counts(root) == [1, 1]
        assert journal(root)['events'][0]['event']['type'] == 'recovery'
        record('legacy snapshot and historical outbox retained without guessing prior delivery', {'legacy_unconfirmed': 1})

    with fixture() as (root, receiver, config):
        with patch.object(watchdog.time, 'time', return_value=1):
            for health in (503, 200, 503):
                receiver.health = health
                watchdog.run_once(config, root / 'state.json', root / 'outbox.jsonl')
        assert len({e['id'] for e in outbox(root)}) == 3 and counts(root) == [3, 3]
        record('rapid same-second incident recovery incident have distinct stable IDs', {'deliveries': 3})

    RESULT['pass'] = True


try:
    main()
except Exception as exc:
    RESULT['pass'] = False
    RESULT['error_type'] = type(exc).__name__
    raise
finally:
    RESULT['at_utc'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    Path(__file__).with_name('result-watchdog-durability.json').write_text(json.dumps(RESULT, indent=2) + '\n')
