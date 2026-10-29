"""Normally repair the exact known exercise observer identifier-format failure with a pinned five-file update."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,sys,uuid
HERE=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';Q=Path('D:/Zqa20261025/Application');B=R/'work/emergency_exercise_repair_update_20261029';L=R/'work/emergency_exercise_repair_lifecycle_20261029'
OLD='286f3cf29fef66380e639ebf3272c69538f3a0be9aff8c13e9542d11902867a8';NEW='83de8d4e5c5a824eaaf6287dd374389047f5ebee167c85703e4bad1111f6e824';PIN='abf707f638056e62f0ae87e8886d1959da325f42c3bcdf4de414b81e3ecf9de5';UPDATER='73e942d1ac5ed52f703c24df3631d9f6b5880d857bef7a8b35ba5f4bbbfbc638'
sys.dont_write_bytecode=True;sys.path.insert(0,str(A/'tools'));from run_original_inventory_ownership_probe import state
from verify_original_work_reservation_sql import run
import install_event_disposal_local_20261029 as retained
prior=retained.prior
retained.L=L
retained.retained.L=L
prior.E=L

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def updater():
 path=B/'payload/tools/original_public_test_update.py';assert sha(path)==UPDATER;spec=importlib.util.spec_from_file_location('own_pinned_event_disposal_updater',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def projection(tag,current):
 old=retained.projection(tag,current);target=L/tag;deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
 try:run(target,'read-exercise-tables',[deps['java'],'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(L/'read-classes')+';'+deps['classpath'],'xnby.replica.OriginalEmergencyExerciseTableReadProbe',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),target/'exercise-tables.private.json'],35,secret)
 finally:del secret
 events=read(target/'exercise-tables.private.json');assert events['readOnlyConnection'] and not events['businessMethodsAuthenticationWritesOrHTTPInvoked'] and not events['rowValuesOutputOrCopied'] and set(events['permanentTwoTables'])=={'emergency_exercise','base_file'}
 return {**old,'permanentExerciseTables':events['permanentTwoTables']}

def prepare():
 assert not L.exists(),'FRESH_LIFECYCLE_REQUIRED';u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 checks=read(B/'file-rollback-verification.json');assert checks['actualFullApplyRestorePassed'] and checks['actualFourthReplacementFailureRestorePassed'] and checks['manifestSHA256']==PIN
 phase=R/'Document/Deployment/emergency_exercise_local_20261029';assert read(phase/'observer-context-r3/result.json')['contextsPerMode']==14 and read(R/'work/emergency_exercise_integration_20261029/updater-gates-r3/result.json')['checks']==107

 from verify_emergency_exercise_interrupted_state import current as known_failure;known_failure();retained.L=L;retained.retained.L=L;prior.E=L;current=state();assert current['controllerPID']==17716 and Path(current['run']).name=='j59';L.mkdir();(L/'tmp').mkdir();(L/'read-classes').mkdir();deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for p,v in deps['inputPins'].items():assert sha(p)==v['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];sources=[prior.source(),*prior.safety_sources(),A/'tools/java/OriginalEmergencyTeamTableReadProbe.java',A/'tools/java/OriginalEmergencyResourceTableReadProbe.java',A/'tools/java/OriginalDutyTableReadProbe.java',A/'tools/java/OriginalEventDisposalTableReadProbe.java',A/'tools/java/OriginalEmergencyExerciseTableReadProbe.java'];run(L,'compile-read',[java.with_name('javac.exe'),'-J-Xmx128m','-proc:none','-encoding','UTF-8','-d',L/'read-classes','-cp',deps['classpath'],*sources],35)
 baseline=projection('before',current);assert baseline==read(R/'work/emergency_exercise_lifecycle_20261029/prepared.json')['baselineProjection'];dump(L/'before-observers.json',prior.observation(current))
 receipt={'at':datetime.datetime.now().astimezone().isoformat(),'bundle':str(B),'manifestSHA256':PIN,'oldReleaseSHA256':OLD,'newReleaseSHA256':NEW,'oldControllerPID':current['controllerPID'],'oldOwnerId':current['ownerId'],'oldRun':current['run'],'oldStateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'databaseUUID':current['databaseUUID'],'installationSHA256':sha(Q/'UserData/OriginalServer/installation.json'),'configurationSHA256':sha(Q/'private/server-configuration.json'),'objectCredentialsSHA256':sha(Q/'UserData/OriginalServer/store-credentials.private.json'),'sourcePins':{str(p):sha(p) for p in [Path(__file__),A/'tools/install_work_safety_local_20261029.py',A/'tools/install_confirmed_operations_local_20261029.py',A/'tools/original_emergency_exercise_update_compat.py',A/'tools/install_event_disposal_local_20261029.py',*sources]},'readClassPins':{p.relative_to(L/'read-classes').as_posix():sha(p) for p in (L/'read-classes').rglob('*.class')},'baselineProjection':baseline,'codeFiles':len(changes),'preparedOnly':True};dump(L/'prepared.json',receipt);print(json.dumps({'prepared':True,'changedPaths':len(changes),'sampleGroups':9,'completeSafetyTables':2,'completeTeamTables':2,'completeEventTables':2,'runtimeStopped':False}),flush=True)
def apply():
 p=read(L/'prepared.json');assert not (L/'apply-started.json').exists(),'NO_UNCHANGED_RETRY';u=updater();plan,old,changes=u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891);assert old==OLD and plan['newReleaseSHA256']==NEW
 for name,pin in p['sourcePins'].items():assert sha(name)==pin
 assert {f.relative_to(L/'read-classes').as_posix():sha(f) for f in (L/'read-classes').rglob('*.class')}==p['readClassPins'];current=state();assert current['controllerPID']==p['oldControllerPID'] and current['ownerId']==p['oldOwnerId'] and current['run']==p['oldRun'] and sha(Q/'UserData/OriginalServer/current-run.json')==p['oldStateSHA256']
 dump(L/'apply-started.json',{'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':PIN});result={'state':'PRECHECK_PASSED','runtimeReady':False,'publicChanged':False,'fullCloneReady':False};backup=Q/'UserData/OriginalFrontendUpdates'/str(uuid.uuid4())
 try:
  print('LOCAL_STOP: normal shutdown of owned j59',flush=True);dump(L/'old-normal-stop.json',u.normal_stop(Q,OLD,current));u.load_bundle(Q,B,PIN,expected_target=Q,expected_port=18891)
  with u.server_lock(Q):u.backup_code(Q,backup,changes);result['codeBackup']=str(backup);u.replace_code(Q,B,changes)
  result['state']='CODE_APPLIED';dump(L/'result.json',result);folder=L/'start';folder.mkdir();print('LOCAL_START: '+NEW[:12],flush=True);new=u.launch(Q,NEW,folder,gateway_port=18891);u.health(Q,new,gateway_port=18891);current=state();assert current['controllerPID']==new['controllerPID'] and current['databaseUUID']==p['databaseUUID']
  for name,key in [(Q/'UserData/OriginalServer/installation.json','installationSHA256'),(Q/'private/server-configuration.json','configurationSHA256'),(Q/'UserData/OriginalServer/store-credentials.private.json','objectCredentialsSHA256')]:assert sha(name)==p[key]
  retained=prior.observation(current);team=u.emergency_team_observer_ready(Q,current);event=u.event_disposal_observer_ready(Q,current);assert event['allEventDisposalMethodsAndManagerMatched'];exercise=u.emergency_exercise_observer_ready(Q,current);assert exercise['allEmergencyExerciseMethodsAndManagerMatched'] and exercise['nonNullUpdateStrategyMatched'];dump(folder/'actual-observers.json',{**retained,'emergencyTeam':team,'eventDisposal':event,'emergencyExercise':exercise});after=projection('after-start',current);assert after==p['baselineProjection'],'SAMPLE_OR_COMPLETE_TABLES_CHANGED'
  dump(folder/'ready.json',{'controllerPID':current['controllerPID'],'run':current['run'],'releaseSHA256':NEW,'sampleGroupsUnchanged':9,'completeSafetyTablesUnchanged':2,'completeTeamTablesUnchanged':2,'completeResourceTablesUnchanged':2,'completeDutyTablesUnchanged':3,'completeEventTablesUnchanged':2,'completeExerciseTablesUnchanged':2,'allRetainedAndEmergencyClassAdvisorMetadataVerified':True})
  result.update(state='LOCAL_READY_EXERCISE_QUOTED_METADATA_REPAIR_REAL_UI_PENDING',runtimeReady=True,controllerPID=current['controllerPID'],run=current['run'],releaseSHA256=NEW,normalOwnedStopStartVerified=True,sampleGroupsUnchanged=9,completeSafetyTablesUnchanged=2,completeTeamTablesUnchanged=2,completeResourceTablesUnchanged=2,completeDutyTablesUnchanged=3,completeEventTablesUnchanged=2,completeExerciseTablesUnchanged=2,allRetainedAndEmergencyClassAdvisorMetadataVerified=True,normalUserLoginPending=True,actualEmergencyExerciseAuthenticatedHTTPOrRoleAcceptance=False,publicFindingSaveFixed=False);print('LOCAL_READY: exercise parent/files save, bulk and delete transaction installed; real authenticated UI pending',flush=True)
 except BaseException as error:result.update(state='STOP_INSPECT_NO_BLIND_RETRY',failureType=type(error).__name__,failure=str(error));raise
 finally:result['endedAt']=datetime.datetime.now().astimezone().isoformat();dump(L/'result.json',result)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True);m.add_argument('--prepare',action='store_true');m.add_argument('--apply',action='store_true');args=p.parse_args();value=prepare() if args.prepare else apply()
 if value:print(json.dumps(value))
