from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';OLD=R/'work/r39-plan-runtime-unified-r1/original-r37-contract';O=R/'work/r39-plan-runtime-unified-r1/r37';D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103/r37';J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
source=T/'original_public_test_update_r39_plan_runtime_r337.py';spec=importlib.util.spec_from_file_location('r38_composition',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bundle=O/'bundle';plan=J(bundle/'update-manifest.json');old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');new=J(bundle/'payload/release-manifest.json');q=J(bundle/'payload/payload-manifest.json')
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
app=O/'contract-Application';assert not app.exists();put(app/'release-manifest.json',(OLD/'payload/release-manifest.json').read_bytes());put(app/'payload-manifest.json',(OLD/'payload/payload-manifest.json').read_bytes())
assert m.r38_unified_bundle_contract(app,bundle,plan,old,new,q)
cases=[]
def negative(label,mutate):
 p,o,n,payload=map(copy.deepcopy,[plan,old,new,q]);mutate(p,o,n,payload)
 try:m.r38_unified_bundle_contract(app,bundle,p,o,n,payload)
 except (ValueError,KeyError)as e:cases.append({'case':label,'refused':str(e)});return
 raise AssertionError('INVALID_UNIFIED_COMPOSITION_ACCEPTED:'+label)
negative('missing-mapper-descriptor',lambda p,o,n,q:n.pop(m.R38_MAPPER_FIELD))
negative('missing-frontend-descriptor',lambda p,o,n,q:n.pop(m.R38_FRONTEND_FIELD))
negative('missing-static-descriptor',lambda p,o,n,q:n.pop(m.R37_STATIC_FIELD))
for key in ['revision','defaultResourcePattern','expectedOriginalXMLResources','expectedOriginalXMLStatements','onlyWhenNoExplicitMapperLocations','originalSQLBytesUnchanged','newDatasourceOrDDL']:
 negative('mapper-contract-'+key,lambda p,o,n,q,k=key:n[m.R38_MAPPER_FIELD].__setitem__(k,'foreign'))
for key in ['encodedResponseBytesPreserved','contentEncodingAndVaryForwarded','successfulHashedAssetsImmutable','htmlBusinessErrorsAndNonHashedResourcesNotLongCached']:
 negative('static-contract-'+key,lambda p,o,n,q,k=key:n[m.R37_STATIC_FIELD].__setitem__(k,False))
for key in [m.R24_PARAMETER,'tools/original_public_test_update.py','iis/App_Code/XnbyReferenceProxy.cs','tools/original_project_branding.py',m.R23_CONTROLLER]:
 negative('wrong-control-source-'+key,lambda p,o,n,q,k=key:n['controllerFiles'].__setitem__(k,'0'*64))
for key in ['payload/business/application.jar',m.R31_NATIVE_CLASS,'private/server-configuration.json',next(k for k in q['files']if k.startswith('frontend/security_pc/'))]:
 negative('changed-retained-payload-'+key,lambda p,o,n,q,k=key:q['files'][k].__setitem__('sha256','0'*64))
negative('extra-payload-class',lambda p,o,n,q:q['files'].__setitem__('payload/business/foreign.jar',{'bytes':1,'sha256':'0'*64}))
negative('changed-compiled-frontend',lambda p,o,n,q:q['files'][next(iter(m.R38_FRONTEND_ROWS))].__setitem__('sha256','0'*64))
negative('extra-accepted-release',lambda p,o,n,q:p['acceptedOldReleases'].__setitem__('0'*64,{}))
negative('old-controller-metadata-drift',lambda p,o,n,q:o['controllerFiles'].__setitem__(m.R23_CONTROLLER,'0'*64))
negative('old-release-metadata-drift',lambda p,o,n,q:o.__setitem__('publicAccepted',True))
negative('wrong-old-IIS-proxy',lambda p,o,n,q:p.__setitem__('iisProxySHA256','0'*64))
negative('wrong-old-IIS-legacy-pin',lambda p,o,n,q:p['legacyEntrySHA256'].__setitem__('iis/App_Code/XnbyReferenceProxy.cs',['0'*64]))
negative('extra-legacy-path',lambda p,o,n,q:p['legacyEntrySHA256'].__setitem__('iis/web.config',['0'*64]))
negative('extra-install-path',lambda p,o,n,q:p['files'].__setitem__('frontend/security_pc/foreign.js',{'bytes':1,'SHA256':'0'*64}))
negative('missing-required-parameter',lambda p,o,n,q:p['files'].pop(m.R24_PARAMETER))
negative('missing-required-live-IIS',lambda p,o,n,q:p['files'].pop('iis/App_Code/XnbyReferenceProxy.cs'))
negative('wrong-parameter-transport',lambda p,o,n,q:p['files'][m.R24_PARAMETER].__setitem__('SHA256','0'*64))
negative('wrong-updater-transport',lambda p,o,n,q:p['files']['tools/original_public_test_update.py'].__setitem__('SHA256','0'*64))
negative('missing-obsolete-removal',lambda p,o,n,q:p['removedFrontendFiles'].pop(next(iter(p['removedFrontendFiles']))))
negative('extra-obsolete-removal',lambda p,o,n,q:p['removedFrontendFiles'].__setitem__('frontend/security_pc/keep.js',{'bytes':1,'SHA256':'0'*64}))
negative('wrong-old-payload-pin',lambda p,o,n,q:p['oldPayloadFiles'][next(iter(p['oldPayloadFiles']))].__setitem__('sha256','0'*64))
negative('drop-original-history',lambda p,o,n,q:n.pop(m.R36_HISTORY_FIELD))
negative('drop-pool-policy',lambda p,o,n,q:n.pop(m.R27_POOL_FIELD))
negative('reuse-old-workflow-parameter-pin',lambda p,o,n,q:n.__setitem__(m.R24_WORKFLOW_FIELD,copy.deepcopy(o[m.R24_WORKFLOW_FIELD])))
negative('wrong-callback-overlay',lambda p,o,n,q:p.__setitem__('callbackOverlay','foreign/manifest.json'))
negative('premature-public-acceptance',lambda p,o,n,q:n.__setitem__('publicAccepted',True))
negative('wrong-unified-revision',lambda p,o,n,q:n.__setitem__('publicTestRevision','foreign'))

negative('missing-plan-runtime-descriptor',lambda p,o,n,q:n.pop(m.R39_PLAN_FIELD))
for key in ['schema','javaMajor','originalJarPlanClassSHA256','candidateSourceSHA256','schemaOrOriginalJarOrAuthenticationChanged']:
 negative('plan-contract-'+key,lambda p,o,n,q,k=key:n[m.R39_PLAN_FIELD].__setitem__(k,'foreign'))
negative('missing-plan-class-payload',lambda p,o,n,q:q['files'].pop(m.R39_PLAN_CLASS))
negative('wrong-plan-class-payload',lambda p,o,n,q:q['files'][m.R39_PLAN_CLASS].__setitem__('sha256','0'*64))
negative('missing-plan-class-transport',lambda p,o,n,q:p['files'].pop(m.R39_PLAN_CLASS))
negative('wrong-plan-class-transport',lambda p,o,n,q:p['files'][m.R39_PLAN_CLASS].__setitem__('SHA256','0'*64))
negative('foreign-class-install-path',lambda p,o,n,q:p['files'].__setitem__('payload/business/run-template/classes/foreign/Plan.class',{'bytes':1,'SHA256':'0'*64}))
negative('different-single-accepted-base',lambda p,o,n,q:p.__setitem__('acceptedOldReleases',{'0'*64:next(iter(p['acceptedOldReleases'].values()))}))

put(D/'composition-negative-cases.json',enc(cases))
oldfrontroot=W/'personal-workflow-routes-r195/dist'
def resolve(n,pin):
 candidates=[OLD/'payload'/n,R/'_g/Application'/n,R/'Application'/n]
 if n.startswith('frontend/emergency_pc/'):candidates.insert(0,oldfrontroot/n.split('/',2)[2])
 if n=='iis/App_Code/XnbyReferenceProxy.cs':
  return resolve('deploy/iis_original/App_Code/XnbyReferenceProxy.cs',pin)
 for p in candidates:
  if p.is_file()and sha(p.read_bytes())==pin:return p.read_bytes()
 raise ValueError('ORIGINAL_TRANSACTION_SOURCE_UNRESOLVED:'+n)
changes={};baseline={};bodies={}
for n,row in plan['files'].items():
 b=(bundle/'payload'/n).read_bytes();assert sha(b)==row['SHA256'];bodies[n]=b
 before=old['controllerFiles'].get(n)or oldq['files'].get(n,{}).get('sha256')
 if n=='release-manifest.json':before=sha((OLD/'payload/release-manifest.json').read_bytes())
 elif n=='payload-manifest.json':before=old['payloadManifestSHA256']
 elif n in plan['legacyEntrySHA256']:before=plan['legacyEntrySHA256'][n][0]
 changes[n]={'before':before,'after':row['SHA256']}
 if before:baseline[n]=resolve(n,before)
for n,row in plan['removedFrontendFiles'].items():changes[n]={'before':row['SHA256'],'after':None};baseline[n]=resolve(n,row['SHA256'])
assert len(changes)==364 and len(plan['files'])==187
peak=(2*sum(map(len,baseline.values()))+sum(map(len,bodies.values())))*16+8*1024**2;assert peak<512*1024**2 and shutil.disk_usage(R).free>peak+2*1024**3
root=O/'transactions';assert not root.exists();results=[]
triggers=[('normal',None),('first-change',1),('first-obsolete-removal',next(iter(plan['removedFrontendFiles']))),('middle-change',len(changes)//2),('branding-write','tools/original_project_branding.py'),('live-IIS-write','iis/App_Code/XnbyReferenceProxy.cs'),('plan-class-write',m.R39_PLAN_CLASS),('parameter-write',m.R24_PARAMETER),('updater-write','tools/original_public_test_update.py'),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json'),('last-change',len(changes))]
def seed_case(case):
 a=case/'Application'
 for n,b in baseline.items():put(a/n,b)
 for n in ['private/own-kept.txt','UserData/own-kept.txt','uploads/own-kept.txt']:put(a/n,b'own-kept-sentinel\n')
 return a
def snapshot(a):return{n:sha((a/n).read_bytes())if(a/n).is_file()else None for n in changes}
for label,trigger in triggers:
 case=root/label;a=seed_case(case);m.backup_code(a,case/'before',changes);count=[0];caught=False
 def after(n):
  count[0]+=1
  if n==trigger or count[0]==trigger:raise RuntimeError('OWN_UNIFIED_WRITE_FAULT')
 try:m.replace_code(a,bundle,changes,after_each=after)
 except RuntimeError as e:assert str(e)=='OWN_UNIFIED_WRITE_FAULT'and trigger is not None;caught=True
 assert caught==(trigger is not None)
 if trigger is None:assert snapshot(a)=={n:r['after']for n,r in changes.items()}
 m.restore_code(a,case/'before',changes);assert snapshot(a)=={n:r['before']for n,r in changes.items()}
 assert all((a/n).read_bytes()==b'own-kept-sentinel\n'for n in ['private/own-kept.txt','UserData/own-kept.txt','uploads/own-kept.txt'])
 results.append({'scenario':label,'all364OriginalPathStatesRestored':True,'changesBeforeRestore':count[0],'privateUserDataAndUploadSentinelsKept':True})
for label,n in [('foreign-IIS','iis/App_Code/XnbyReferenceProxy.cs'),('foreign-parameter',m.R24_PARAMETER),('foreign-plan-class',m.R39_PLAN_CLASS),('foreign-new-frontend',next(k for k,v in changes.items()if v['before']is None))]:
 case=root/label;a=seed_case(case);m.backup_code(a,case/'before',changes);put(a/n,b'own-unrelated-foreign-edit\n');snap=snapshot(a)
 try:m.restore_code(a,case/'before',changes)
 except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
 else:raise AssertionError('FOREIGN_FILE_OVERWRITTEN:'+n)
 assert snapshot(a)==snap;results.append({'scenario':label,'foreignDriftRefusedBeforeAnyRestore':True})

readyroot=O/'plan-readiness';assert not readyroot.exists()
readyapp=readyroot/'Application';runtime=readyroot/'runtime';readycases=[]
def seed_ready(rel,pay,installed=True,running=True):
 rel=copy.deepcopy(rel);raw=enc(pay);rel['payloadManifestSHA256']=sha(raw)
 put(readyapp/'payload-manifest.json',raw);put(readyapp/'release-manifest.json',enc(rel))
 for path,include in [(readyapp/m.R39_PLAN_CLASS,installed),(runtime/'b'/m.R39_PLAN_CLASS.split('/run-template/',1)[1],running)]:
  if path.exists():path.unlink()
  if include:put(path,bodies[m.R39_PLAN_CLASS])
seed_ready(new,q)
assert m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})['installedAndRuntimeClassCopyMatched']
readycases.append({'case':'declared-installed-and-runtime-copy-exact','passed':True})
for label in ['missing-runtime-copy','foreign-runtime-copy','foreign-installed-copy','missing-descriptor','wrong-class-pin','wrong-jar-pin']:
 rel,pay=copy.deepcopy(new),copy.deepcopy(q)
 if label=='missing-descriptor':rel.pop(m.R39_PLAN_FIELD)
 if label=='wrong-class-pin':pay['files'][m.R39_PLAN_CLASS]['sha256']='0'*64
 if label=='wrong-jar-pin':pay['files']['payload/business/application.jar']['sha256']='0'*64
 seed_ready(rel,pay,running=label!='missing-runtime-copy')
 if label=='foreign-runtime-copy':put(runtime/'b'/m.R39_PLAN_CLASS.split('/run-template/',1)[1],b'own-foreign-runtime-bytecode')
 if label=='foreign-installed-copy':put(readyapp/m.R39_PLAN_CLASS,b'own-foreign-installed-bytecode')
 try:m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})
 except ValueError as e:readycases.append({'case':label,'refused':str(e)})
 else:raise AssertionError('PLAN_READINESS_BOUNDARY_ACCEPTED:'+label)
seed_ready(old,oldq,installed=False,running=False)
assert m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})is None
readycases.append({'case':'unchanged-original-base-requires-no-plan-override','passed':True})
assert len(readycases)==8
put(D/'plan-readiness-boundaries-r340.json',enc({'passed':True,'cases':readycases,'onlyOwnedFileFixtures':True,'notActualJVMOrServerHealthAcceptance':True}))

proof={'passed':True,'negativeCompositionCases':len(cases),'allNegativeCasesRefused':True,'writes':187,'removals':177,'changePaths':364,'normalAndFaultFileRecoveryCases':results,'peakAllocationBudgetBytes':peak,'updaterSHA256':sha(source.read_bytes()),'updateManifestSHA256':sha((bundle/'update-manifest.json').read_bytes()),'realProcessesSQLDatabaseOrPublicTouched':False,'newUpdaterApplyUpdateTransactionExecuted':False,'actualFileBackupReplaceRestoreFunctionsExecuted':True,'planReadinessByteBoundaryScenarios':len(readycases),'baselineVariant':'R37'}
put(D/'composition-and-recovery.json',enc(proof));put(O/'changes.json',enc(changes));print(json.dumps({k:v for k,v in proof.items()if k!='normalAndFaultFileRecoveryCases'}))
