from pathlib import Path
src=Path('tests/native105/regression.py').read_text()
src=src.replace("extra=", "extra=",1)
needle="src=src.replace(needle,extra+needle,1)"
assert needle in src
src=src.replace(needle,"extra+=\"overlay+=Path('tests/native106/isolation.sql').read_text()\\n\"\n"+needle).replace('native105-regression.json','native106-regression.json')
exec(compile(src,'retained26-on106','exec'),{'__name__':'__main__'})
