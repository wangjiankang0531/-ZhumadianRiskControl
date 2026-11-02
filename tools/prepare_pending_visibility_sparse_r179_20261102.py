from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';OLD=W/'r33-project-header-candidate-r1/bundle';OUT=W/'r34-pending-visibility-candidate-r1';TX=R/'work/r34tx-r1';G=R/'_g/Application';F=W/'avatar-full-r157'
assert not OUT.exists()and not TX.exists();J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes());enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists();assert J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r78/result.json')['allPassed'] and J(R/'work/event_delivery_consistency_20261030/full-controller-r163/prepared-r78/frontend-restored.json')['passed']
source=T/'original_public_test_update_r34_20261102.py';spec=importlib.util.spec_from_file_location('r32_avatar_delta',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');oldraw=(OLD/'payload/release-manifest.json').read_bytes();oldqraw=(OLD/'payload/payload-manifest.json').read_bytes();assert digest(oldraw)=='330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13';assert digest(oldqraw)==old['payloadManifestSHA256']
roots={'security_pc':F/'security_pc/build/dist','emergency_pc':W/'workflow-pending-visibility-r178/dist'};oldroots={'security_pc':F/'security_pc/build/dist','emergency_pc':W/'project-header-home-r167/dist'};front={};bodies={}
for role,root in roots.items():
 for p in root.rglob('*'):
  if not p.is_file():continue
  n='frontend/'+role+'/'+p.relative_to(root).as_posix();raw=p.read_bytes();pin={'bytes':len(raw),'sha256':digest(raw)};front[n]=pin
  if oldq['files'].get(n)!=pin:bodies[n]=raw
assert len(front)==1174
q=copy.deepcopy(oldq);q['files']={n:p for n,p in q['files'].items()if not n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))};q['files'].update(front)
release=copy.deepcopy(old);release[m.R34_PENDING_FIELD]=copy.deepcopy(m.R34_PENDING_CONTRACT);release.update(publicTestRevision='20261102-R34-emergency-exact-pending-operator-visibility',publicAccepted=False)
control='tools/original_public_test_update.py';bodies[control]=source.read_bytes();release['controllerFiles'][control]=sha(source);bodies['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(release)
removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldq['files'].items()if n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))and n not in q['files']}
plan=copy.deepcopy(J(OLD/'update-manifest.json'));plan.update(updateId='20261102-R34-emergency-pending-visibility-from-exact-R33',acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],newReleaseSHA256=digest(bodies['release-manifest.json']),oldPayloadFiles={n:oldq['files'][n]for n in bodies if n in oldq['files']},legacyEntrySHA256={},removedFrontendFiles=removed,files={n:{'bytes':len(b),'SHA256':digest(b)}for n,b in bodies.items()})
assert bodies and removed and sum(map(len,bodies.values()))<32*1024**2;assert not any(n.startswith('frontend/security_pc/')for n in set(bodies)|set(removed))
baseline={}
for n in set(bodies)|set(removed):
 if n=='release-manifest.json':raw=oldraw
 elif n=='payload-manifest.json':raw=oldqraw
 elif n==control:raw=(T/'original_public_test_update_r33_20261102.py').read_bytes()
 elif n in oldq['files']:
  role=n.split('/')[1];raw=(oldroots[role]/n.split('/',2)[2]).read_bytes();assert len(raw)==oldq['files'][n]['bytes']and digest(raw)==oldq['files'][n]['sha256']
 else:continue
 baseline[n]=raw
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(b)}for n,b in bodies.items()};changes.update({n:{'before':p['SHA256'],'after':None}for n,p in removed.items()})
peak=sum(map(len,baseline.values()))*20+sum(map(len,bodies.values()))*3;free=shutil.disk_usage(R).free;assert peak<1024**3 and free>peak+1024**3;OUT.mkdir();TX.mkdir();put(OUT/'storage-plan.json',enc({'estimatedAdditionalPeakBytesUpperBound':peak,'freeBytesBefore':free,'GISOriginalAssetsDependenciesOrDatabaseCopied':False}))
bundle=OUT/'bundle'
for n,b in bodies.items():put(bundle/'payload'/n,b)
put(bundle/'update-manifest.json',enc(plan));put(OUT/'changes.json',enc(changes))
app=OUT/'contract-Application';put(app/'payload-manifest.json',oldqraw);put(app/'release-manifest.json',oldraw)
required={**m.risk_backend_rows(old,oldq),**m.R23_ASYNC_ROWS,m.R24_TASK_CLASS:m.R24_TASK_PIN,**m.R25_MATERIAL_ROWS,**m.R26_TEAM_SOURCE,**m.R26_TEAM_ROWS}
for n,p in required.items():raw=(G/n).read_bytes();assert len(raw)==p['bytes']and digest(raw)==p['sha256'];put(app/n,raw)
for n,pin in old['controllerFiles'].items():raw=((T/'original_public_test_update_r33_20261102.py')if n==control else G/n).read_bytes();assert digest(raw)==pin;put(app/n,raw)
contracts=['r32_avatar_bundle_contract','risk_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','material_bundle_contract','team_bundle_contract','workflow_bundle_contract']
assert all(getattr(m,n)(app,bundle,plan,old,release,q)for n in contracts)
cases=[]
def negative(label,mutate):
 p,o,r,n=map(copy.deepcopy,[plan,old,release,q]);mutate(p,o,r,n)
 try:accepted=m.r32_avatar_bundle_contract(app,bundle,p,o,r,n)
 except ValueError as e:cases.append({'case':label,'passed':True,'refusal':str(e)});return
 assert not accepted,'R32_BAD_COMPOSITION_ACCEPTED:'+label;cases.append({'case':label,'passed':True,'refusal':'descriptor-absent-not-accepted'})
