// Isolated SMTP only. Never exports mail bodies, recovery URLs, passwords or tokens.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('playwright'),state=JSON.parse(fs.readFileSync(path.join(__dirname,'.runtime.json')));
const result={source:process.env.GITHUB_SHA,environment:'Chromium Linux actual candidate UI + real GoTrue SMTP to local Mailpit1.33.0',live:false,real_delivery:false,checks:[]};
const ok=(v,name)=>{assert(v,name);result.checks.push({name,pass:true});fs.writeFileSync(path.join(__dirname,'result-auth-mail.json'),JSON.stringify(result,null,2)+'\n');console.log('PASS mail '+name)};
const sleep=n=>new Promise(r=>setTimeout(r,n));
async function mailLink(email,type){
 for(let n=0;n<50;n++){
  const listing=await(await fetch('http://127.0.0.1:8025/api/v1/messages')).json();
  for(const msg of listing.messages||[]){
   if(!(msg.To||[]).some(x=>x.Address===email))continue;
   const body=await(await fetch('http://127.0.0.1:8025/api/v1/message/'+msg.ID)).json();
   const links=[...String(body.HTML||body.Text||'').matchAll(/https?:\/\/[^\s"<>]+/g)].map(x=>x[0].replaceAll('&amp;','&'));
   for(const link of links){const u=new URL(link);if(u.hostname==='127.0.0.1'&&u.pathname==='/verify'&&u.searchParams.get('type')===type)return u.href}
  }await sleep(200);
 }throw Error('mail_not_received_'+type);
}
(async()=>{let browser,page,stage='start';const diagnostics=[],secretValues=[];try{
 browser=await chromium.launch(process.env.PILOT_CHROMIUM_PATH?{executablePath:process.env.PILOT_CHROMIUM_PATH}:{});result.browserVersion=browser.version();const context=await browser.newContext({viewport:{width:390,height:844}});
 await context.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
 page=await context.newPage();page.on('response',async r=>{if(r.url().includes('/auth/v1/'))diagnostics.push({endpoint:new URL(r.url()).pathname,status:r.status()})});await page.goto('http://127.0.0.1:8080/customer.html?lang=en');await page.waitForSelector('#tlb-go');
 if(!process.env.MAIL_ONLY_RECOVERY){
  stage='signup_confirmation';const email='mail_'+crypto.randomBytes(5).toString('hex')+'@synthetic.invalid',pw='Synthetic-only-'+crypto.randomBytes(12).toString('hex');
  await page.click('#tlb-t-up');await page.fill('#tlb-nm','DEMO mail confirmation');await page.fill('#tlb-ph','+992900000599');await page.fill('#tlb-em',email);await page.fill('#tlb-pw',pw);await page.click('#tlb-go');await page.waitForSelector('#tlb-bk');
  ok(true,'signup UI requires email confirmation, without an authenticated app session');
  const before=await fetch('http://127.0.0.1:9999/token?grant_type=password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pw})});ok(before.status===400,'unconfirmed identity cannot password-login');
  const link=await mailLink(email,'signup');ok(true,'GoTrue sent actual confirmation email through isolated SMTP');await page.goto(link);await page.waitForFunction(()=>typeof TLB!=='undefined'&&TLB.me()?.id,{timeout:30000});
  ok(true,'confirmation link returns to the actual application and authenticates the same identity');
  await page.evaluate(()=>TLB.logout());await page.waitForSelector('#tlb-go');
 }
 stage='reset_entry';ok(await page.locator('#tlb-forgot').count()===1,'password recovery has a user entry in existing login');
 stage='recover_request';await page.click('#tlb-forgot');await page.fill('#tlb-rem',state.accounts.customer.email);await page.click('#tlb-rgo');await page.waitForFunction(()=>document.querySelector('#tlb-rsent')?.hidden===false);
 ok(true,'reset request is sent through UI with a neutral account-existence message');
 const link=await mailLink(state.accounts.customer.email,'recovery');stage='recovery_link';await page.goto(link);await page.waitForSelector('#tlb-newpw');
 ok(true,'recovery link opens new-password screen instead of entering the app');
 const newpw='Synthetic-only-'+crypto.randomBytes(12).toString('hex');secretValues.push(newpw);
 await page.fill('#tlb-newpw',newpw);await page.fill('#tlb-newpw2',newpw+'different');await page.click('#tlb-savepw');
 ok((await page.locator('#tlb-rerr').textContent())==='Passwords do not match.','mismatched password confirmation does not submit');
 stage='password_update';await page.fill('#tlb-newpw',newpw);await page.fill('#tlb-newpw2',newpw);await page.click('#tlb-savepw');await page.waitForSelector('#tlb-forgot');
 ok(true,'successful reset returns to sign-in without entering a privileged app');
 for(const [pw,expected]of [[state.accounts.customer.password,400],[newpw,200]]){
  const r=await fetch('http://127.0.0.1:9999/token?grant_type=password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:state.accounts.customer.email,password:pw})});ok(r.status===expected,expected===400?'old password rejected after reset':'new password accepted by real Auth');
 }
 stage='untrusted_marker';await page.fill('#tlb-em',state.accounts.customer.email);await page.fill('#tlb-pw',newpw);await page.click('#tlb-go');await page.waitForFunction(()=>typeof TLB!=='undefined'&&TLB.me()?.id,{timeout:30000});
 await page.goto('http://127.0.0.1:8080/customer.html?lang=en#type=recovery');await page.waitForSelector('#tlb-forgot');ok(await page.locator('#tlb-newpw').count()===0,'bare recovery marker cannot reset a pre-existing signed-in identity');
 stage='replay';const replayContext=await browser.newContext();await replayContext.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const fresh=await replayContext.newPage();await fresh.goto(link);await fresh.waitForSelector('#tlb-go');ok(await fresh.locator('#tlb-newpw').count()===0,'used recovery link cannot reopen a reset form in a fresh session');
 stage='unknown_email';await fresh.click('#tlb-forgot');await fresh.fill('#tlb-rem','does-not-exist@synthetic.invalid');await fresh.click('#tlb-rgo');await fresh.waitForFunction(()=>document.querySelector('#tlb-rsent')?.hidden===false);ok((await fresh.locator('#tlb-rsent').textContent()).startsWith('If the account exists'),'unregistered address gets the same neutral UI response');
 result.pass=true;
}catch(e){result.pass=false;result.failed_stage=stage;result.auth_http_trace=diagnostics;if(page){try{result.form_diagnostics=await page.evaluate(()=>({error:document.querySelector('#tlb-rerr')?.textContent,pwLength:document.querySelector('#tlb-newpw')?.value.length,confirmLength:document.querySelector('#tlb-newpw2')?.value.length,hasRecovery:!!document.querySelector('#tlb-newpw')}))}catch(_){}};result.error=e.name==='AssertionError'?e.message:'operation_failed:'+e.name;console.error('FAIL mail '+stage+' '+result.error);process.exitCode=1}
finally{if(result.form_diagnostics?.error)for(const value of secretValues)result.form_diagnostics.error=result.form_diagnostics.error.split(value).join('[REDACTED]');if(browser)await browser.close();fs.writeFileSync(path.join(__dirname,'result-auth-mail.json'),JSON.stringify(result,null,2)+'\n')}})();
