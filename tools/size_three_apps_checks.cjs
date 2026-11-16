#!/usr/bin/env node
'use strict';
// TALABOT SIZE-7 approved three-app mobile-only CSS regressions; no network.
const fs=require('node:fs'),assert=require('node:assert/strict');
const read=p=>fs.readFileSync(p,'utf8');
const c=read('assets/size-three-apps-20261116/customer.css');
const m=read('assets/size-three-apps-20261116/merchant.css');
const d=read('assets/size-three-apps-20261116/driver.css');
const hc=read('customer.html'),hm=read('merchant.html'),hd=read('driver.html');
const originalDriver=read('assets/driver-a/driver-a.css');
const checks=[];
function check(name,fn){try{fn();checks.push(name);console.log('PASS '+name);}catch(e){console.error('FAIL '+name,e.message);process.exitCode=1;}}
check('SIZE_spec_tokens_applied',()=>{
 for(const [html,path] of [[hc,'customer'],[hm,'merchant'],[hd,'driver']])
  assert(html.includes('assets/size-three-apps-20261116/'+path+'.css'));
 assert(!read('admin.html').includes('size-three-apps-20261116'));
 assert(c.includes('h1{font-size:18px')&&c.includes('h2{font-size:15px'));
 assert(c.includes('.card{padding:14px}')&&c.includes('body{font-size:13px;line-height:1.4}'));
 assert(m.includes('padding-left:12px;padding-right:12px'));
 assert(m.includes('.card{padding:12px}')&&m.includes('padding-top:8px;padding-bottom:8px'));
 assert(d.includes('body{font-size:15px;line-height:21px}'));
 assert(d.includes('h1{font-size:20px;line-height:26px}')&&d.includes('h2{font-size:17px;line-height:23px}')&&d.includes('.card{padding:14px}'));
 assert(c.includes('@media (max-width:430px)')&&m.includes('@media (max-width:430px)')&&d.includes('@media (max-width:430px)'));
});
check('SIZE_touch_targets_ge_44',()=>{
 // Preserved 42px ordinary legacy button is owner-locked, not silently increased or reduced.
 assert(hc.includes('.btn{')&&hc.includes('height:42px'));
 assert(hc.includes('.btn.big{width:100%;height:46px'));
 assert(hm.includes('.b.s{')&&hm.includes('height:42px'));
 assert(m.includes('min-height:44px'));
 assert(originalDriver.includes('.nav>button{min-height:56px'));
 assert(originalDriver.includes('.a-dock .swp{height:62px'));
 assert(originalDriver.includes('.a-dock .swk{width:52px;height:52px'));
 assert(d.includes('body.a-mission .a-sheet.a-compact-card'));
 assert(originalDriver.includes('--a-headh:calc(52px + env(safe-area-inset-top,0px))'));
 for(const css of [c,m,d]) {
  assert(!/transform\s*:\s*scale\s*\(/i.test(css),'no global CSS scale');
  assert(!/(?:^|[;\s])zoom\s*:/i.test(css),'no CSS zoom');
  assert(!/#[a-f\d]{3,8}\b/ig.test(css),'no new hardcoded palette values');
 }
});
check('SIZE_protected_admin_untouched',()=>{
 assert(!hc.includes('assets/size-three-apps-20261116/merchant.css'));
 assert(!hm.includes('assets/size-three-apps-20261116/customer.css'));
 assert(!hd.includes('assets/size-three-apps-20261116/customer.css'));
 assert(!d.includes('height:60px'),'approved header already has 52px layout variable, avoid enlarging');
 assert(!d.includes('height:64px'),'no resurrected legacy header');
 assert(!m.includes('background:'),'brand color unchanged');
 assert(!c.includes('background:'),'brand color unchanged');
});
if(!process.exitCode) console.log('SIZE_SOURCE_GATES: 3/3 PASS');
