"""Build SQL for the explicitly isolated Supabase target. Never production."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
TARGET='fsvrsvqfknogwmhccera'
def build(out):
 out.mkdir(parents=True,exist_ok=True)
 source=(ROOT/'tests/base-lab/web/bootstrap.sql').read_text()
 source=source[source.index('set check_function_bodies=off;'):]
 source=source.replace('dzydscryrnahnneydnry',TARGET)
 source+='\ncreate trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user();\n'
 files=[('00_public_baseline.sql',source)]
 for p in [ROOT/'sql/proposed/admin_finance_integrity_20261101.sql',ROOT/'sql/proposed/admin_finance_receipts_20261102.sql',*sorted((ROOT/'sql/proposed').glob('pilot_*.sql'))]:files.append((p.name,p.read_text()))
 for n,s in files:(out/n).write_text(s)
 return [{'file':n,'sha256':hashlib.sha256(s.encode()).hexdigest()} for n,s in files]
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--target',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
 if args.target!=TARGET:raise SystemExit('Only the existing isolated project is allowed')
 print(json.dumps({'target':TARGET,'files':build(Path(args.out))},indent=2))
