import json,subprocess,sys,hashlib
from pathlib import Path
from html.parser import HTMLParser
root=Path(sys.argv[1]);src=(root/'public/customer.html').read_text();core=(root/'public/talabat-core.js').read_text()
fn=src[src.index('function cxCard('):src.index('/* a live notice',src.index('function cxCard('))]
esc=next(l.strip() for l in core.splitlines() if l.strip().startswith('function esc(s)'))
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.handlers=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if 'sdi' in d.get('class','').split():self.handlers.append(d.get('onclick'))
def node(s):return json.loads(subprocess.check_output(['node','-e',s],text=True))
cases=['Normal restaurant',"O\'Hara",'Double " quote','&quot; plain entity','&quot;);globalThis.__audit=1;//','&#34;);globalThis.__audit=1;//','line\u2028separator\u2029end']
results=[]
for candidate in [False]:
 renderer=fn.replace("JSON.stringify(s.n).replace(/\"/g,'&quot;')","esc(JSON.stringify(s.n))") if candidate else fn
 for name in cases:
  html=node(esc+';const t=x=>x,simStores=()=>[],simDishes=()=>[{s:{n:'+json.dumps(name)+'},it:{name:"Synthetic dish"}}],pxH=()=>"",sdOf=()=>0;'+renderer+';console.log(JSON.stringify(cxCard({status:"rejected",cancelReason:"out_of_stock"})))')
  p=Parser();p.feed(html);h=p.handlers[0]
  got=node('const vm=require("node:vm"),c={};c.openN=x=>c.value=x;try{vm.runInNewContext('+json.dumps(h)+',c);console.log(JSON.stringify({value:c.value,marker:c.__audit||0}));}catch(e){console.log(JSON.stringify({error:e.name,marker:c.__audit||0}));}')
  results.append({'candidate_only':candidate,'input':name,'result':got,'preserves_literal_argument':got.get('value')==name,'marker_not_executed':got.get('marker')==0})
assert all(x['preserves_literal_argument'] and x['marker_not_executed'] for x in results)
print(json.dumps({'file_sha256':hashlib.sha256(src.encode()).hexdigest(),'method':'actual cxCard renderer, HTMLParser attribute decoding, local VM stub; no browser/network/DB','results':results},ensure_ascii=False,indent=2))
