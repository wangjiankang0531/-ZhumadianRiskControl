"""Install one pinned local B/S update using normal owned stop/backup/start.

Preserves databases, uploads, credentials and IIS. No forced stop or blind retry.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,sys,uuid
W=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';Q=Path('D:/Zqa20261025/Application');ROOT=R/'work/bs_atomic_local_update_20261028';B=ROOT/'bundle';E=ROOT/'lifecycle'
PIN='1d6e286b983efb76ff3fdb1c9f2b164a1fa3c7bc044f6d0bc623980b1450ea3c';OLD='3f1ee528b0e2107da4aead4359786fdaf2d87cc7b43214d0822eca9a46c344cd';NEW='8b5d5bb1cbd98f00c371ba973328c6f0dbbf6cb8f04a25ab13e0a4a3da874c2a'
sys.path.insert(0,str(A/'tools'))
from run_original_inventory_ownership_probe import state
from verify_original_work_reservation_sql import run
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def updater():
 p=B/'payload/tools/original_public_test_update.py';s=importlib.util.spec_from_file_location('own_bs_atomic_updater',p);u=importlib.util.module_from_spec(s);s.loader.exec_module(u);return u
def projection(tag,current):
 deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');target=E/tag;target.mkdir();secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
 try:run(target,'read',[deps['java'],'-Xmx128m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-cp',str(E/'read-classes')+';'+deps['classpath'],'xnby.replica.OriginalAtomicUpdateReadProbe',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),target/'projection.private.json'],35,secret)
 finally:del secret
 report=read(target/'projection.private.json');assert report['readOnlyConnection'] and not report['businessMethodsAuthenticationOrWritesInvoked'];return report['samples']
def observe(current):
 folder=Path(current['run'])/'b';report=read(folder/'work-services-transaction-observation.json');old=read(folder/'transaction-bean-observation.json');pins=read(B/'build-result.json')['classSHA256']
 assert report['schema']=='xnby.work-services-transaction-observation.v1' and report['PID']==current['children']['business'] and report['run']==Path(current['run']).name and report['ownerIdSHA256']==hashlib.sha256(current['ownerId'].encode('ascii')).hexdigest()
 assert report['existingSingletonMetadataOnly'] and not report['businessMethodsInvoked'] and not report['SQLOrNetworkRequestsIssuedByObserver']
 for key,needle in [('reservation','/work/service/impl/WorkReservationBaseServiceImpl.class'),('thirdParty','/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class')]:
  group=report[key];assert group['allMethodsHaveMatchingTransactionAdvisor'] and len(group['services'])==1;bean=group['services'][0];assert bean['existingSingleton'] and bean['isAopProxy'] and bean['allMethodsHaveMatchingTransactionAdvisor'];expected=next(v for k,v in pins.items() if k.endswith(needle));assert bean['targetClassSHA256']==expected
 assert old['allThreeMethodsHaveMatchingTransactionAdvisor'] and old['existingTransactionManagerCount']>=1
 return {'workServices':report,'inventory':old}
def prepare():
 assert not E.exists();u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 current=state();assert current['controllerPID']==35292 and Path(current['run']).name=='j41';E.mkdir();(E/'tmp').mkdir();(E/'read-classes').mkdir()
 deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for p,pin in deps['inputPins'].items():assert sha(p)==pin['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];source=(W/'java' if (W/'java').is_dir() else W)/'OriginalAtomicUpdateReadProbe.java'
 run(E,'compile-read',[java.with_name('javac.exe'),'-J-Xmx192m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',E/'read-classes',source],35)
 baseline=projection('before',current)
 prepared={'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':PIN,'oldReleaseSHA256':OLD,'newReleaseSHA256':NEW,'oldControllerPID':current['controllerPID'],'oldOwnerId':current['ownerId'],'oldRun':current['run'],'oldStateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'databaseUUID':current['databaseUUID'],'identitySHA256':sha(Q/'UserData/OriginalServer/installation.json'),'configurationSHA256':sha(Q/'private/server-configuration.json'),'objectCredentialsSHA256':sha(Q/'UserData/OriginalServer/store-credentials.private.json'),'sourcePins':{str(p):sha(p) for p in [Path(__file__),source]},'compiledReadClassSHA256':sha(E/'read-classes/xnby/replica/OriginalAtomicUpdateReadProbe.class'),'baselineOwnSampleFingerprints':baseline,'files':len(changes),'codeBackupIncludesUserData':False,'preparedOnly':True}
 dump(E/'prepared.private.json',prepared);print(json.dumps({'prepared':True,'ownSampleGroups':5,'codeFiles':len(changes),'runtimeStopped':False}),flush=True)
def apply():
 prepared=read(E/'prepared.private.json');assert not (E/'apply-started.json').exists(),'NO_UNCHANGED_RETRY';u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 for p,pin in prepared['sourcePins'].items():assert sha(p)==pin
 assert sha(E/'read-classes/xnby/replica/OriginalAtomicUpdateReadProbe.class')==prepared['compiledReadClassSHA256']
 current=state();assert current['controllerPID']==prepared['oldControllerPID'] and current['ownerId']==prepared['oldOwnerId'] and current['run']==prepared['oldRun'] and sha(Q/'UserData/OriginalServer/current-run.json')==prepared['oldStateSHA256']
 dump(E/'apply-started.json',{'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':PIN});result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':PIN,'state':'PRECHECK_PASSED','runtimeReady':False,'publicChanged':False,'fullCloneReady':False};stopped=False;code_started=False;new=None;backup=Q/'UserData/OriginalBSUpdates'/str(uuid.uuid4())
 try:
  print('LOCAL_STOP: normal shutdown of j41; original data remains in place',flush=True);final=u.normal_stop(Q,OLD,current);dump(E/'old-normal-stop.json',final);stopped=True
  u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891)
  with u.server_lock(Q):
   u.backup_code(Q,backup,changes);result['codeBackup']=str(backup);code_started=True;u.replace_code(Q,B,changes)
  result['state']='CODE_APPLIED';dump(E/'result.private.json',result)
  for number in (1,2):
   folder=E/('start'+str(number));folder.mkdir();print('LOCAL_START_'+str(number)+': starting exact candidate '+NEW[:12],flush=True);new=u.launch(Q,NEW,folder,gateway_port=18891);u.health(Q,new,gateway_port=18891);live=state();assert live['controllerPID']==new['controllerPID'] and live['databaseUUID']==prepared['databaseUUID'];new=live
   for path,key in [(Q/'UserData/OriginalServer/installation.json','identitySHA256'),(Q/'private/server-configuration.json','configurationSHA256'),(Q/'UserData/OriginalServer/store-credentials.private.json','objectCredentialsSHA256')]:assert sha(path)==prepared[key],'EXISTING_DATA_IDENTITY_OR_CREDENTIAL_DRIFT'
   observation=observe(new);dump(folder/'actual-observers.private.json',observation);samples=projection('after-start'+str(number),new);assert samples==prepared['baselineOwnSampleFingerprints'],'OWN_ACCEPTANCE_SAMPLE_DATA_CHANGED_DURING_RESTART';dump(folder/'ready.private.json',{'controllerPID':new['controllerPID'],'run':new['run'],'releaseSHA256':NEW,'databaseUUID':new['databaseUUID'],'existingSampleGroupsUnchanged':5,'actualClassAndTransactionAdvisorMetadataVerified':True})
   if number==1:print('LOCAL_RESTART: same-data normal stop/start verification',flush=True);dump(folder/'normal-stop.json',u.normal_stop(Q,NEW,new));new=None
  result.update(state='LOCAL_READY_MANUAL_BROWSER_ACCEPTANCE_PENDING',runtimeReady=True,controllerPID=new['controllerPID'],run=new['run'],releaseSHA256=NEW,sameDataNormalRestartVerified=True,ownSampleGroupsUnchanged=5,actualServiceClassAndAdvisorMetadataVerified=True,actualHTTPBusinessRollbackAccepted=False,normalUserLoginPending=True,publicChanged=False)
  print('LOCAL_READY: candidate live; normal login and original-page verification pending',flush=True)
 except BaseException as error:
  result.update(state='STOP_INSPECT_NO_BLIND_RETRY',failureType=type(error).__name__,failure=str(error))
  # Never restore code beneath a starting/live controller or force a process exit.
  if stopped and code_started and new is not None and new.get('ready') and u.process_owned(new['controllerPID'],Q,NEW):
   dump(E/'candidate-failure-normal-stop.json',u.normal_stop(Q,NEW,new));new=None
   with u.server_lock(Q):u.restore_code(Q,backup,changes)
   rollback=E/'rollback';rollback.mkdir();restored=u.launch(Q,OLD,rollback,gateway_port=18891);u.health(Q,restored,gateway_port=18891);result.update(codeRolledBack=True,restoredControllerPID=restored['controllerPID'])
  raise
 finally:
  result['endedAt']=datetime.datetime.now().astimezone().isoformat();dump(E/'result.private.json',result)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--apply',action='store_true');a=p.parse_args();r=prepare() if a.prepare else apply()
 if r:print(json.dumps(r))
