"""Prepare and normally install the exact current disposal transaction and original event-operation frontend update; preserve all data."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,sys,uuid
HERE=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';Q=Path('D:/Zqa20261025/Application');B=R/'work/event_disposal_update_20261029';L=R/'work/event_disposal_lifecycle_20261029'
OLD='b55043e1f135b4ba7fb97dc56b4d9a2da418bb67f7f76db081745b066cb55006';NEW='9fbc1db40a205414f0788c21d109ba966196ad178c04bb60195f46f99a0631b3';PIN='1e134852f61b0c5db23d3ea38b6f73596a68779389efd3d325be4afbda1af65b';UPDATER='7c709a32fadba0381e8b5df36e558ff07156e1258b9994c1d6deb27a73837934'
sys.dont_write_bytecode=True;sys.path.insert(0,str(A/'tools'));from run_original_inventory_ownership_probe import state
from verify_original_work_reservation_sql import run
import install_confirmed_operations_local_20261029 as retained
prior=retained.prior
retained.L=L
prior.E=L

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def updater():
 path=B/'payload/tools/original_public_test_update.py';assert sha(path)==UPDATER;spec=importlib.util.spec_from_file_location('own_pinned_event_disposal_updater',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def projection(tag,current):
 old=retained.projection(tag,current);target=L/tag;deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
 try:run(target,'read-event-tables',[deps['java'],'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(L/'read-classes')+';'+deps['classpath'],'xnby.replica.OriginalEventDisposalTableReadProbe',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),target/'event-tables.private.json'],35,secret)
 finally:del secret
 events=read(target/'event-tables.private.json');assert events['readOnlyConnection'] and not events['businessMethodsAuthenticationWritesOrHTTPInvoked'] and not events['rowValuesOutputOrCopied'] and set(events['permanentTwoTables'])=={'event_info','event_disposal_record'}
 return {**old,'permanentEventTables':events['permanentTwoTables']}

def prepare():
 assert not L.exists(),'FRESH_LIFECYCLE_REQUIRED';u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 checks=read(B/'file-rollback-verification.json');assert checks['actualFullApplyRestorePassed'] and checks['actualFourthReplacementFailureRestorePassed'] and checks['manifestSHA256']==PIN
 phase=R/'Document/Deployment/event_disposal_atomic_20261029';assert read(phase/'sql-verification.json')['candidateCases']==11 and read(phase/'observer-context-r1/result.json')['contextsPerMode']==7 and read(phase/'browser-disposal-r2/browser-result.json')['sceneCount']==7 and read(phase/'browser-exercise-r2/browser-result.json')['sceneCount']==9
 current=state();assert current['controllerPID']==11344 and Path(current['run']).name=='j57';u.health(Q,current,gateway_port=18891);L.mkdir();(L/'tmp').mkdir();(L/'read-classes').mkdir();deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for p,v in deps['inputPins'].items():assert sha(p)==v['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];sources=[prior.source(),*prior.safety_sources(),A/'tools/java/OriginalEmergencyTeamTableReadProbe.java',A/'tools/java/OriginalEmergencyResourceTableReadProbe.java',A/'tools/java/OriginalDutyTableReadProbe.java',A/'tools/java/OriginalEventDisposalTableReadProbe.java'];run(L,'compile-read',[java.with_name('javac.exe'),'-J-Xmx128m','-proc:none','-encoding','UTF-8','-d',L/'read-classes','-cp',deps['classpath'],*sources],35)
 baseline=projection('before',current);dump(L/'before-observers.json',prior.observation(current))
 receipt={'at':datetime.datetime.now().astimezone().isoformat(),'bundle':str(B),'manifestSHA256':PIN,'oldReleaseSHA256':OLD,'newReleaseSHA256':NEW,'oldControllerPID':current['controllerPID'],'oldOwnerId':current['ownerId'],'oldRun':current['run'],'oldStateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'databaseUUID':current['databaseUUID'],'installationSHA256':sha(Q/'UserData/OriginalServer/installation.json'),'configurationSHA256':sha(Q/'private/server-configuration.json'),'objectCredentialsSHA256':sha(Q/'UserData/OriginalServer/store-credentials.private.json'),'sourcePins':{str(p):sha(p) for p in [Path(__file__),A/'tools/install_work_safety_local_20261029.py',A/'tools/install_confirmed_operations_local_20261029.py',A/'tools/original_event_disposal_update_compat.py',*sources]},'readClassPins':{p.relative_to(L/'read-classes').as_posix():sha(p) for p in (L/'read-classes').rglob('*.class')},'baselineProjection':baseline,'codeFiles':len(changes),'preparedOnly':True};dump(L/'prepared.json',receipt);print(json.dumps({'prepared':True,'changedPaths':len(changes),'sampleGroups':9,'completeSafetyTables':2,'completeTeamTables':2,'completeEventTables':2,'runtimeStopped':False}),flush=True)
def apply():
 p=read(L/'prepared.json');assert not (L/'apply-started.json').exists(),'NO_UNCHANGED_RETRY';u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 for name,pin in p['sourcePins'].items():assert sha(name)==pin
 assert {f.relative_to(L/'read-classes').as_posix():sha(f) for f in (L/'read-classes').rglob('*.class')}==p['readClassPins'];current=state();assert current['controllerPID']==p['oldControllerPID'] and current['ownerId']==p['oldOwnerId'] and current['run']==p['oldRun'] and sha(Q/'UserData/OriginalServer/current-run.json')==p['oldStateSHA256']
 dump(L/'apply-started.json',{'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':PIN});result={'state':'PRECHECK_PASSED','runtimeReady':False,'publicChanged':False,'fullCloneReady':False};backup=Q/'UserData/OriginalFrontendUpdates'/str(uuid.uuid4())
 try:
  print('LOCAL_STOP: normal shutdown of owned j57',flush=True);dump(L/'old-normal-stop.json',u.normal_stop(Q,OLD,current));u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891)
  with u.server_lock(Q):u.backup_code(Q,backup,changes);result['codeBackup']=str(backup);u.replace_code(Q,B,changes)
  result['state']='CODE_APPLIED';dump(L/'result.json',result);folder=L/'start';folder.mkdir();print('LOCAL_START: '+NEW[:12],flush=True);new=u.launch(Q,NEW,folder,gateway_port=18891);u.health(Q,new,gateway_port=18891);current=state();assert current['controllerPID']==new['controllerPID'] and current['databaseUUID']==p['databaseUUID']
  for name,key in [(Q/'UserData/OriginalServer/installation.json','installationSHA256'),(Q/'private/server-configuration.json','configurationSHA256'),(Q/'UserData/OriginalServer/store-credentials.private.json','objectCredentialsSHA256')]:assert sha(name)==p[key]
  retained=prior.observation(current);team=u.emergency_team_observer_ready(Q,current);event=u.event_disposal_observer_ready(Q,current);assert event['allEventDisposalMethodsAndManagerMatched'];dump(folder/'actual-observers.json',{**retained,'emergencyTeam':team,'eventDisposal':event});after=projection('after-start',current);assert after==p['baselineProjection'],'SAMPLE_OR_COMPLETE_TABLES_CHANGED'
  dump(folder/'ready.json',{'controllerPID':current['controllerPID'],'run':current['run'],'releaseSHA256':NEW,'sampleGroupsUnchanged':9,'completeSafetyTablesUnchanged':2,'completeTeamTablesUnchanged':2,'completeResourceTablesUnchanged':2,'completeDutyTablesUnchanged':3,'completeEventTablesUnchanged':2,'allRetainedAndEmergencyClassAdvisorMetadataVerified':True})
  result.update(state='LOCAL_READY_EVENT_DISPOSAL_REAL_UI_PENDING',runtimeReady=True,controllerPID=current['controllerPID'],run=current['run'],releaseSHA256=NEW,normalOwnedStopStartVerified=True,sampleGroupsUnchanged=9,completeSafetyTablesUnchanged=2,completeTeamTablesUnchanged=2,completeResourceTablesUnchanged=2,completeDutyTablesUnchanged=3,completeEventTablesUnchanged=2,allRetainedAndEmergencyClassAdvisorMetadataVerified=True,normalUserLoginPending=True,actualEventDisposalAuthenticatedHTTPOrRoleAcceptance=False,publicFindingSaveFixed=False);print('LOCAL_READY: event disposal transaction/false rollback and event/exercise result handling installed; real authenticated UI pending',flush=True)
 except BaseException as error:result.update(state='STOP_INSPECT_NO_BLIND_RETRY',failureType=type(error).__name__,failure=str(error));raise
 finally:result['endedAt']=datetime.datetime.now().astimezone().isoformat();dump(L/'result.json',result)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True);m.add_argument('--prepare',action='store_true');m.add_argument('--apply',action='store_true');args=p.parse_args();value=prepare() if args.prepare else apply()
 if value:print(json.dumps(value))
