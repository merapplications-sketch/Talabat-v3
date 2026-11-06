"""Package current four apps for the already-created isolated project only."""
import pathlib,shutil,json,re,hashlib,argparse,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
TARGET='fsvrsvqfknogwmhccera'
p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--publishable-key',required=True);p.add_argument('--out',required=True);a=p.parse_args()
assert a.target==TARGET and a.publishable_key.startswith('sb_publishable_'),'Isolated target and browser publishable key required'
out=pathlib.Path(a.out).resolve();assert not out.exists(),'Use a new output directory; no overwrite'
out.mkdir(parents=True)
files=[ROOT/x for x in ['customer.html','merchant.html','driver.html','admin.html','talabat-core.js']]+[p for p in (ROOT/'assets').rglob('*') if p.is_file()]
manifest={'source':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'version':'pilot-mobile-20261106.1','target':TARGET,'published':False,'files':{}}
for f in files:
 rel=f.relative_to(ROOT);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);data=f.read_bytes()
 if f.suffix in ['.html','.js','.css','.svg']:
  s=data.decode().replace('dzydscryrnahnneydnry',TARGET)
  if rel.as_posix()=='talabat-core.js':s=re.sub(r"var SB_KEY = '[^']+'",lambda m:"var SB_KEY = '"+a.publishable_key+"'",s)
  data=s.encode()
 dest.write_bytes(data);manifest['files'][rel.as_posix()]=hashlib.sha256(data).hexdigest()
for f in out.rglob('*'):
 if f.is_file():assert b'dzydscryrnahnneydnry' not in f.read_bytes(),'Live backend reference left'
(out/'index.html').write_text('''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TALABOT · Тест</title><h1>TALABOT · Только тестовые данные</h1><p>pilot-mobile-20261106.1</p><p>Откройте каждое приложение в отдельной вкладке.</p>'''+''.join('<p><a target="_blank" rel="noopener" href="'+r+'.html">'+t+'</a></p>' for r,t in [('customer','Заказ'),('merchant','Ресторан'),('driver','Курьер'),('admin','Управление')]))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'source':manifest['source'],'target':TARGET,'files':len(files),'productionReferences':0,'published':False}))
