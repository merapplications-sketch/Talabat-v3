import http.server,threading,importlib.util,json,pathlib
spec=importlib.util.spec_from_file_location('watchdog',pathlib.Path(__file__).resolve().parents[2]/'ops/pilot-watchdog.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
status=200
class H(http.server.BaseHTTPRequestHandler):
 def do_GET(self):self.send_response(status);self.end_headers();self.wfile.write(b'TALABOT fixture')
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 config={'endpoints':[{'name':'synthetic-check','url':'http://127.0.0.1:'+str(server.server_port),'contains':'TALABOT'}]};s,e=m.check(config);assert s['synthetic-check']['healthy']and not e
 status=503;s,e=m.check(config,s);assert len(e)==1 and e[0]['type']=='incident'
 s,e=m.check(config,s);assert not e
 status=200;s,e=m.check(config,s);assert len(e)==1 and e[0]['type']=='recovery'
 result={'pass':True,'checks':4,'scope':'local fake health endpoint: healthy, incident, no duplicate incident, recovery','real_external_alert_delivery':False,'live':False};pathlib.Path(__file__).with_name('result-watchdog.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS watchdog 4 transitions')
finally:server.shutdown()
