// Validates operator-supplied observations; does not authenticate evidence or call provider.
export function assessStorage(rows){
 const issues=[];
 if(!Array.isArray(rows))return{passed:false,providerFixProven:false,issues:['invalid_records']};
 for(const method of ['GET','HEAD','RANGE']){
  const found=rows.filter(r=>r?.method===method),r=found[0],allowed=method==='RANGE'?206:200;
  if(found.length!==1||!r||r.baseline!==allowed||r.control!==allowed||r.warmed!==true||r.revocationIndependentlyVerified!==true||typeof r.url!=='string'||!r.url||typeof r.tokenHash!=='string'||!r.tokenHash||r.revoked?.url!==r.url||r.revoked?.tokenHash!==r.tokenHash||![401,403,404].includes(r.revoked?.status)||r.revoked?.bytes!==0||![401,403,404].includes(r.outsider))issues.push(method);
 }
 return {passed:issues.length===0,providerFixProven:false,issues};
}
