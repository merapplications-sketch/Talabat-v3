"""One-shot observer with a durable alert journal and optional receipt transport.

The receiver must durably deduplicate Idempotency-Key before acknowledging an
event. Its delivery receipt is distinct from a human on-call acknowledgement.
No scheduler or real destination is configured by this module.
"""
import argparse
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.parse
import urllib.request
import uuid


def check(config, prior=None):
    prior = prior or {}
    state, events = {}, []
    for endpoint in config['endpoints']:
        name = endpoint['name']
        healthy, error = False, None
        started = time.monotonic()
        try:
            headers = {key: os.environ[value] for key, value in endpoint.get('headers_env', {}).items()}
            request = urllib.request.Request(endpoint['url'], headers=headers)
            with urllib.request.urlopen(request, timeout=endpoint.get('timeout_s', 5)) as response:
                body = response.read(1024 * 1024)
                healthy = response.status == 200 and endpoint.get('contains', '').encode() in body
                if not healthy:
                    error = 'status_or_content_mismatch'
        except Exception as exc:
            error = type(exc).__name__
        state[name] = {
            'healthy': healthy, 'observed_at': int(time.time()),
            'latency_ms': round((time.monotonic() - started) * 1000, 1), 'error': error,
        }
        previous = prior.get(name)
        event_type = None
        if not healthy and (not previous or previous['healthy']):
            event_type = 'incident'
        elif healthy and previous and not previous['healthy']:
            event_type = 'recovery'
        if event_type:
            events.append({
                'type': event_type, 'endpoint': name,
                'at': state[name]['observed_at'], 'id': uuid.uuid4().hex,
            })
    return state, events


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_write(path, json.dumps(value, indent=2) + '\n')


def load_journal(state_path, outbox_path):
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    if 'journal_version' in previous:
        if previous['journal_version'] != 1:
            raise ValueError('unsupported_journal_version')
        return previous
    # Older snapshots contain only health. Historical outbox entries have no
    # delivery receipts, so retain them without guessing whether to resend them.
    history = []
    if outbox_path.is_file():
        history = [json.loads(line) for line in outbox_path.read_text().splitlines() if line.strip()]
    return {'journal_version': 1, 'health': previous, 'events': [], 'legacy_outbox': history}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def deliver(event, config):
    destination = urllib.parse.urlsplit(os.environ[config['url_env']])
    if destination.username or destination.password or destination.fragment:
        raise ValueError('invalid_delivery_url')
    if destination.scheme != 'https':
        if destination.scheme != 'http' or not ipaddress.ip_address(destination.hostname).is_loopback:
            raise ValueError('delivery_requires_https_or_literal_loopback')
    headers = {key: os.environ[value] for key, value in config.get('headers_env', {}).items()}
    headers.update({'Content-Type': 'application/json', 'Idempotency-Key': event['id']})
    request = urllib.request.Request(
        destination.geturl(), data=json.dumps(event).encode(), headers=headers, method='POST',
    )
    with urllib.request.build_opener(NoRedirect).open(request, timeout=config.get('timeout_s', 5)) as response:
        receipt = json.loads(response.read(65537))
        if response.status not in (200, 201) or receipt.get('event_id') != event['id']:
            raise ValueError('invalid_delivery_receipt')
        if receipt.get('status') != 'delivered' or not isinstance(receipt.get('receipt_id'), str) or not receipt['receipt_id']:
            raise ValueError('unconfirmed_delivery_receipt')
        return {'receipt_id': receipt['receipt_id'], 'confirmed_at': int(time.time())}


def run_once(config, state_path, outbox_path):
    state_path, outbox_path = Path(state_path), Path(outbox_path)
    lock_path = Path(str(state_path) + '.lock')
    if outbox_path.resolve() in {state_path.resolve(), lock_path.resolve()}:
        raise ValueError('state_outbox_paths_must_differ')
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # One owner covers observation, journal replacement, export and receipts.
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        journal = load_journal(state_path, outbox_path)
        current, events = check(config, journal['health'])
        journal['health'] = current
        journal['events'].extend({'event': event, 'exported': False, 'receipt': None} for event in events)
        atomic_json(state_path, journal)

        unwritten = [record for record in journal['events'] if not record['exported']]
        if unwritten or not outbox_path.is_file():
            payloads = journal['legacy_outbox'] + [record['event'] for record in journal['events']]
            atomic_write(outbox_path, ''.join(json.dumps(event) + '\n' for event in payloads))
            for record in unwritten:
                record['exported'] = True
            atomic_json(state_path, journal)

        delivered, delivery_error = 0, None
        if config.get('delivery'):
            for record in journal['events']:
                if record['receipt'] is not None:
                    continue
                try:
                    receipt = deliver(record['event'], config['delivery'])
                except Exception as exc:
                    # Retain this event and its original key. Stop here so a
                    # recovery cannot overtake the incident it follows.
                    delivery_error = type(exc).__name__
                    break
                record['receipt'] = receipt
                atomic_json(state_path, journal)
                delivered += 1
        return {
            'healthy': all(value['healthy'] for value in current.values()),
            'events_written': len(unwritten), 'deliveries_confirmed': delivered,
            'pending_delivery': sum(record['receipt'] is None for record in journal['events']),
            'legacy_unconfirmed': len(journal['legacy_outbox']),
            'delivery_error': delivery_error,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--outbox', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    result = run_once(config, args.state, args.outbox)
    print(json.dumps(result))
    if result['delivery_error']:
        raise SystemExit(1)
