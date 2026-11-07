from pathlib import Path
import json,csv,re,collections
base=Path(__file__).resolve().parents[1]
rows=json.loads((base/'acceptance-plan/asvs-5.0.0-implementation-test-plan.json').read_text())
actions={}
for line in (Path(__file__).parent/'triage-actions.tsv').read_text().splitlines():
 i,c,n,m=line.split('\t');actions[i]=(c,n,m)
labels={'N':'executable_now','T':'additional_test_needed','B':'external_blocked'}
# External dependency descriptions identify the barrier to complete acceptance;
# they do not prohibit independent source review or preparation.
manual=set('V6.2.1 V6.2.2 V6.2.3 V6.2.5 V6.2.9 V6.3.7 V6.4.1 V6.4.3 V6.4.5 V6.4.6 V6.5.1 V6.5.5 V6.5.6 V6.5.8 V6.6.2 V6.6.3 V7.2.4 V7.4.3 V7.5.1 V7.5.2 V10.4.2 V10.4.3 V10.4.9 V10.6.2 V10.7.1 V10.7.2 V10.7.3 V16.3.1'.split())
policy=set('V2.3.5 V3.5.4 V6.1.2 V6.2.11 V6.4.4 V7.1.1 V7.1.2 V7.3.2 V7.5.3 V8.1.4 V8.2.4 V8.4.2 V10.3.5 V10.4.4 V10.4.13 V10.4.14 V10.4.16 V11.1.1 V11.1.4 V11.2.2 V13.1.4 V14.1.2 V14.2.4 V14.2.7 V15.1.1 V15.2.1'.split())
prod=set('V4.3.2 V13.4.2 V13.4.4 V15.2.3'.split())
alerts={'V6.3.5','V16.4.3'}
refs={
'V1.1.2':['source-review/findings.md','source-review/xss-local-proof.json'],
'V1.2.3':['source-review/findings.md','source-review/xss-local-proof.json'],
'V1.2.4':['continuation23/dynamic-sql.json','continuation23/UNIFIED-STATUS.md'],
'V1.3.6':['continuation23/dynamic-sql.json','continuation23/edge-functions.json','continuation23/UNIFIED-STATUS.md'],
'V2.3.3':['functional-sql/finance-valid-report.md'],
'V2.3.4':['concurrency21/README.md','concurrency21/review.json','functional-sql/finance-valid-report.md'],
'V3.4.3':['csp19/REPORT.md','csp19/deployed-curl-safe.json'],
'V3.4.7':['csp19/REPORT.md','csp19/deployed-curl-safe.json'],
'V3.7.5':['auth-compatibility/ACCEPTANCE.md','continuation22/REPORT.md'],
'V5.2.1':['CURRENT-RESUME.md'],
'V5.2.2':['CURRENT-RESUME.md'],
'V5.2.6':['CURRENT-RESUME.md'],
'V5.3.2':['continuation21/proof-ui.json','session-revocation/proof-operation-results.json'],
'V6.4.3':['auth-compatibility/ACCEPTANCE.md','auth-compatibility/recovery.cjs','continuation23/mfa-state.json'],
'V6.8.4':['continuation21/finance-mfa-results.json'],
'V7.4.1':['session-revocation/lifecycle-http-14.json','continuation21/REPORT.md'],
'V8.2.1':['rpc-continuation/REPORT.md','continuation21/REPORT.md'],
'V8.2.2':['continuation21/proof-ui.json','session-revocation/proof-operation-results.json'],
'V8.3.1':['continuation22/table-surface.json','continuation22/policies.json'],
'V8.3.2':['continuation23/role-lifecycle-result.json','continuation23/cleanup.json','finance-session-after-21.json','continuation21/finance-mfa-results.json'],
'V11.5.1':['continuation22/REPORT.md','continuation22/request-id-compat.cjs'],
'V14.3.3':['csp19/REPORT.md','CURRENT-RESUME.md'],
'V15.1.2':['supply-chain/CONTINUATION-18.md'],
'V15.2.4':['supply-chain/CONTINUATION-18.md'],
'V16.3.1':['continuation21/monitoring.json','continuation23/mfa-state.json'],
'V16.4.3':['continuation21/monitoring.json','operations/INCIDENT-RESPONSE.md'],
}
for key in ['V1.1.2','V1.2.1','V1.2.3']:
 refs.setdefault(key,[]).extend(['continuation24/source-review/REPORT.md','continuation24/source-review/customer-handler-results.json','continuation24/source-review/customer-handler-after.json'])
