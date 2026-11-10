from pathlib import Path
src=Path('tests/native104/native.py').read_text()
needle="namespace['MIGRATION']+=overlay"
extra="overlay+=Path('tests/native105/resources.sql').read_text()+\"insert into security_private.closure_policy105(singleton,max_rows,max_account_rows,max_reason_bytes) values(true,10000,1000,1000) on conflict do nothing;\"\n"
assert needle in src
src=src.replace(needle,extra+needle,1).replace('native104-results.json','native105-regression.json')
exec(compile(src,'retained104-on105','exec'),{'__name__':'__main__'})
