from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');H=V/'event_crud_r1004';OLD=V/'event_crud_r985';BASE=R/'Document/Deployment/event_result_owned_full_r1003_20261105'
J=lambda p:json.loads(Path(p).read_bytes());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert J(R/'Document/Deployment/event_result_runtime_r1000_20261105/verified-metadata-contract-r1002.json')['passed']
assert not H.exists()
s=(V/'prepare_event_crud_r979.py').read_text('utf8').replace('r979','r1004').replace('R979','R1004').replace('ev979','ev1004').replace('ecfg979','ecfg1004')
s=s.replace('event_crud_native_r1004_20261104','event_crud_native_r1004_20261105')
anchor="SOURCE=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104'";assert s.count(anchor)==1;s=s.replace(anchor,"SOURCE=R/'Document/Deployment/event_result_owned_full_r1003_20261105'")
anchor="assert sha(SOURCE/'full-source-and-restore-plan.private.json')=='a44203be5562ea30a565752e9b4ec2081b2f5b9d577f7455bc7497a348a9fc7d'";assert s.count(anchor)==1
s=s.replace(anchor,"assert sha(SOURCE/'full-source-and-restore-plan.private.json')=="+repr(sha(BASE/'full-source-and-restore-plan.private.json')))
s=s.replace("assert sha(source)==J(OLD/'ledger-source-pins-r960.json')['files'].get(str(source),sha(source))","# Derivative configuration algorithm fixed by the new source manifest.")
p=V/'prepare_event_crud_r1004.py';assert not p.exists();p.write_text(s,encoding='utf8')
r=subprocess.run(['python',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
for name in ['verify_event_crud_r985.mjs','event_crud_probe_r985.py','test_event_receiver_configuration_r985.py']:
 s=(OLD/name).read_text('utf8').replace('r985','r1004').replace('R985','R1004').replace('ev985','ev1004').replace('ecfg985','ecfg1004')
 if name.endswith('.mjs'):
  # Create and normal edit once, then exercise a sibling delete before leaving
  # this live editor. The restart phase is read-only, including missing detail.
  anchor=" }else{\n  context=";assert s.count(anchor)==1;s=s.replace(anchor," }\n if(w.phase==='first-start'){\n  context=")
  anchor=" }\n await Promise.all([...reads]);";assert s.count(anchor)==1
  restart=''' }else{
  context=JSON.parse(await fs.readFile(contextFile,'utf8'));
  if(context.phase!=='delete-and-false-save-verified'||context.nonce!==w.nonce||context.name!==name)throw Error('EXACT_POSTFIX_DELETED_EVENT_CONTEXT');
  check((await exactRecord()).length===0,'normal-restart-does-not-resurrect-originally-deleted-own-event');
  await search(false);await until(()=>evaluate('!!document.querySelector(".el-table__body-wrapper")'));
  check(!await evaluate(`!!(${rowExpr})`),'normal-original-list-refresh-excludes-deleted-record');
  check(await api('/eventInfo/getById?id='+encodeURIComponent(context.id))===null,'original-detail-api-returns-null-for-deleted-own-event');
  await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/response/edit?type=edit&id='+encodeURIComponent(context.id)},session);
  await until(()=>evaluate('document.body.textContent.includes("详情未取得，请返回列表刷新后重试。")'));
  check(true,'missing-detail-displays-failure-without-overwriting-form-or-JS-exception');
  check(count('/eventInfo/save')===0&&count('/eventInfo/updateById')===0&&count('/eventInfo/removeById')===0,'restart-and-invalid-detail-readback-mutation-requests-zero');
 }
 await Promise.all([...reads]);'''
  s=s.replace(anchor,restart)
  sibling=(V/'event_crud_r990/verify_event_crud_r990.mjs').read_text('utf8');start=sibling.index('async function openNormalSibling()');end=sibling.index('async function close()',start)
  helper=sibling[start:end];s=s.replace('async function close()',helper+'async function close()')
  s=s.replace("{path:u.pathname,method:v.params.request.method}","{path:u.pathname,method:v.params.request.method,secondaryContext:v.sessionId!==firstSession}")
  s=s.replace("await attach();await search();let before=","await openNormalSibling();await search();await until(()=>requests.some(r=>r.secondaryContext&&r.path.endsWith('/oauth/CurrentUser')&&r.normalOwnUserMatched));let before=")
  s=s.replace('2026-11-04 09:00:00','2026-11-05 09:00:00')
 (H/name.replace('r985','r1004')).write_text(s,encoding='utf8')
p=H/'home_transfer_health_r906.py';s=p.read_text('utf8').replace('exactPublicR47ProgramAndControllerBytes','exactPreparedR48ProgramAndControllerBytes').replace("plan['onlyPrivateConfigurationManifestPinAdapted']","plan['onlySixOwnedDockReceiverURLsAndPrivateManifestPinsAdapted']").replace('exactR47UpdaterAndCoreUsed','exactPreparedR48UpdaterAndCoreUsed');p.write_text(s,encoding='utf8')
p=H/'run_event_crud_r1004.py';s=p.read_text('utf8');end=s.index('"""',3)+3
s='"""Exact prepared R48, one new own repair-validation event: positive create/edit, native sibling cancel/delete, false-save input retention, then normal restart/missing detail readback. No public deployment or sparse publisher acceptance is claimed."""'+s[end:]
s=s.replace("query=\"(Get-CimInstance","query=\"$ErrorActionPreference='Stop'; (Get-CimInstance")
s=s.replace('# This original-backend candidate never changes private application configuration.','# Restore only this attempt\'s six owned notification URLs and manifest pins first.')
s=s.replace("'actualIISTLSOrPublicAccepted':False,","'actualIISTLSOrPublicAccepted':False,'newR48SparsePublisherAcceptedByThisRun':False,'exactPreparedR48ProgramsUsed':True,")
ast.parse(s);p.write_text(s,encoding='utf8')
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_event_crud_r1004.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
D=R/'Document/Deployment/event_crud_native_r1004_20261105'
(D/'prepared-postfix-r1004.json').write_text(json.dumps({'preparedOnly':True,'exactPreparedR48ProgramSource':True,'oneNewOwnedRepairValidationRecordOnly':True,'oldDeletedR985EventWillNotBeReadRestoredOrReused':True,'firstLifecycleHasAllNormalUIMutationsSecondLifecycleReadOnly':True,'sparsePublicUpdateContractNotExercisedByThisLifecycle':True,'runtimeAccepted':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'runtimeAccepted':False,'originalAppCodeConfigOrDataChanged':False}))
