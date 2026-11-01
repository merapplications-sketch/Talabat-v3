"""Build a completely offline preview from the candidate source, never the newer app."""
from pathlib import Path
import re, hashlib, json
r=Path(__file__).resolve().parents[1]
admin=(r/'admin.html').read_text()
fixture=(r/'tests/fixture.js').read_text()
fixture=fixture.replace("window.__ROLE='admin';", "window.__ROLE=new URLSearchParams(location.search).get('role')||'admin';")
fixture=fixture.replace("window.__FIN_ROLE=window.__DEMO_MODE==='old-server'?'admin':'accountant';", "window.__FIN_ROLE=new URLSearchParams(location.search).get('access')||'accountant';")
fixture+="\nif(__ROLE!=='admin'){__FT.profiles[0].role=__ROLE;__FT.profiles[0].driver_status='approved';}\n"
admin=re.sub(r'<script src="https://[^\"]+"></script>',lambda m:'<script>'+fixture+'</script>',admin)
admin=re.sub(r'<script src="talabat-core.js[^\"]*"></script>',lambda m:'<script>'+(r/'talabat-core.js').read_text()+'</script>',admin)
admin=re.sub(r'<link rel="stylesheet" href="assets/admin-finance/admin-finance.css[^\"]*">',lambda m:'<style>'+(r/'assets/admin-finance/admin-finance.css').read_text()+'</style>',admin)
admin=re.sub(r'<script src="assets/admin-finance/admin-finance.js[^\"]*"></script>',lambda m:'<script>'+(r/'assets/admin-finance/admin-finance.js').read_text()+'</script>',admin)
admin=admin.replace('<head>','<head><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'">')
admin=admin.replace('<body>','<body><aside id="demo-status">ДЕМО · ИСКУССТВЕННЫЕ ДАННЫЕ · БЕЗ СЕТИ</aside>')
out=r/'tests/generated';out.mkdir(exist_ok=True)
(out/'candidate-preview.html').write_text(admin)
files=['admin.html','talabat-core.js','assets/admin-finance/admin-finance.css','assets/admin-finance/admin-finance.js']
(out/'inputs.json').write_text(json.dumps({f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in files},indent=2)+'\n')