for key in ['V14.3.1','V7.4.1']:
 refs.setdefault(key,[]).extend(['continuation24/data-crypto/REPORT.md','continuation24/data-crypto/passive-signout-before.json','continuation24/data-crypto/passive-signout-after.json'])
refs.setdefault('V14.3.1',[]).extend(['continuation24/data-crypto/proof-late-resolution-before.json','continuation24/data-crypto/proof-epoch-after.json'])
def resolve(x):
 x=x.strip().strip("[]'\" ")
 if 'security-20261107/' in x:x=x.split('security-20261107/',1)[1]
 if (base/x).is_file():return 'security-20261107/'+x
 return None
def external(i):
 if i=='V2.3.4':return ('Owner + automatic approval boundary','Persistent setup was rejected and latest owner instruction explicitly prohibits using permanent finance records to bypass the block. A separately approved disposable multi-connection target/fixture design is needed; do not retry rejected setup.','No real money; paid target not authorized; no cost quote obtained.','Review prepared lock/interleaving assertions and preserve prior overlap evidence; no new persistent rows.')
 if i=='V3.7.5':return ('Owner/device test operator','Actual older iPhone/Android devices or an expressly authorized real-device service are unavailable.','No paid device service authorized.','Maintain capability test plan and .22 secure-ID evidence without declaring device compatibility.')
 if i in alerts:return ('Owner + alert service administrator','Approved recipient/channel and supported delivery integration are missing; user must authorize the destination for a labelled synthetic incident.','Integration cost unknown; no paid activation or outbound message authorized by merely writing the plan.','Map available event fields and prepare a redacted synthetic trigger/acknowledgement checklist.')
 if i in prod:return ('Owner/provider evidence custodian','Requirement explicitly references production, which is outside direct-access authorization; obtain approved configuration evidence instead of probing it.','Separate production approval would be required for live access; none assumed.','Inspect the isolated test analogue and document the evidence-transfer limit.')
 if i in manual:return ('Owner/security test account operator','User-mediated secure credential/factor entry and/or a controlled deliverable synthetic mailbox is required. Current synthetic factor count0 and .invalid email do not provide it.','No protected credential changes, real email/codes or paid delivery service without explicit approval; no secrets in chat.','Review current UI/server flow and prepare exact success/replay/expiry cases without enrolling a factor or sending mail.')
 if i in policy:return ('Owner; provider administrator where delegated','Acceptance depends on an unapproved policy, scope or architecture decision. Prepare options from current behavior; do not silently alter customer login, accounting, roles or production.','Cost and implementation impact require scoped review; no paid service or policy change authorized by this triage.','Document current behavior and the minimum decision needed; test already-authorized mechanisms independently.')
 if i=='V5.4.3':return ('Owner/storage provider administrator','No verified malware-scanning facility or approved isolated scanner test exists.','Scanner pricing unknown; paid activation prohibited without approval.','Inventory upload routes/types and document scanner integration boundary; do not upload real malware.')
 if i in {'V6.2.4','V6.2.12'}:return ('Owner/Supabase administrator','Need actual provider password-screening capability/configuration and user-controlled synthetic entry; leaked-password protection currently reported disabled.','Feature availability/cost not approved; no plan upgrade.','Review nonsecret provider controls and preserve advisor evidence; do not change five protected credentials.')
 if i=='V7.4.5':return ('Owner/Supabase administrator + automatic approval boundary','Broad Auth deletion was rejected; only the dedicated synthetic scope is applied. A supported scoped termination mechanism and approved target scope are required.','No global logout, signing-key rotation or bypass of tool rejection.','Review current scoped revocation and prepare retained-token/multi-session evidence requirements.')
 return ('Relevant hosting/Auth/storage/provider administrator','Required provider-owned configuration, assurance or isolated test capability is not available through current application-source/DB evidence. Obtain the specific evidence named in next_action.','Provider cost unknown; no paid features, production changes or infrastructure stress authorized.','Inspect available application-side configuration and record exactly where provider evidence begins; do not mark the whole row blocked from preparatory work.')
