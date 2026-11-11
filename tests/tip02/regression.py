"""Affected retained tests on TIP-02; historical test files remain byte-identical."""
import os,json,unittest
from pathlib import Path
assert os.environ.get('TIP02_ISOLATED')=='yes'
# Every retained server test sees the post-TIP01 overlay, including re-upgrade paths.
s=Path('tests/tip01/regression.py').read_text()
s=s.replace("patch=Path('tests/tip01/acceptance.sql').read_text()", "patch=Path('tests/tip01/acceptance.sql').read_text()+Path('tests/tip02/acceptance.sql').read_text()")
s=s.replace("Path('tests/tip01/acceptance.sql').read_text()\\n", "Path('tests/tip01/acceptance.sql').read_text()+Path('tests/tip02/acceptance.sql').read_text()\\n")
s=s.replace('tip01-regression.json','tip02-regression.json')
exec(compile(s,'retained_server_assertions_on_tip02','exec'),{'__name__':'__main__'})
