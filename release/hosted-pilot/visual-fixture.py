"""Render test-only catalogue SQL. Does not connect or execute it."""
import argparse,base64,pathlib,re
p=argparse.ArgumentParser();p.add_argument('--target',required=True);a=p.parse_args()
assert a.target=='fsvrsvqfknogwmhccera','Only the isolated test target is allowed'
root=pathlib.Path(__file__).resolve().parents[2]
s=pathlib.Path(__file__).with_suffix('.sql.in').read_text()
def image(m):
 data=(root/'assets/3d'/m.group(1)).read_bytes()
 return 'data:image/webp;base64,'+base64.b64encode(data).decode()
print(re.sub(r'fixture-image:([a-z-]+\.webp)',image,s))