out=[]
for r in rows:
 if r['status']!='غير مختبر':continue
 i=r['req_id'];c,n,m=actions[i]
 raw=r.get('evidence_files',[]);raw=[raw] if isinstance(raw,str) else raw
 rr=[]
 for v in raw:
  for fragment in re.split(r';',str(v)):
   z=resolve(fragment)
   if z:rr.append(z)
 for v in refs.get(i,[]):
  z=resolve(v)
  if z:rr.append(z)
 owner='Application/security implementer';dependency='No external dependency established for the next scoped action.';cost='No new paid service or production permission required for the stated scoped action.';independent=n
 if c=='T':dependency='Prepare a dedicated synthetic/local/rollback fixture or permitted session to execute this untested case. This is technical test preparation, not automatically an external blocker.'
 if c=='B':owner,dependency,cost,independent=external(i)
 evidence=r.get('evidence','').strip() or 'No requirement-specific executed evidence linked in the canonical row; existing chapter work must not be treated as coverage of this requirement.'
 if i=='V8.3.2':evidence+=' .21 finance revoked-session and AAL tests plus .23 same-session staff deactivation/permission-removal test are retained; do not repeat them unchanged.'
 if i in {'V1.1.2','V1.2.1','V1.2.3'}:evidence+=' C24-CLIENT-01 local actual-renderer regression: entity-decoded inline-handler marker executed before; actual repaired renderer preserves 7/7 arguments with zero markers. Full persisted lower-role attack path and complete output-sink inventory remain untested; source publication attribution belongs to root.'
 if i=='V14.3.1':evidence+=' C24 local regressions prove stale proof-response suppression through epoch invalidation and immediate passive-signout UI hiding with deferred reload. Actual browser navigation completion, cross-tab events and all data cleanup remain untested; entire requirement stays untested.'
 if i=='V7.4.1':evidence+=' C24 passive-signout regression preserves remote-signout-failure warning and tests error/rejection/throw paths; this does not prove provider token revocation.'
 if i=='V11.5.1':evidence+=' .22 UUIDv4 compatibility fix is an idempotency-identifier result, not ≥128-bit secret entropy evidence.'
 if i in {'V7.4.1','V16.5.1','V16.2.5'}:evidence+=' Root reported new local .23-candidate boot-error signout and raw-RPC-error repairs during this review; source publication and final evidence file association are pending root consolidation. Do not treat this report as independent retest.'
 out.append({'req_id':i,'level':r['L'],'chapter':r['chapter_name'],'official_requirement':r['req_description'],'status_preserved':r['status'],'classification':labels[c],'existing_evidence_summary':evidence,'evidence_refs_verified_local':list(dict.fromkeys(rr)),'legacy_evidence_refs_raw':raw,'missing_coverage':m,'next_action':n,'independent_work_now':independent,'external_dependency':dependency,'dependency_owner':owner,'cost_or_permission':cost,'closure_rule':'Remain untested until this complete requirement is covered; partial evidence, source mechanisms and applicability hypotheses do not constitute a pass.','source_baseline':'Site .22 4c78c739cd65c53746b07db6426cf5f66f178d8a; root may supersede after current source repair publication.'})
assert len(out)==331 and len({x['req_id'] for x in out})==331
folder=Path(__file__).parent
(folder/'asvs-331-triage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
with (folder/'asvs-331-triage.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in x.items()} for x in out)
counts=dict(collections.Counter(x['classification'] for x in out))
chapters={}
for x in out:chapters.setdefault(x['chapter'],collections.Counter())[x['classification']]+=1
summary={'total':331,'classification_counts':counts,'chapters':{k:dict(v) for k,v in chapters.items()},'canonical_matrix_unchanged':True,'excluded':{'failed':['V6.3.3','V7.4.2'],'not_applicable':'12 V17 requirements remain as already classified by root'},'quality_limits':['Triage is not execution or acceptance; no database/browser/provider calls were performed by this agent.','Each untested requirement was assigned a distinct action and missing-coverage statement from its official text; categories describe the next scoped action, not guaranteed closure feasibility.','External-blocked rows retain an independent preparation action; no claim that all technical work is exhausted.','OAuth/SAML/LDAP/archives and other conditional technology rows remain untested until applicability is evidenced; no assumed non-applicability.','Provider-owned controls and production-only requirements are not inferred from test source.','Root-reported new fixes need final source/evidence association before acceptance; canonical status remains unchanged.']}
(folder/'TRIAGE-SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(counts))
