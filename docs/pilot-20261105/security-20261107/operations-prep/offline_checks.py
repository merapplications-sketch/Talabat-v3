"""Offline preparation utilities. No sockets, provider clients or shell execution.

These validate exercise artifacts, not TALABOT's live controls. A manifest must
come from a trusted export; matching hashes alone cannot authenticate a backup.
"""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from uuid import UUID

PILOT = 'fsvrsvqfknogwmhccera'
PRODUCTION = 'dzydscryrnahnneydnry'


def restore_target(project, approved_targets):
    if project in (PILOT, PRODUCTION) or project not in approved_targets:
        raise ValueError('separate approved disposable target required')
    return project


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def verify_bundle(root, manifest):
    """Verify DB export and independently inventoried Storage bytes, fail closed."""
    root = Path(root).resolve(strict=True)
    if manifest.get('source_project') != PILOT or manifest.get('format') != 1:
        raise ValueError('unapproved source or format')
    if not manifest.get('export_started_utc') or not manifest.get('export_finished_utc'):
        raise ValueError('export interval required')
    files = manifest['files']
    if not files or not any(x['kind'] == 'database' for x in files):
        raise ValueError('database artifact required')
    expected = manifest['storage_inventory']
    seen, objects = set(), set()
    for item in files:
        rel = PurePosixPath(item['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in str(rel) or not rel.parts:
            raise ValueError('unsafe artifact path')
        path = root / str(rel)
        if any((root.joinpath(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts)+1)):
            raise ValueError('symlink refused')
        if not path.resolve(strict=True).is_relative_to(root) or str(rel) in seen:
            raise ValueError('duplicate or outside artifact')
        seen.add(str(rel))
        if item['kind'] not in ('database', 'storage'):
            raise ValueError('unknown artifact kind')
        if not path.is_file() or path.stat().st_size != item['size'] or digest(path) != item['sha256']:
            raise ValueError('artifact integrity mismatch')
        if item['kind'] == 'storage':
            key = (item['bucket'], item['object'])
            if key in objects:
                raise ValueError('duplicate storage object')
            objects.add(key)
    inventory = {(x['bucket'], x['object']) for x in expected}
    if len(inventory) != len(expected) or inventory != objects:
        raise ValueError('storage inventory incomplete or duplicated')
    return {'verified_files': len(seen), 'verified_objects': len(objects),
            'database_restored': False, 'auth_restored': False,
            'trusted_manifest_required': True}


def incident_event(raw):
    """Allowlist, not key-name redaction; arbitrary strings never reach output."""
    event_id = str(UUID(raw['event_id']))
    if raw.get('project') != PILOT or raw.get('synthetic') is not True:
        raise ValueError('synthetic pilot events only')
    kind = raw['kind']
    if kind not in ('auth_failure_burst', 'authorization_denied', 'service_unavailable', 'cost_threshold'):
        raise ValueError('unsupported event')
    count = raw['count']
    if type(count) is not int or not 1 <= count <= 10000:
        raise ValueError('invalid count')
    return {'event_id': event_id, 'project': PILOT, 'synthetic': True,
            'kind': kind, 'count': count}


def delivery_drill(event, statuses):
    """Local scripted transport only. No external notification can be emitted."""
    safe = incident_event(event)
    attempts = []
    for status in list(statuses)[:3]:
        if type(status) is not int or status not in range(100, 600):
            raise ValueError('invalid simulated status')
        attempts.append(status)
        if 200 <= status < 300:
            return {'event': safe, 'attempts': attempts, 'transport_ack': True,
                    'human_receipt': False, 'external_delivery': False}
        if status == 429 or status < 500:
            break
    return {'event': safe, 'attempts': attempts, 'transport_ack': False,
            'human_receipt': False, 'external_delivery': False}


def rate_drill(statuses, budget=8):
    """Bounded replay of captured/synthetic statuses, NEVER sends requests.

    Stop at first 429/5xx/timeout. Shared-IP and recovery probes must be separate
    explicitly scheduled phases; no automatic extra attempt during a lockout.
    """
    if type(budget) is not int or not 1 <= budget <= 16:
        raise ValueError('budget must be 1..16')
    observed = []
    for status in statuses:
        if len(observed) == budget:
            break
        if status is not None and (type(status) is not int or not 100 <= status < 600):
            raise ValueError('invalid status')
        observed.append(status)
        if status is None or status == 429 or status >= 500:
            break
    return {'observed': observed, 'provider_tested': False,
            'halted': bool(observed and (observed[-1] is None or observed[-1] == 429 or observed[-1] >= 500))}


def recovery_case(address, role):
    """Prepare a non-deliverable fixture; no tokens, mail client, or password."""
    if not re.fullmatch(r'[a-z0-9-]+@talabot-test\.invalid', address):
        raise ValueError('offline fixtures must use reserved .invalid domain')
    if role not in ('customer', 'admin'):
        raise ValueError('unsupported recovery fixture')
    return {'fixture': address, 'role': role, 'send_enabled': False,
            'steps': ['request_once', 'generic_response', 'receive_authorized_mailbox',
                      'approved_redirect', 'single_use', 'expiry', 'new_login',
                      'old_session_check'] + (['mfa_still_required', 'lost_factor_separate_recovery'] if role == 'admin' else ['no_new_mfa_requirement']),
            'live_status': 'NOT_TESTED'}
