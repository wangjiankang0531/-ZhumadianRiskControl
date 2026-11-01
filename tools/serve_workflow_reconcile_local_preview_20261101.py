"""Bounded local manual preview, original six components and synthetic data only."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,socket,subprocess,time
R=Path('D:/Project/Zhumadian');A=R/'_e/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r123'
read=lambda p:json.loads(p.read_bytes());dump=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
assert read(C/'r9/result.json')['allPassed']and read(C/'r9/controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']
assert all(read(C/'r9'/('workflow-browser-'+a)/'browser-terminal.json')['normalBrowserClosed'] for a in ['operator','reviewer','operator-readback'])
assert read(C/'synthetic-database-prepared.json')['onlyOwnedSyntheticR114DatasetCopied']
prepared=read(C/'controller-fixture-ready.json');assert prepared['verifiedTaskGuardAnd19OriginalControlsWithTempCandidate']
assert hashlib.sha256((A/'release-manifest.json').read_bytes()).hexdigest()==prepared['releaseSHA256']
spec=importlib.util.spec_from_file_location('own_workflow_preview_nonterminating_job',A/'tools/original_server_windows_job.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=C/'workflow-reconcile-manual-preview-r1';assert not root.exists();root.mkdir()
with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
duration=7200;env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME','PYTHONPATH','PYTHONHOME']}
args=[str(A/'runtime/python/python.exe'),'-I','-B',str(A/'tools/serve_original_server_release.py'),'--application',str(A),'--release-manifest-sha256',prepared['releaseSHA256'],'--gateway-port',str(port),'--callback-overlay',str(A/'payload/callback-overlay/20261026-password-identity/manifest.json'),'--callback-overlay-sha256','91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb']
process=None;job=None;run=None
with(root/'controller.private.log').open('wb')as log:
 try:
  process=subprocess.Popen(args,cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=m.OwnedWindowsJob(process)
  dump(root/'started.json',{'pid':process.pid,'gatewayPort':port,'syntheticManualPreviewOnly':True,'durationSecondsAfterReady':duration})
  print('OWN_LOCAL_MANUAL_PREVIEW_STARTING',flush=True);end=time.monotonic()+570;next_progress=0
  while time.monotonic()<end:
   p=A/'UserData/OriginalServer/current-run.json'
   if p.exists():
    row=read(p)
    if row.get('controllerPID')==process.pid and row.get('gatewayPort')==port and row.get('ready'):run=Path(row['run']);break
   assert process.poll()is None,'OWN_MANUAL_PREVIEW_EXITED_BEFORE_READY'
   if time.monotonic()>next_progress:print('OWN_MANUAL_PREVIEW_WAITING_FOR_READY',flush=True);next_progress=time.monotonic()+25
   time.sleep(.2)
  assert run is not None
  config=read(A/'private/server-configuration.json');password=config['seedRootPassword'];config=None
  checker_spec=importlib.util.spec_from_file_location('own_preview_health',A/'tools/original_public_test_update.py');checker=importlib.util.module_from_spec(checker_spec);checker_spec.loader.exec_module(checker);checker.health(A,row,gateway_port=port)
  reader=read(C/'callback-reader.json');identity=read(A/'UserData/OriginalServer/installation.json')
  callback=subprocess.run([reader['java'],'-Xmx128m','-cp',reader['classpath'],'OwnWorkflowCallbackEndpointFixture',str(row['databasePort']),identity['databaseUUID'],str(A/'UserData/OriginalServer/database/data'),str(row['businessPort'])],input=password.encode(),capture_output=True,timeout=30,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
  assert callback.returncode==0,'OWN_MANUAL_CALLBACK_BINDING_FAILED'
  dump(root/'own-callback-binding.json',json.loads(callback.stdout.decode('utf-8')))
  private=root/'private';private.mkdir();account=private/'本机体验账号.txt'
  account.write_text('仅用于本轮本机虚构测试环境，不能用于公网。\n发起人账号：own_operator_a\n审批人账号：own_reviewer_b\n本机共同测试口令：'+password+'\n',encoding='utf-8');password=None
  now=datetime.datetime.now().astimezone();descriptor={'schema':'xnby.local.workflow-details.manual-preview.v1','ready':True,'controllerPID':process.pid,'gatewayPort':port,
   'url':'http://127.0.0.1:'+str(port)+'/zhumadian/emergency/workflow/startWithMeTwo','readyAt':now.isoformat(),
   'estimatedExpiresAt':(now+datetime.timedelta(seconds=duration)).isoformat(),'initialSyntheticDataOnly':True,'manualInputMayContainUserData':True,'publicOrFormalApplicationChanged':False,
   'loginFile':str(account),'application':str(A),'run':str(run),'stopRequest':str(run/'stop-requested.txt'),
   'userManualPreviewDoNotReuseForAutomatedWritesOrCleanupWhileLive':True,'frontendSourceRevision':'r6','nativeListsDetailsTaskReadOnlyAndInitiatorVerified':True,'singleApprovalUICallbackVerified':True,'responseLossAndQueryOnlyRecoveryVerified':True,'unprocessedRequestRetryVerified':True,'taskState2FilterVerified':True,'completeBusinessFlowNotYetAccepted':True}
  dump(A.parent/'user-manual-protected.json',{'protectedForUserManualUse':True,'initialSyntheticDataOnly':True,'manualInputMayContainUserData':True,'readyDescriptor':str(root/'ready.json'),'noAutomatedBusinessReadsWritesReplacementOrDataCloneAfterHandoff':True});dump(root/'ready.json',descriptor);print(json.dumps({'ready':True,'url':descriptor['url'],'estimatedExpiresAt':descriptor['estimatedExpiresAt'],'loginFile':str(account)},ensure_ascii=False),flush=True)
  try:process.wait(timeout=duration)
  except subprocess.TimeoutExpired:pass
 finally:
  if process:
   if process.poll()is None:
    p=A/'UserData/OriginalServer/current-run.json'
    if p.exists():
     row=read(p)
     if row.get('controllerPID')==process.pid:
      own_run=Path(row['run']);assert own_run.parent==A/'UserData/OriginalServer/runs';(own_run/'stop-requested.txt').write_text('OWN_NORMAL_PREVIEW_STOP\n',encoding='ascii')
   while process.poll()is None:
    try:process.wait(timeout=20)
    except subprocess.TimeoutExpired:print('OWN_PREVIEW_NORMAL_SHUTDOWN_PENDING_NO_FORCE',flush=True)
   if job:
    while job.active_processes():time.sleep(.5)
    job.close()
   dump(root/'terminal.json',{'controllerExitCode':process.returncode,'allActualDescendantsZero':True,'forceTerminationUsed':False})
   p=root/'ready.json'
   if p.exists():descriptor=read(p);descriptor['ready']=False;descriptor['normalExitCode']=process.returncode;dump(p,descriptor)
   print('OWN_LOCAL_PREVIEW_NORMALLY_STOPPED',flush=True)
