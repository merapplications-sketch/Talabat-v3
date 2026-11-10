"""Unmodified native98 admission assertions with SQL103 and strict102 fixture."""
from pathlib import Path
base=Path('tests/native98/setup.sql').read_text()+Path('tests/native102/constraints.sql').read_text()+Path('tests/native103/fidelity.sql').read_text()
setup=base+'create schema extensions;create extension pgcrypto with schema extensions;'+''.join(Path('tests/native103/'+p).read_text() for p in ['schema.sql','functions.sql'])+"insert into security_private.order_request_keys103 values(1,extensions.gen_random_bytes(32),true);"
setup+=''.join(Path('tests/native104/'+p).read_text() for p in ['schema.sql','functions.sql','lifecycle.sql'])
setup+=Path('tests/native105/resources.sql').read_text()
Path('tests/native103/setup.generated.sql').write_text(setup)
s=Path('tests/native98/admission.py').read_text();assert s.count("Path('tests/native96/setup.sql')")==1
s=s.replace("Path('tests/native96/setup.sql')","Path('tests/native103/setup.generated.sql')")
old=" if Path('tests/native98/place_order.fixed.sql').exists():a.execute(Path('tests/native98/place_order.fixed.sql').read_text())"
assert s.count(old)==2;s=s.replace(old,'')
try:exec(compile(s,'native98 assertions on103','exec'),{'__name__':'__main__'})
finally:Path('tests/native103/setup.generated.sql').unlink(missing_ok=True)
Path('native98-result.json').rename('native105-admission.json')
