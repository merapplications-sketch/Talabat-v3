#!/usr/bin/env python3
"""Offline regression: extract actual renderers, parse HTML attributes, execute only handlers in a stub VM."""
import json, pathlib, subprocess, sys
from html.parser import HTMLParser
source=pathlib.Path(sys.argv[1]).read_text()
core=pathlib.Path(sys.argv[2]).read_text() if len(sys.argv)>2 else ''
esc="function esc(s){return String(s==null?'':s).replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));}"
if core:
 esc=next(line.strip() for line in core.splitlines() if line.strip().startswith('function esc(s)'))
def extract(start,end): return source[source.index(start):source.index(end,source.index(start))]
support=extract('function supCard()','async function supSave()')
staff=extract('function vStaff()','function addPromo()')
def node(script): return json.loads(subprocess.check_output(['node','-e',script],stderr=subprocess.STDOUT))
class Buttons(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True);self.handlers=[]
 def handle_starttag(self,tag,attrs):
  if tag=='button' and dict(attrs).get('onclick'): self.handlers.append(dict(attrs)['onclick'])
def handlers(markup):
 p=Buttons();p.feed(markup);return p.handlers
results=[]
def record(name,action):
 try: action();results.append({'test':name,'pass':True})
 except Exception as e:results.append({'test':name,'pass':False,'error':str(e)[:300]})
def support_test(value):
 markup=node(esc+';let SUP=null;const TLB={supportInfo:()=>('+json.dumps({'phone':value,'hours':value})+')};const t=x=>x;'+support+';console.log(JSON.stringify(supCard()))')
 handler=handlers(markup)[0]
 result=node('const vm=require("node:vm");const ctx={SUP:null,count:0,render(){this.count++}};ctx.render=()=>ctx.count++;try{vm.runInNewContext('+json.dumps(handler)+',ctx);console.log(JSON.stringify({value:ctx.SUP,marker:ctx.__audit||0,count:ctx.count}));}catch(e){console.log(JSON.stringify({error:e.name}));}')
 assert result.get('value')=={'ph':value,'hrs':value} and result.get('marker')==0 and result.get('count')==1,result
cases=['ordinary 09:00–18:00',"O'Hara",'quote " and backslash \\', '&quot; &#39; &amp; <tag>', 'line\u2028separator\u2029end', "'};globalThis.__audit=1;//"]
for i,value in enumerate(cases):record('support-context-'+str(i),lambda value=value:support_test(value))
def staff_test(email,active):
 row={'user_id':'00000000-0000-4000-8000-000000000001','email':email,'name':'Example','perms':['orders','support'],'active':active}
 markup=node(esc+';const TLB={isSuper:()=>true};const STF={list:['+json.dumps(row)+'],email:"",perms:[],busy:false};const PERMS=["orders","support"];const t=x=>x;'+staff+';console.log(JSON.stringify(vStaff()))')
 for prefix,expected in [('stfSave(',[row['user_id'],email]),('stfActive(',[row['user_id'],email,row['perms'],not active])]:
  handler=next(x for x in handlers(markup) if x.startswith(prefix))
  result=node('const vm=require("node:vm");const ctx={};ctx.stfSave=(...x)=>ctx.args=x;ctx.stfActive=(...x)=>ctx.args=x;try{vm.runInNewContext('+json.dumps(handler)+',ctx);console.log(JSON.stringify({args:ctx.args,marker:ctx.__audit||0}));}catch(e){console.log(JSON.stringify({error:e.name}));}')
  assert result.get('args')==expected and result.get('marker')==0,{'handler':prefix,'result':result}
for email in ['normal@example.test',"o'hara@example.test",'entity&quot;@example.test']:
 for active in [True,False]:record('staff-'+email+'-'+str(active),lambda email=email,active=active:staff_test(email,active))
if core:
 # Exercise actual client staffSet input validation using a stub rpc, with no network.
 body=core[core.index('staffSet: function (email, perms, active) {'):core.index('    brandRoute:',core.index('staffSet: function (email, perms, active) {'))].strip().rstrip(',')
 script='const ALL_PERMS=["orders"];let sent=null;function rpc(name,args){sent={name,args};return Promise.resolve({ok:true})};const TLB={'+body+'};TLB.staffSet("o\'hara@example.test",["orders"],true).then(()=>console.log(JSON.stringify(sent)));'
 def allowed():
  got=node(script);assert got and got['args']['p_email']=="o'hara@example.test",got
 record('actual-staffSet-allows-apostrophe-email',allowed)
print(json.dumps({'passed':sum(x['pass'] for x in results),'total':len(results),'results':results},indent=2))
sys.exit(0 if all(x['pass'] for x in results) else 1)
