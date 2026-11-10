export const required=Object.freeze(['publicCI','privateDB','hostedRBAC','roleE2E','storageRevocation','providerRecovery','safariDevice','sqlQA']);
export function evaluate(commit,evidence){
 const issues=[];
 if(!/^[a-f0-9]{40}$/.test(commit||''))issues.push('invalid_commit');
 const object=evidence&&typeof evidence==='object'&&!Array.isArray(evidence)?evidence:{};
 for(const name of required){const x=object[name];if(!x||x.status!=='passed'||x.commit!==commit||typeof x.evidence!=='string'||!x.evidence.trim()||x.kind!=='actual')issues.push(name);}
 return {status:issues.length?'BLOCKED':'REQUIRES_INDEPENDENT_REVIEW',eligible:issues.length===0,productionReady:false,issues};
}
