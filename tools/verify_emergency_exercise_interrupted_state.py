"""Validate only the exact live first-install metadata-format failure; never claim normal readiness."""
from pathlib import Path
import hashlib,json,sys
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application');T=R/'Application/tools';D=R/'Document/Deployment/emergency_exercise_local_20261029';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def current():
 from run_original_inventory_ownership_probe import state
 import install_emergency_exercise_local_20261029 as first
 c=state();expected=read(D/'initial-installed-current-state.private.json');assert c==expected and c['controllerPID']==17716 and Path(c['run']).name=='j59';assert sha(Q/'release-manifest.json')=='286f3cf29fef66380e639ebf3272c69538f3a0be9aff8c13e9542d11902867a8';u=first.updater();assert len(first.prior.observation(c))==4 and u.emergency_team_observer_ready(Q,c)['allEmergencyTeamMethodsAndManagerMatched'] and u.event_disposal_observer_ready(Q,c)['allEventDisposalMethodsAndManagerMatched'];v=read(Path(c['run'])/'b/emergency-exercise-transaction-observation.json');assert v==read(D/'initial-installed-observer-report.json') and v['PID']==c['children']['business'] and v['run']=='j59' and v['ownerIdSHA256']==hashlib.sha256(c['ownerId'].encode('ascii')).hexdigest();assert v['existingTransactionManagerCount']==1 and v['existingSingletonMetadataOnly'] and not v['businessMethodsInvoked'] and not v['SQLOrNetworkRequestsIssuedByObserver'] and v['allEmergencyExerciseMethodsAndManagerMatched'] is False and v['nonNullUpdateStrategyMatched'] is False
 expectedColumns={'emergency_plan_id','exercise_location','organize_department','commander_chief','exercise_time','participants','cooperating_unit','exercise_type','exercise_device','exercise_describe','exercise_special_situation','problems_andmeasures','created_at'};assert {x[1:-1] if x.startswith('`') and x.endswith('`') else x for x in v['exerciseUpdateStrategies']}==expectedColumns
 for item in v['exerciseUpdateStrategies'].values():assert item['updateStrategy']=='NOT_NULL' and item['withUpdateFill'] is False
 for group in v['exercise'].values():
  assert group['allMethodsHaveMatchingTransactionAdvisor'] and len(group['services'])==1;bean=group['services'][0];assert bean['existingSingleton'] and bean['isAopProxy'] and bean['targetClassSHA256']=='dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece'
 p=read(R/'work/emergency_exercise_lifecycle_20261029/prepared.json')
 for name,key in [(Q/'UserData/OriginalServer/installation.json','installationSHA256'),(Q/'private/server-configuration.json','configurationSHA256'),(Q/'UserData/OriginalServer/store-credentials.private.json','objectCredentialsSHA256')]:assert sha(name)==p[key]
 return {'run':c['run'],'controllerPID':c['controllerPID'],'databaseUUID':c['databaseUUID'],'knownMetadataFormattingFailureOnly':True,'normalReadinessAccepted':False}
