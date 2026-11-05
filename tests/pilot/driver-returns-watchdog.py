"""Exercise the existing observer against the new authenticated REST read, in the lab."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import lab

oid = json.loads((lab.HERE / '.runtime-return-ui.json').read_text())['order']
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = {'endpoints': [{'name': 'return-read', 'url':
              f'http://127.0.0.1:3000/rpc/order_return_status?p_order={oid}',
              'contains': 'can_document_departure',
              'headers_env': {'Authorization': 'LAB_RETURN_PROBE_AUTH'}}]}
    (root/'config').write_text(json.dumps(config))
    def probe(token):
        return json.loads(subprocess.check_output([
            sys.executable, str(lab.ROOT/'ops/pilot-watchdog.py'), '--config', str(root/'config'),
            '--state', str(root/'state'), '--outbox', str(root/'outbox')],
            env={**os.environ, 'LAB_RETURN_PROBE_AUTH': 'Bearer ' + token}, text=True))
    valid = lab.bearer('driver1')
    actual = [probe(token) for token in (valid, 'bad-token', 'bad-token', valid)]
    expected = [(True, 0), (False, 1), (False, 0), (True, 1)]
    assert [(r['healthy'], r['events_written']) for r in actual] == expected, actual
    events = [json.loads(line)['type'] for line in (root/'outbox').read_text().splitlines()]
    assert events == ['incident', 'recovery']
    lab.save(lab.HERE/'result-driver-returns-watchdog.json',
             {'pass': True, 'live': False, 'observations': actual, 'outbox_events': events,
              'actual_delivery': False})
    print('PASS isolated authenticated return read and alert outbox', flush=True)
