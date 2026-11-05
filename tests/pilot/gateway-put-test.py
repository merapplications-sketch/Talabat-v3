"""New isolated bridge contract: actual HTTP PUT password update is forwarded.
No Auth account or real password. The upstream endpoint is a temporary local stub.
"""
import http.server,importlib.util,json,pathlib,sys,threading,types,urllib.request,urllib.error
root=pathlib.Path(__file__).resolve().parents[2]
sys.modules['lab']=types.SimpleNamespace(ROOT=root,HERE=root/'tests/pilot')
spec=importlib.util.spec_from_file_location('gateway',root/'tests/pilot/gateway.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
seen=[]
class Backend(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_PUT(self):
  body=self.rfile.read(int(self.headers['Content-Length']));seen.append({'path':self.path,'method':self.command,'body_matches':json.loads(body)=={'password':'synthetic-probe-only'}})
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"id":"synthetic"}')
upstream=http.server.ThreadingHTTPServer(('127.0.0.1',9999),Backend)
bridge=http.server.ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
for s in[upstream,bridge]:threading.Thread(target=s.serve_forever,daemon=True).start()
try:
 req=urllib.request.Request(f'http://127.0.0.1:{bridge.server_port}/auth/v1/user',data=b'{"password":"synthetic-probe-only"}',headers={'Content-Type':'application/json'},method='PUT')
 try:
  with urllib.request.urlopen(req)as r:status=r.status
 except urllib.error.HTTPError as e:status=e.code
 result={'live':False,'probe':'real local HTTP PUT -> bridge -> synthetic upstream /user','status':status,'upstream':seen,'pass':status==200 and seen==[{'path':'/user','method':'PUT','body_matches':True}]}
 out=root/'docs/pilot-20261105/followup'/('gateway-put-after.json'if result['pass']else'gateway-put-before.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:
 for s in[upstream,bridge]:s.shutdown();s.server_close()
