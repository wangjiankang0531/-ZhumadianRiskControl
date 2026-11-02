from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent;W=R/'work/user_feedback_20261031';S=W/'r31-task-unified-candidate-r2/bundle/payload';F=W/'avatar-full-r157';O=T/'original_public_test_update_r32_20261102.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();source=T/'original_public_test_update_r31_20261102.py';assert sha(source)=='477cd84dbce633623db7d31d6bf1504455cbcfa114f44c53f4c5d751a00d64ac'
def manifest(rows,role):
 selected={n:p for n,p in rows.items()if n.startswith('frontend/'+role+'/')};return {'files':len(selected),'manifestSHA256':hashlib.sha256(json.dumps(selected,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
old=J(S/'payload-manifest.json')['files'];new={}
for role,root in [('security_pc',F/'security_pc/build/dist'),('emergency_pc',F/'emergency_pc/dist')]:
 for p in root.rglob('*'):
  if p.is_file():new['frontend/'+role+'/'+p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
contract={'revision':'two-native-portal-avatar-source-and-original-default-icon-v1','headerSourceSHA256':'5ec7dd353ecdd6e67880d8940e2c42f80dc12e7a851174b1390f9eb80a726bb3','normalizerSourceSHA256':sha(T/'frontend/OriginalHeaderAvatarSource.ts'),'frontends':{role:manifest(new,role)for role in ['security_pc','emergency_pc']},'originalLoginSDKAndPermissionsRetained':True,'originalMissingPhotoRestored':False}
constants='R32_AVATAR_FIELD = "nativePortalAvatarSource"\nR32_AVATAR_CONTRACT = '+repr(contract)+'\nR32_OLD_FRONTENDS = '+repr({role:manifest(old,role)for role in ['security_pc','emergency_pc']})+'\nR32_OLD_UPDATER_SHA = "'+sha(source)+'"\n\n'
s=source.read_text(encoding='utf-8');anchor='def runtime_pool_declared(release):';assert s.count(anchor)==1;s=s.replace(anchor,constants+(V/'r32_avatar_contract.py.in').read_text(encoding='utf-8')+anchor,1)
anchor="n.startswith('frontend/emergency_pc/')";assert s.count(anchor)==7;s=s.replace(anchor,'r32_frontend_scope(n, release, payload)')
anchor='    risk_bundle_contract(app, bundle, plan, old, release, payload)';assert s.count(anchor)==1;s=s.replace(anchor,'    r32_avatar_bundle_contract(app, bundle, plan, old, release, payload)\n\n'+anchor,1)
anchor="    source = check_file(bundle / 'payload', name, candidate['controllerFiles'][name])";assert s.count(anchor)==1;s=s.replace(anchor,"    source_root = bundle / 'payload' if name in plan['files'] else app\n\n    source = check_file(source_root, name, candidate['controllerFiles'][name])",1)
ast.parse(s);O.write_text(s,encoding='utf-8');D=R/'Document/Deployment/public_test_avatar_r32_20261102';assert not D.exists();D.mkdir();(D/'updater-source-preparation.json').write_text(json.dumps({'priorUpdaterSHA256':sha(source),'newUpdaterSHA256':sha(O),'exactFrontendContract':contract,'oldCompiledFrontendPins':{role:manifest(old,role)for role in ['security_pc','emergency_pc']},'allPriorLifecycleAndCodeRecoveryFunctionsUnchanged':True,'candidateBudgetSupportsExactRetainedParameterSource':True,'contractAndWholeProgramTestsNotYetRun':True,'publicChanged':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'newUpdaterSHA256':sha(O),'fullContractTestsNotYetPassed':True,'publicChanged':False}))
