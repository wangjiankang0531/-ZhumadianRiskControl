"""Offer verified material import paths for bounded manual use; protect data after handoff."""
from pathlib import Path
import ctypes,datetime,hashlib,importlib.util,json,os,socket,subprocess,time
R=Path('D:/Project/Zhumadian');A=R/'_f/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r130'
read=lambda p:json.loads(p.read_bytes());dump=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
assert not(A.parent/'user-manual-protected.json').exists()
assert read(C/'r11/result.json')['allPassed']and read(C/'r11/controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']
assert read(C/'r11/material-browser/browser-terminal.json')['chromeExitCode']==0
assert read(C/'r11/material-browser/result.json')['productFixed']
prepared=read(C/'candidate-install-r2/controller-fixture-ready.json');assert hashlib.sha256((A/'release-manifest.json').read_bytes()).hexdigest()==prepared['releaseSHA256']
root=C/'material-manual-preview-r1';assert not root.exists();root.mkdir()
class Memory(ctypes.Structure):
 _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('pageTotal',ctypes.c_ulonglong),('pageAvailable',ctypes.c_ulonglong),('virtualTotal',ctypes.c_ulonglong),('virtualAvailable',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
memory=Memory();memory.length=ctypes.sizeof(memory);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
assert memory.available>4*1024**3,'OWN_MANUAL_PREVIEW_NEEDS_AVAILABLE_MEMORY'
dump(root/'memory-before.json',{'availablePhysicalBytes':memory.available,'requiredMinimumBytes':4*1024**3})
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
j=module('own_manual_job',A/'tools/original_server_windows_job.py');m=module('own_manual_health',A/'tools/original_public_test_update.py')
with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
duration=7200;env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME','PYTHONHOME','PYTHONPATH']}
args=[str(A/'runtime/python/python.exe'),'-I','-B',str(A/'tools/serve_original_server_release.py'),'--application',str(A),'--release-manifest-sha256',prepared['releaseSHA256'],'--gateway-port',str(port),'--callback-overlay',str(A/'payload/callback-overlay/20261026-password-identity/manifest.json'),'--callback-overlay-sha256','91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb']
process=None;job=None
with(root/'controller.private.log').open('wb')as log:
 try:
  process=subprocess.Popen(args,cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(process)
  dump(root/'started.json',{'pid':process.pid,'gatewayPort':port,'syntheticManualPreviewOnly':True,'durationSecondsAfterReady':duration})
  print('OWN_MATERIAL_MANUAL_PREVIEW_STARTING',flush=True);end=time.monotonic()+570;next_message=0;row=None
  while time.monotonic()<end:
   pointer=A/'UserData/OriginalServer/current-run.json'
   if pointer.exists():
    current=read(pointer)
    if current.get('controllerPID')==process.pid and current.get('ready')and current.get('gatewayPort')==port:row=current;break
   assert process.poll()is None,'OWN_MATERIAL_PREVIEW_EXITED_BEFORE_READY'
   if time.monotonic()>next_message:print('OWN_MATERIAL_PREVIEW_WAITING_FOR_READY',flush=True);next_message=time.monotonic()+25
   time.sleep(.2)
  assert row is not None,'OWN_MATERIAL_PREVIEW_READY_TIMEOUT';m.health(A,row,gateway_port=port)
  for relative,pin in read(R/'work/event_delivery_consistency_20261030/full-controller-r128/material-excel-candidate-r1/candidate.json')['classFiles'].items():m.check_file(Path(row['run'])/'b/classes',relative,pin['sha256'],pin['bytes'])
  cfg=read(A/'private/server-configuration.json');password=cfg['seedRootPassword'];cfg=None
  private=root/'private';private.mkdir();account=private/'本机物资体验账号.txt'
  account.write_text('仅限本轮本机虚构物资体验环境，不适用于公网。菜单中的审批流程不在本次体验验收范围。\n账号：own_operator_a\n口令：'+password+'\n验证码：0000\n',encoding='utf-8');password=None
  now=datetime.datetime.now().astimezone();descriptor={'schema':'xnby.local.material.manual-preview.v1','ready':True,
   'controllerPID':process.pid,'gatewayPort':port,'url':'http://127.0.0.1:'+str(port)+'/zhumadian/emergency/emergencyResources/materials',
   'readyAt':now.isoformat(),'estimatedExpiresAt':(now+datetime.timedelta(seconds=duration)).isoformat(),
   'loginFile':str(account),'application':str(A),'run':row['run'],'initialSyntheticDataOnly':True,'manualInputMayContainUserData':True,
   'verifiedPaths':['native-required-validation','real-dictionary-and-department-choice','actual-map-mouse-coordinate-selection','native-add-save-and-detail-readback','latest-request-result-and-loading-order-protection','actual-template-download','three-row-upload-and-normal-role-api-readback','3001-row-failure-rolls-back-all-new-rows','fake-format-rejected','header-only-noop','repeated-import-appends','late-original-success-keeps-new-dialog-open','accepted-data-survives-restart'],
   'nativeManualAddDepartmentCoordinateAndDetailAccepted':True,'nativeEditDeleteAndExportAcceptedInPriorR129':True,'actualBaseMapImageryAndRealZhumadianGISAccepted':False,'completeMaterialModuleAccepted':False,'realNangangRolesOrCompleteModuleAccepted':False,'publicOrFormalChanged':False}
  dump(A.parent/'user-manual-protected.json',{'protectedForUserManualUse':True,'initialSyntheticDataOnly':True,'manualInputMayContainUserData':True,
   'readyDescriptor':str(root/'ready.json'),'noAutomatedBusinessReadsWritesReplacementOrDataCloneAfterHandoff':True})
  dump(root/'ready.json',descriptor);print(json.dumps({'ready':True,'url':descriptor['url'],'expires':descriptor['estimatedExpiresAt'],'loginFile':str(account)},ensure_ascii=False),flush=True)
  try:process.wait(timeout=duration)
  except subprocess.TimeoutExpired:pass
 finally:
  if process:
   if process.poll()is None:
    pointer=A/'UserData/OriginalServer/current-run.json'
    if pointer.exists():
     current=read(pointer)
     if current.get('controllerPID')==process.pid:
      run=Path(current['run']);assert run.parent==A/'UserData/OriginalServer/runs';(run/'stop-requested.txt').write_text('OWN_NORMAL_PREVIEW_STOP\n',encoding='ascii')
   while process.poll()is None:
    try:process.wait(timeout=20)
    except subprocess.TimeoutExpired:print('OWN_MATERIAL_PREVIEW_NORMAL_STOP_PENDING_NO_FORCE',flush=True)
   if job:
    while job.active_processes():time.sleep(.5)
    job.close()
   dump(root/'terminal.json',{'exitCode':process.returncode,'allActualDescendantsZero':True,'forceTerminationUsed':False})
   p=root/'ready.json'
   if p.exists():value=read(p);value['ready']=False;value['normalExitCode']=process.returncode;dump(p,value)
   print('OWN_MATERIAL_MANUAL_PREVIEW_NORMALLY_STOPPED',flush=True)