negative('avatar-descriptor-missing',lambda p,o,r,n:r.pop(m.R34_PENDING_FIELD))
for field,value in [('revision','other'),('componentSHA256','0'*64),('adapterSHA256','0'*64),('exactCurrentUserProcessAndOperatorMembership',False),('pendingLookupFailureDoesNotOfferApproval',False),('originalAuthAuditAPIsAndInitiatorRulesRetained',False),('independentBeforeAddsignOpinionFixed',True)]:negative('descriptor-'+field,lambda p,o,r,n,f=field,v=value:r[m.R34_PENDING_FIELD].__setitem__(f,v))
for role in roots:negative('compiled-'+role+'-manifest-pin',lambda p,o,r,n,k=role:r[m.R34_PENDING_FIELD]['frontends'][k].__setitem__('manifestSHA256','0'*64))
nonfront=[m.R31_NATIVE_CLASS,m.R24_TASK_CLASS,'private/server-configuration.json','payload/business/application.jar']
for name in nonfront:negative('retained-payload-'+Path(name).name,lambda p,o,r,n,k=name:n['files'][k].__setitem__('sha256','0'*64))
negative('drop-retained-project-header-home-contract',lambda p,o,r,n:r.pop(m.R33_HEADER_FIELD))
negative('drop-reusable-native-default-session',lambda p,o,r,n:o.pop(m.R31_NATIVE_FIELD))
negative('change-other-controller',lambda p,o,r,n:r['controllerFiles'].__setitem__(m.R23_JOB,'0'*64))
negative('wrong-updater-base',lambda p,o,r,n:o['controllerFiles'].__setitem__(control,'0'*64))
negative('wrong-candidate-updater',lambda p,o,r,n:r['controllerFiles'].__setitem__(control,'0'*64))
negative('additional-accepted-release',lambda p,o,r,n:p['acceptedOldReleases'].__setitem__('0'*64,{}))
negative('legacy-entry-added',lambda p,o,r,n:p['legacyEntrySHA256'].__setitem__('legacy.cmd',['0'*64]))
negative('extra-unchanged-backend-transport',lambda p,o,r,n:p['files'].__setitem__(m.R24_TASK_CLASS,{'bytes':m.R24_TASK_PIN['bytes'],'SHA256':m.R24_TASK_PIN['sha256']}))
changed=next(n for n in bodies if n.startswith('frontend/emergency_pc/'));oldchanged=next(iter(plan['oldPayloadFiles']));deleted=next(iter(removed))
negative('missing-required-frontend',lambda p,o,r,n:p['files'].pop(changed))
negative('wrong-frontend-transport-hash',lambda p,o,r,n:p['files'][changed].__setitem__('SHA256','0'*64))
negative('missing-old-frontend-pin',lambda p,o,r,n:p['oldPayloadFiles'].pop(oldchanged))
negative('missing-obsolete-removal',lambda p,o,r,n:p['removedFrontendFiles'].pop(deleted))
negative('wrong-obsolete-removal-bytes',lambda p,o,r,n:p['removedFrontendFiles'][deleted].__setitem__('bytes',1))
negative('changed-retained-release-contract',lambda p,o,r,n:r.__setitem__(m.R27_POOL_FIELD,{}))
negative('premature-full-public-acceptance',lambda p,o,r,n:r.__setitem__('publicAccepted',True))
put(OUT/'contract-negative-cases.json',enc(cases))
triggers=[('normal',None),('first-path',1),('fourth-path',4),('emergency-asset-removal',next(n for n in removed if n.startswith('frontend/emergency_pc/'))),('updater-write',control),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json')];recoveries=[]
for label,trigger in triggers:
 case=TX/label;app=case/'Application'
 for n,b in baseline.items():put(app/n,b)
 m.backup_code(app,case/'backup',changes);count=[0];caught=False
 def after(name):
  count[0]+=1
  if name==trigger or count[0]==trigger:raise RuntimeError('OWN_R32_FAULT_'+label)
 try:m.replace_code(app,bundle,changes,after_each=after)
 except RuntimeError as e:assert trigger is not None and str(e)=='OWN_R32_FAULT_'+label;caught=True
 assert caught==(trigger is not None)
 if trigger is None:assert all((app/n).read_bytes()==b for n,b in bodies.items())and all(not(app/n).exists()for n in removed)
 m.restore_code(app,case/'backup',changes);assert all((app/n).read_bytes()==b for n,b in baseline.items())and all(not(app/n).exists()for n in changes if n not in baseline)
 row={'scenario':label,'pathsBeforeRecovery':count[0],'allOriginalBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)};put(case/'result.json',enc(row));recoveries.append(row)
case=TX/'foreign-drift';app=case/'Application'
for n,b in baseline.items():put(app/n,b)
m.backup_code(app,case/'backup',changes);n=next(n for n in baseline if n.startswith('frontend/emergency_pc/'));put(app/n,b'own unrelated edit\n');snapshot={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
try:m.restore_code(app,case/'backup',changes)
except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_EDIT_OVERWRITTEN')
assert snapshot=={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
proof={'schema':'xnby.r179.exact-pending-visibility-sparse-update.v1','allCompositionContractsPassed':True,'contracts':contracts,'negativeCases':len(cases),'allNegativeCasesRefused':True,'oldPublicReleaseSHA256':digest(oldraw),'newReleaseSHA256':plan['newReleaseSHA256'],'newUpdaterSHA256':sha(source),'updateManifestSHA256':sha(bundle/'update-manifest.json'),'writes':len(bodies),'oldAssetRemovals':len(removed),'totalInstallPaths':len(changes),'writeBytes':sum(map(len,bodies.values())),'recoveryScenarios':recoveries,'foreignDriftRefusedBeforeAnyRestore':True,'allOther19ControlsAndEveryNonFrontendPayloadByteRetained':True,'fullProgramPreflightPassed':False,'newUpdaterActualLifecyclePassed':False,'publicUploadedOrInstalled':False,'fullCloneReady':False}
put(OUT/'result.json',enc(proof));print(json.dumps({k:v for k,v in proof.items()if k!='recoveryScenarios'}))
