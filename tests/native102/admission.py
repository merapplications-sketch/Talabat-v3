"""Run original four native98 assertions against strict cumulative102 fixture.
Only input paths change; original assertions and concurrency coordination are retained.
"""
from pathlib import Path
base=Path('tests/native98/setup.sql').read_text()
strict=Path('tests/native102/constraints.sql').read_text()
candidate=Path('tests/native102/candidate.sql').read_text()
Path('tests/native102/setup.generated.sql').write_text(base+strict+candidate)
source=Path('tests/native98/admission.py').read_text()
assert source.count("Path('tests/native96/setup.sql')")==1
source=source.replace("Path('tests/native96/setup.sql')","Path('tests/native102/setup.generated.sql')")
override=" if Path('tests/native98/place_order.fixed.sql').exists():a.execute(Path('tests/native98/place_order.fixed.sql').read_text())"
assert source.count(override)==2
source=source.replace(override,'')
try:exec(compile(source,'native98 assertions with candidate102','exec'),{'__name__':'__main__'})
finally:Path('tests/native102/setup.generated.sql').unlink(missing_ok=True)
Path('native98-result.json').rename('native102-admission.json')
