import base64,gzip,json,hashlib
from pathlib import Path
x=json.loads(gzip.decompress(base64.b64decode(Path('ci97/source.b64').read_bytes())))
root=Path('isolated97').resolve();root.mkdir(exist_ok=True)
for name,content in x['files'].items():
 p=(root/name).resolve()
 assert p.is_relative_to(root) and p!=root
 assert hashlib.sha256(content.encode()).hexdigest()==x['manifest']['files'][name]
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
(root/'EXPORT-MANIFEST.json').write_text(json.dumps(x['manifest'],indent=2))
