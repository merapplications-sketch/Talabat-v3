"""106 isolated dump/restore acceptance with TIP-01 and original tip20 payload."""
import os
from pathlib import Path
assert os.environ.get('TIP01_ISOLATED')=='yes'
src=Path('tests/native106/restore.py').read_text()
needle="assert os.environ.get('PGHOST')=='127.0.0.1'"
assert src.count(needle)==1
extra="MIGRATION+=Path('tests/tip01/acceptance.sql').read_text()\noriginal_args=args\ndef args(*a,**kw):\n p=original_args(*a,**kw);p[2]=20;return p\n"
src=src.replace(needle,extra+needle).replace('restore106_source','tip01_restore_source').replace('restore106_target','tip01_restore_target').replace('native106-restore.json','tip01-restore.json')
src=src.replace("assert c.execute('select max_rows,max_account_rows", "assert c.execute('select tip,total,driver_payout from orders').fetchone()==(20,42,21.5)\n  assert c.execute('select max_rows,max_account_rows")
exec(compile(src,'tip01_dump_restore','exec'),{'__name__':'__main__'})
