"""Verify the actual installed PC release without claiming old stopped previews healthy."""
from pathlib import Path
import argparse,ctypes,hashlib,json,sys,urllib.request
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';Q=Path('D:/Zqa20261025/Application');L=R/'work/event_disposal_lifecycle_20261029';B=R/'work/event_disposal_update_20261029';NEW='9fbc1db40a205414f0788c21d109ba966196ad178c04bb60195f46f99a0631b3';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def current():
 from run_original_inventory_ownership_probe import state
 import install_event_disposal_local_20261029 as installed
 c=state();actual=read(L/'result.json');assert actual['runtimeReady'] and actual['releaseSHA256']==NEW and c['controllerPID']==actual['controllerPID'] and c['run']==actual['run'] and sha(Q/'release-manifest.json')==NEW;u=installed.updater();u.health(Q,c,gateway_port=18891);team=u.emergency_team_observer_ready(Q,c);assert team['allEmergencyTeamMethodsAndManagerMatched'] and len(installed.prior.observation(c))==4;event=u.event_disposal_observer_ready(Q,c);assert event['allEventDisposalMethodsAndManagerMatched']
 baseline=read(L/'prepared.json')['baselineProjection'];assert read(L/'after-start/projection.private.json')['samples']==baseline['samples']
 for prefix,key in [('safety','permanentSafetyTables'),('team','permanentTeamTables'),('resource','permanentResourceTables'),('duty','permanentDutyTables'),('event','permanentEventTables')]:assert read(L/('after-start/'+prefix+'-tables.private.json'))['permanentThreeTables' if prefix=='duty' else 'permanentTwoTables']==baseline[key]
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_bool,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p;k.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)];k.CloseHandle.argtypes=[ctypes.c_void_p];images=[]
 for pid in [c['controllerPID'],*c['children'].values()]:
  h=k.OpenProcess(0x1000,False,pid);assert h;buf=ctypes.create_unicode_buffer(32768);size=ctypes.c_ulong(len(buf))
  try:assert k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size));image=Path(buf.value).resolve(strict=True);assert image.is_relative_to((Q/'runtime').resolve(strict=True));images.append({'PID':pid,'image':str(image)})
  finally:k.CloseHandle(h)
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));urls=['http://127.0.0.1:18891/zhumadian/home','http://127.0.0.1:18891/zhumadian/emergency/','http://127.0.0.1:18891/zhumadian/h5/'];st=read(A/'UserData/ConfirmedOperationsPreview_20261029/web-service.json')
 with opener.open(st['baseURL']+'/__preview_health',timeout=3) as response:h=json.load(response)
 assert h['owner']==st['owner'] and h['PID']==st['PID']==860 and h['packageManifestSHA256']==st['packageManifestSHA256']=='161a11c06e34390d2b29580b520a586889856076f2757da353e8716019e19bad' and not h['businessBackendConnected'];urls.extend(st['baseURL']+p for p in ['/','/security/?mode=candidate','/emergency/?mode=candidate','/responsibility/?mode=candidate'])
 new=read(A/'UserData/EventDisposalPreview_20261029/web-service.json');launch=read(A/'UserData/EventDisposalPreview_20261029/launch.json');assert new['owner']==launch['owner'] and new['PID']==launch['PID']==26136 and new['packageManifestSHA256']=='7d16bad01a7677ee7849fecc0834244eb14528d1e6607c7fd0230761583b0317' and sha(A/'tools/emergency_resource_preview_server.py')==new['serverSourceSHA256']
 with opener.open(new['baseURL']+'/__preview_health',timeout=3) as response:h=json.load(response)
 assert h['PID']==new['PID'] and h['owner']==new['owner'] and h['packageManifestSHA256']==new['packageManifestSHA256'] and not h['businessBackendConnected'];urls.extend(new['baseURL']+p for p in ['/','/disposal/?mode=candidate','/exercise/?mode=candidate'])
 for url in urls:
  with opener.open(url,timeout=10) as response:assert response.status==200
 return {'currentBS':Path(c['run']).name,'controllerPID':c['controllerPID'],'children':c['children'],'releaseSHA256':NEW,'databaseUUID':c['databaseUUID'],'sevenOwnedRuntimeImages':images,'nineSamplesAndElevenCompleteTablesUnchangedAtActualStart':True,'retainedAndEmergencyAndEventDisposalAdvisorMetadataMatched':True,'tenCurrentEntrypointsHTTP200':urls,'newPreviewOwnerAndManifestMatched':True,'eventOriginalFormPreviewOwnerAndManifestMatched':True,'activeLogRoot':str(L/'start'),'uniqueInstalledUpdateRoot':str(B),'codeBackup':actual['codeBackup'],'normalUserAuthenticatedPagesAndRolesPending':True,'oldStoppedPreviewServicesNotClaimedHealthy':True,'publicRuntimeChanged':False,'fullCloneReady':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);out=p.parse_args().report;assert not out.exists();v=current();out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(v))
