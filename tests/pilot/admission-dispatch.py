"""Exercise actual offer creation, only the new consent/admission interaction."""
import importlib.util
import os
from pathlib import Path

import confirmation as cf
import lab

spec = importlib.util.spec_from_file_location(
    'backup_fixture', Path(__file__).with_name('confirmation-backup.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

result = {'source': os.environ.get('GITHUB_SHA'), 'live': False, 'checks': []}
try:
    oid, revision = fixture.seed(accept=False)
    with lab.db() as db:
        # With no fresh location, dispatch broadcasts to every eligible courier.
        db.execute(
            "update profiles set online=true,last_seen=now(),loc_updated=null where id=any(%s::uuid[])",
            ([lab.uid('driver1'), lab.uid('driver2')],),
        )
    merchant = lab.bearer('merchant')
    lab.rpc(merchant, 'dispatch_tick', {})
    with lab.db() as db:
        assert lab.q(db, 'select count(*) from order_offers where order_id=%s', (oid,)) == 0
    result['checks'].append('held order creates no courier offer')
    cf.confirm(lab.bearer('customer'), oid, revision)
    lab.rpc(merchant, 'dispatch_tick', {})
    with lab.db() as db:
        offers = db.execute(
            'select driver_id::text,mode::text,state::text from order_offers where order_id=%s',
            (oid,),
        ).fetchall()
    assert offers == [(lab.uid('driver1'), 'broadcast', 'pending')], offers
    result['checks'].append('approved order broadcasts only to the enrolled online courier')
    result.update({'pass': True, 'offers': offers})
    print('PASS new consent/admission automatic dispatch', flush=True)
except Exception as exc:
    result.update(error=str(exc), **{'pass': False})
    raise
finally:
    lab.save(lab.HERE / 'result-admission-dispatch.json', result)
