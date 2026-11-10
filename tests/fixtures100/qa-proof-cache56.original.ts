// Temporary TEST fixture maintenance: fixed synthetic bytes/path only; no caller-supplied target.
const TEST='https://fsvrsvqfknogwmhccera.supabase.co';
const BUYER='5dd0ab3d-640a-415b-9772-75dc4529c740';
const PATH=BUYER+'/talabot-storage54-fixture.jpg';
const ORIGIN='https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site';
const cors={'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Headers':'authorization,apikey,content-type','Access-Control-Allow-Methods':'POST,OPTIONS','Cache-Control':'private, no-store'};
const result=(status:number,code:string)=>new Response(JSON.stringify({code}),{status,headers:{...cors,'Content-Type':'application/json'}});
Deno.serve(async(req:Request)=>{
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors});
 if(req.method!=='POST')return result(405,'method_not_allowed');
 if(Deno.env.get('SUPABASE_URL')!==TEST||Date.now()>Date.parse('2026-11-08T18:00:00Z'))return result(410,'fixture_setup_closed');
 const auth=req.headers.get('authorization')||'';
 if(!auth.startsWith('Bearer '))return result(401,'authentication_required');
 const anon=Deno.env.get('SUPABASE_ANON_KEY')||'';
 try{
 const headers={apikey:anon,Authorization:auth};
 const u=await fetch(TEST+'/auth/v1/user',{headers});
 if(!u.ok)return result(401,'invalid_session');
 const user=await u.json();if(user.id!==BUYER||user.email!=='qa51-buyer@talabot-test.invalid')return result(403,'fixture_owner_required');
 const active=await fetch(TEST+'/rest/v1/rpc/account_enabled',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:'{}'});
 if(!active.ok||await active.json()!==true)return result(403,'account_blocked');
 const service=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');if(!service)return result(503,'fixture_setup_unavailable');
 const bytes=Uint8Array.from(atob('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAgACADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDkqKKK9w8gKKKKACiiigAooooA/9k='),c=>c.charCodeAt(0));
 const put=await fetch(TEST+'/storage/v1/object/proofs/'+PATH,{method:'PUT',headers:{apikey:service,Authorization:'Bearer '+service,'Content-Type':'image/jpeg','Cache-Control':'private, no-store, max-age=0, must-revalidate'},body:bytes});
 if(!put.ok)return result(502,'fixture_update_failed');
 return result(200,'fixed_fixture_cache_updated');
 }catch(_){return result(503,'fixture_setup_unavailable');}
});
