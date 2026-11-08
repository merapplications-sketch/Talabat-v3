import re,json,urllib.request,urllib.error,datetime
from pathlib import Path
p=Path(__file__).parent
s=(p/'published-core.js').read_text()
key=re.findall(r'sb_publishable_[A-Za-z0-9_-]+',s)
assert len(key)==1 and 'https://fsvrsvqfknogwmhccera.supabase.co' in s
cases=[('brand_stats',{'p_brand':None,'p_days':1}),('branch_create',{'p_brand':None,'p_branch':'ASVS36','p_address':'synthetic','p_lat':0,'p_lng':0,'p_phone':'+992900000001'}),('brand_sync_menu',{'p_from':None,'p_to':None})]
results=[]
for name,body in cases:
 req=urllib.request.Request('https://fsvrsvqfknogwmhccera.supabase.co/rest/v1/rpc/'+name,data=json.dumps(body).encode(),headers={'apikey':key[0],'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=15) as r:status=r.status;response=r.read().decode()
 except urllib.error.HTTPError as e:status=e.code;response=e.read().decode()
 except Exception as e:status=None;response=type(e).__name__+': '+str(e)
 results.append({'rpc':name,'status':status,'body':response[:1500]})
 if status==429:break
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':'fsvrsvqfknogwmhccera','credential':'public publishable key only; no user bearer token','scope':'anonymous HTTP requests, null resource IDs; not authenticated owner or UI proof','results':results}
(p/'http-anon.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
