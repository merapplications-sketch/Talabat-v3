"""Unprivileged runtime preparation: download verified packages and extract locally only."""
from pathlib import Path
import urllib.request,lzma,json,subprocess,hashlib,concurrent.futures
root=Path(__file__).resolve().parent/'runtime-libs';root.mkdir(exist_ok=True)
for component in ['main','universe']:
 dest=root/(component+'-Packages')
 if not dest.exists():
  url='https://archive.ubuntu.com/ubuntu/dists/noble/'+component+'/binary-amd64/Packages.xz'
  dest.write_bytes(lzma.decompress(urllib.request.urlopen(url,timeout=25).read()))
packages={}
for component in ['main','universe']:
 for block in (root/(component+'-Packages')).read_text().split('\n\n'):
  fields={}
  for line in block.splitlines():
   if line and not line.startswith(' ') and ': ' in line:
    k,v=line.split(': ',1);fields[k]=v
  if 'Package' in fields:packages[fields['Package']]=fields
installed=subprocess.check_output(['dpkg-query','-W','-f','${binary:Package}\t${Status}\t${Provides}\n'],text=True)
installed_lines=[line.split('\t')for line in installed.splitlines()if '\tinstall ok installed\t' in line];installed={parts[0].split(':')[0]for parts in installed_lines};installed.update(a.strip().split(' ')[0]for parts in installed_lines for a in (parts[2]if len(parts)>2 else '').split(',')if a.strip())
providers={}
for name,p in packages.items():
 for a in p.get('Provides','').split(','):
  if a.strip():providers.setdefault(a.strip().split(' ')[0],name)
needed='libgstreamer1.0-0 libgtk-4-1 libgraphene-1.0-0 libevent-2.1-7t64 libgstreamer-plugins-base1.0-0 libgstreamer-gl1.0-0 libgstreamer-plugins-bad1.0-0 libavif16 libharfbuzz-icu0 libwayland-server0 libmanette-0.2-0 libhyphen0 libsecret-1-0 libgles2 liblzo2-2'.split()
selected={}
def add(name,force=False):
 if name in selected or (name in installed and not force):return
 if name not in packages:raise RuntimeError('package not resolved: '+name)
 p=packages[name];selected[name]=p
 for dependency in (p.get('Pre-Depends','')+','+p.get('Depends','')).split(','):
  alternatives=[s.strip().split(' ')[0].split(':')[0]for s in dependency.split('|')if s.strip()]
  if not alternatives:continue
  if any(a in installed or a in selected for a in alternatives):continue
  possible=next((a if a in packages else providers.get(a) for a in alternatives if a in packages or a in providers),None)
  if possible:add(possible)
  else:raise RuntimeError('dependency not resolved: '+str(alternatives))
for n in needed:add(n,True)
archive=root/'debs';archive.mkdir(exist_ok=True);extract=root/'extract';extract.mkdir(exist_ok=True)
def download(item):
 name,p=item;url='https://archive.ubuntu.com/ubuntu/'+p['Filename'];dest=archive/Path(p['Filename']).name
 if not dest.exists():dest.write_bytes(urllib.request.urlopen(url,timeout=25).read())
 b=dest.read_bytes();assert hashlib.sha256(b).hexdigest()==p['SHA256'],name+' checksum'
 return {'name':name,'version':p['Version'],'url':url,'sha256':p['SHA256'],'bytes':len(b),'file':str(dest)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:results=list(pool.map(download,selected.items()))
for p in results:subprocess.run(['dpkg-deb','-x',p['file'],str(extract)],check=True)
manifest={'method':'HTTPS Ubuntu noble indexes and SHA256-checked deb downloads; dpkg-deb -x to scratch only','system_package_install':False,'sandbox_or_permission_change':False,'packages':results}
(root.parent/'local-libs-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'packages':len(results),'bytes':sum(p['bytes']for p in results),'extract':str(extract)}))
