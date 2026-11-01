"""Exercise only the new R22 preflight/readiness contracts using real pinned code files."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';S=R/'work/user_feedback_20261031/r22-risk-candidate-r3';W=R/'work/user_feedback_20261031/r22-updater-contract-r1';assert not W.exists();W.mkdir()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda v:(json.dumps(v,indent=2)+'\n').encode()
source=T/'original_public_test_update_r22_20261101.py';spec=importlib.util.spec_from_file_location('own_r22_contract',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
app=W/'Application';bundle=W/'bundle';app.mkdir();bundle.mkdir();old=read(S/'r21-base-release-manifest.json');payload=read(S/'r21-base-payload-manifest.json');release=copy.deepcopy(old);release['riskUnitNativeSessionCandidate']=m.R22_RISK_SESSION_REVISION
operations=read(S/'candidate-stage.json')['backendOperations'];plan={'files':{}}
for item in operations:
 name=item['relative'];raw=(S/'payload'/name).read_bytes();dest=bundle/'payload'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);payload['files'][name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};plan['files'][name]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
factory='payload/business/run-template/classes/META-INF/spring.factories';oldFactory=(R/'work/user_feedback_20261031/public-r21-template-recovery-r1'/factory).read_bytes();newFactory=(bundle/'payload'/factory).read_bytes();factoryPath=app/factory;factoryPath.parent.mkdir(parents=True);factoryPath.write_bytes(oldFactory)
payloadRaw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payloadRaw).hexdigest();(app/'release-manifest.json').write_bytes(enc(release));(app/'payload-manifest.json').write_bytes(payloadRaw)
checks=[]
def check(label,fn,denied=False):
 caught=False
 try:fn()
 except (ValueError,FileNotFoundError):caught=True
 assert caught==denied,label
 checks.append({'case':label,'expectedRefusal':denied,'passed':True})
def contract(p=None,r=None,q=None,o=None):return m.risk_bundle_contract(app,bundle,p or plan,o or old,r or release,q or payload)
check('fresh-exact-five-file-upgrade',contract)
r=copy.deepcopy(release);r.pop('riskUnitNativeSessionCandidate');check('missing-explicit-candidate',lambda:contract(r=r),True)
r=copy.deepcopy(release);r['riskUnitNativeSessionCandidate']='other';check('foreign-candidate',lambda:contract(r=r),True)
for name in m.R22_BACKEND_ROWS:
 p=copy.deepcopy(plan);p['files'].pop(name);check('incomplete-transport-'+name,lambda p=p:contract(p=p),True)
 q=copy.deepcopy(payload);q['files'][name]['sha256']='0'*64;check('wrong-declared-pin-'+name,lambda q=q:contract(q=q),True)
 q=copy.deepcopy(payload);q['files'].pop(name);check('missing-declared-pin-'+name,lambda q=q:contract(q=q),True)
 p=copy.deepcopy(plan);p['files'][name]['SHA256']='0'*64;check('wrong-transport-pin-'+name,lambda p=p:contract(p=p),True)
for label,raw in [('missing-prior-initializer',oldFactory.replace(b'xnby.replica.OriginalTransactionObservation,',b'')),('duplicated-prior-initializer',oldFactory.replace(b'xnby.replica.OriginalTransactionObservation,',b'xnby.replica.OriginalTransactionObservation,xnby.replica.OriginalTransactionObservation,')),('already-added-with-old-release',newFactory)]:
 factoryPath.write_bytes(raw);check(label,contract,True);factoryPath.write_bytes(oldFactory)
factoryPath.write_bytes(newFactory);check('retained-r22-factory',lambda:contract(p={'files':{}},o=release));factoryPath.write_bytes(oldFactory)
run=app/'UserData/OriginalServer/runs/j1';business=run/'b';business.mkdir(parents=True)
for item in operations:
 sub=item['relative'].split('run-template/',1)[1];dest=business/sub;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((S/'payload'/item['relative']).read_bytes())
owner='own-r22-readiness-contract';(business/'server-owner.properties').write_text('schema=zhumadian.original.server.owner.v1\nownerId='+owner+'\n',encoding='ascii');row={'run':str(run),'ownerId':owner}
report=business/'native-session-guard-ready.properties';actual=(R/'work/event_delivery_consistency_20261030/full-business-main-r101/closed-short-runtime-evidence/native-session-guard-ready.properties').read_bytes();report.write_bytes(actual)
check('actual-r101-marker-and-five-runtime-files',lambda:m.native_session_ready(app,row))
expected=m.marker(report)
for key in expected:
 altered=dict(expected);altered[key]='foreign-or-false';report.write_text(''.join(k+'='+v+'\n'for k,v in altered.items()),encoding='ascii');check('wrong-marker-'+key,lambda:m.native_session_ready(app,row),True)
for label,raw in [('duplicate-key',actual.replace(b'guardCount=1',b'guardCount=1\nguardCount=1')),('extra-key',actual+b'unknown=true\n'),('oversized-marker',b'a'*4097),('non-ascii-marker',actual+b'\xff')]:
 report.write_bytes(raw);check(label,lambda:m.native_session_ready(app,row),True)
report.unlink();check('missing-marker',lambda:m.native_session_ready(app,row),True);report.write_bytes(actual)
check('wrong-current-owner',lambda:m.native_session_ready(app,dict(row,ownerId='foreign')),True)
check('foreign-current-run',lambda:m.native_session_ready(app,dict(row,run=str(W/'other/j1'))),True)
for item in operations:
 file=business/item['relative'].split('run-template/',1)[1];raw=file.read_bytes();file.write_bytes(raw+b'X');check('drift-runtime-'+file.name,lambda:m.native_session_ready(app,row),True);file.write_bytes(raw)
bad=copy.deepcopy(release);bad['payloadManifestSHA256']='0'*64;(app/'release-manifest.json').write_bytes(enc(bad));check('wrong-runtime-manifest',lambda:m.native_session_ready(app,row),True);(app/'release-manifest.json').write_bytes(enc(release))
legacyPayload=read(S/'r21-base-payload-manifest.json');legacy=copy.deepcopy(old);legacyRaw=enc(legacyPayload);legacy['payloadManifestSHA256']=hashlib.sha256(legacyRaw).hexdigest();(app/'payload-manifest.json').write_bytes(legacyRaw);(app/'release-manifest.json').write_bytes(enc(legacy));check('old-r21-does-not-require-new-marker',lambda:m.native_session_ready(app,row))
oldTree=ast.parse((S/'retained-r21-updater.py').read_text(encoding='utf-8'));newTree=ast.parse(source.read_text(encoding='utf-8'));before={n.name:ast.dump(n,include_attributes=False)for n in oldTree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};after={n.name:ast.dump(n,include_attributes=False)for n in newTree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};assert all(after[k]==v for k,v in before.items()if k not in ['load_bundle','health']);assert set(after)-set(before)=={'risk_declared','risk_bundle_contract','native_session_ready'}
result={'schema':'xnby.r22.updater-contract-checks.v1','checks':len(checks),'cases':checks,'allPassed':True,'actualR101ReadyMarkerUsed':True,'allFiveTestedCandidateBytesUsed':True,'oldUnchangedFunctions':len(before)-2,'realRuntimeOrPublicChanged':False,'sourceSHA256':sha(source)};(W/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:result[k]for k in ['checks','allPassed','oldUnchangedFunctions','realRuntimeOrPublicChanged','sourceSHA256']}))
