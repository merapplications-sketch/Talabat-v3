import pathlib,json,hashlib
root=pathlib.Path('/workspace/sites/talabot-security24/.sites-checkout')
out=pathlib.Path(__file__).parent
files=[]
for folder in ['worker','public']:
 for p in (root/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.js','.html','.json']:
   files.append({'file':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(out/'component-files.json').write_text(json.dumps(files,indent=2))
triage=json.load(open(out.parent/'asvs-331-triage.json'))
scoped_na={'V1.2.5':'Worker exposes only Fetch/Response and static asset lookup/CSP JSON intake; no process invocation API. Browser runs JS only. Database/provider native processes are not attested.', 'V1.2.6':'Application identity goes through Supabase Auth, data through REST/RPC; no directory/LDAP connector in the supplied deployable components. Provider identity internals are outside supplied source.', 'V1.2.7':'Application accepts CSP JSON and browser JSON data, not XML queries; no XPath query engine in deployable runtime. Provider parser internals not attested.', 'V1.2.8':'Receipt output is escaped HTML/print, not TeX compilation; no server document rendering pipeline in Worker.', 'V1.3.8':'Worker/browser are JavaScript; no JVM or JNDI component in supplied runtime. Managed provider internals not attested.', 'V1.3.9':'Worker has no network or cache binding; browser uses memory and web storage plus Supabase. No application memcache interface. Provider backing caches not attested.', 'V1.5.1':'Only request-body intake in Worker is bounded strict UTF-8 JSON. Frontend consists of native HTML and JSON SDK calls, not XML document parser calls; static SVG/assets are not XML request parsing. Provider import/API parser behavior not attested.'}
specific={
'V1.5.2':'Applicable: Worker JSON.parse, local cart/preference JSON.parse, SDK response JSON and Realtime binary framing. Worker only projects primitive directive/status fields and does not instantiate client types. Need complete SDK/message and persisted-object assignment review before closing.',
'V1.5.3':'Applicable across browser URL/JSON parsers, Worker WHATWG URL/UTF-8 JSON, and Supabase/PostgREST JSON. Need cross-boundary duplicate-key, Unicode and URI interpretation evidence; source-only Worker proof insufficient.',
'V4.3.1':'Do not mark NA: application uses PostgREST data-layer expressions and managed Supabase may expose GraphQL separately. Need enabled-schema/endpoint inventory and actual query/resource controls.',
'V4.3.2':'No application GraphQL caller is not evidence of disabled Supabase GraphQL endpoint. Obtain project exposure/configuration and endpoint introspection policy evidence.',
'V4.4.1':'Applicable: subscribeRealtime uses sb.channel; client URL fixed to HTTPS and SDK changes protocol http to ws, producing wss. Source supports intended WSS only. Need loaded deployment/actual handshake evidence before global closure.',
'V4.4.2':'Applicable: handshake terminated by managed Supabase Realtime, not Worker. Need provider Origin policy and limited valid/invalid-Origin handshake test. CORS headers on REST do not establish this.',
'V4.4.3':'Realtime SDK uses auth access tokens; inspect lifecycle and authenticated-channel semantics. No dedicated-token NA conclusion until standard-session reuse and provider validation established.',
'V4.4.4':'Realtime is real application functionality. Need trace token provenance/session refresh into channel and provider enforcement; HTTPS base alone does not prove validation.',
'V4.1.4':'Worker explicitly permits GET/HEAD and CSP POST only. Supabase Auth/REST/Storage/Realtime methods are separate surfaces; full requirement needs actual allowed-method inventory/tests there.',
'V4.2.1':'Protocol framing is controlled by Cloudflare edge and Supabase ingress. Worker Fetch API receives parsed requests; local Request tests cannot prove anti-smuggling.',
'V4.2.2':'Worker uses Response API without manually setting Content-Length. Provider and edge emitted framing needs external/runtime evidence.',
'V4.2.3':'Browser/Worker platform generates headers but provider/edge accepts HTTP2/3. Need actual ingress evidence; source absence insufficient.',
'V4.2.4':'Managed ingress parses header bytes before Worker. Need provider guarantees and bounded protocol test; JS Headers normalization cannot prove entire path.'}
rows=[]
for r in triage:
 if not r['req_id'].startswith(('V1.','V4.')):continue
 i=r['req_id']; rows.append({'req_id':i,'official_requirement':r['official_requirement'],'decision':'scoped_application_not_applicable_candidate' if i in scoped_na else 'remain_unclosed','full_requirement_closure_proposed':False,'evidence_and_gap':scoped_na.get(i,specific.get(i,'Applicable or unresolved. Prior triage next action remains required; bounded protocol inventory does not cover all sinks/providers.')),'next_action':r['next_action'],'provider_boundary':'Supabase Auth, REST/PostgREST, Storage, Realtime, optional GraphQL and Cloudflare ingress not source-complete here.'})
(out/'per-id-decisions.json').write_text(json.dumps(rows,indent=2))
print(len(files),'components;',len(rows),'requirement decisions; no global closure')
