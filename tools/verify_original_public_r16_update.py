"""Exercise exact R14 composition and file recovery in owned sparse roots only."""
from pathlib import Path
from unittest.mock import patch
import argparse,datetime,hashlib,importlib.util,json,shutil,sys,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from build_original_public_r16_update import BASE,LOCAL,UPDATER,UPIN,FACTORIES,FPIN,PREFIX,sha,read,encode,need
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def clean(p,root):
 need(p.resolve(strict=True)==p and p.parent==root,'EXACT_OWN_TEST_ROOT');need(all(not x.is_symlink() and not getattr(x.lstat(),'st_file_attributes',0)&0x400 for x in [p,*p.rglob('*')]),'NO_TEST_ROOT_REDIRECTION');shutil.rmtree(p)
def verify(root):
 root=Path(root).resolve(strict=True);need(not (root/'verification.json').exists(),'FRESH_R16_VERIFICATION');build=read(root/'build-result.json');variant=root/'from-r15';bundle=variant/'bundle';baseline=variant/'baseline';u=module(bundle/'payload'/UPDATER,'r16_exact_unchanged_public_updater');need(sha(bundle/'payload'/UPDATER)==build['newUpdaterSHA256'],'EXACT_COMPOSED_PUBLIC_UPDATER');original=u.check_file;inputs={};checks=0;cache={}
 priorRoots=[R/'work'/f'public_test_update_20261029_{rev}'/('from-r8/bundle/payload' if rev in ['r12','r13','r14'] else 'from-r14/bundle/payload' if rev=='r15' else 'bundle/payload') for rev in ['r15','r14','r13','r12','r9','r8']];backups=[Q/'UserData/OriginalFrontendUpdates'/n/'before' for n in ['75d6a676-f643-44dd-837a-406f71002728','297bf06c-39ae-4d8f-9a9f-e8e05403deb1','366d6aee-d890-44cf-9b24-fc581cedb963','769e60e4-4dae-4a5a-93c7-b63ace691684','f8d4283d-dc1c-4836-9ef7-e8bb3dc80690']]
 def resolve(base,name,pin,size=None):
  nonlocal checks
  if Path(base).resolve()!=baseline:return original(base,name,pin,size)
  for source in [baseline,*priorRoots,Q,*backups,R/'Application']:
   p=source/name
   if not p.is_file() or p.is_symlink() or size is not None and p.stat().st_size!=size:continue
   stamp=(str(p),p.stat().st_size,p.stat().st_mtime_ns,pin)
   if stamp not in cache:cache[stamp]=sha(p)==pin
   if not cache[stamp]:continue
   checks+=1;inputs[name]={'path':str(p),'SHA256':pin,'bytes':p.stat().st_size,'mtimeNS':p.stat().st_mtime_ns};return p
  raise ValueError('EXACT_CAPTURED_R14_INPUT_NOT_FOUND:'+name)
 with patch.object(u,'check_file',resolve):plan,old,changes=u.load_bundle(baseline,bundle,sha(bundle/'update-manifest.json'))
 need(old==BASE and len(changes)==build['changedPaths'] and len(plan['files'])==build['replacementFiles'] and len(plan['removedFrontendFiles'])==build['obsoleteFrontendFiles'],'EXACT_SPARSE_COUNTS');before=read(baseline/'payload-manifest.json');after=read(bundle/'payload/payload-manifest.json');oldRelease=read(baseline/'release-manifest.json');newRelease=read(bundle/'payload/release-manifest.json')
 from original_emergency_exercise_update_compat import initializers
 from run_original_inventory_ownership_probe import state
 from verify_emergency_exercise_local_state import current
 need({n:v for n,v in oldRelease['controllerFiles'].items() if n!=UPDATER}=={n:v for n,v in newRelease['controllerFiles'].items() if n!=UPDATER} and newRelease['controllerFiles'][UPDATER]==build['newUpdaterSHA256'],'ALL_OTHER_PUBLIC_CONTROLLERS_PRESERVED')
 allowed=set(build['fourTestedClasses'])|{FACTORIES}
 need({n:v for n,v in before['files'].items() if not n.startswith(PREFIX) and n not in allowed}=={n:v for n,v in after['files'].items() if not n.startswith(PREFIX) and n not in allowed},'ALL_NON_TARGET_PAYLOAD_DECLARATIONS_PRESERVED')
 need(initializers((bundle/'payload'/FACTORIES).read_bytes())==build['retainedInitializers']+['xnby.replica.OriginalEventDisposalTransactionObservation','xnby.replica.OriginalEmergencyExerciseTransactionObservation'],'ALL_FIVE_PUBLIC_INITIALIZERS_AND_NEW_TWO_PRESERVED')
 local=read(Q/'payload-manifest.json');need({n:v for n,v in after['files'].items() if n.startswith(PREFIX)}=={n:v for n,v in local['files'].items() if n.startswith(PREFIX)},'COMPLETE_J60_EMERGENCY_FRONTEND')
 need(set(plan['files'])=={n for n in after['files'] if n.startswith(PREFIX) and before['files'].get(n)!=after['files'][n]}|allowed|{UPDATER,'release-manifest.json','payload-manifest.json'},'ONLY_FRONTEND_DELTA_FOUR_CLASSES_FACTORY_AND_REQUIRED_HELPER_METADATA')
 for name,pin in build['fourTestedClasses'].items():need(sha(bundle/'payload'/name)==sha(Q/name)==pin,'ACTUAL_LOCALLY_LOADED_TESTED_CLASS_BYTES')
 live=state();need(u.event_disposal_observer_ready(Q,live)['allEventDisposalMethodsAndManagerMatched'] and u.emergency_exercise_observer_ready(Q,live)['allEmergencyExerciseMethodsAndManagerMatched'],'COMPOSED_PUBLIC_NEW_GATES_READ_ACTUAL_LOCAL_SINGLETON_METADATA')
 tx=variant/'transaction-qa';backup=variant/'transaction-backup';need(not tx.exists() and not backup.exists(),'FRESH_FILE_TRANSACTION_ROOTS');tx.mkdir()
 for name,row in changes.items():
  if row['before'] is not None:p=tx/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(resolve(baseline,name,row['before']).read_bytes())
 canaries=['private/OWN_CANARY','UserData/OriginalServer/database/OWN_CANARY','UserData/Uploads/OWN_CANARY','Assets/OWN_CANARY']
 for name in canaries:p=tx/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'OWN_SYNTHETIC_KEEP')
 def restored():
  for name,row in changes.items():
   p=tx/name;need(not p.exists() if row['before'] is None else p.is_file() and sha(p)==row['before'],'EXACT_OLD_BYTES_RESTORED')
  for name in canaries:need((tx/name).read_bytes()==b'OWN_SYNTHETIC_KEEP','CANARIES_PRESERVED')
 u.backup_code(tx,backup,changes);order=[];u.replace_code(tx,bundle,changes,order.append);need(order[-1]=='release-manifest.json' and len(order)==len(changes),'RELEASE_POINTER_LAST')
 for name,row in changes.items():need(not (tx/name).exists() if row['after'] is None else sha(tx/name)==row['after'],'NEW_BYTES_OR_EXACT_REMOVAL')
 u.restore_code(tx,backup,changes);restored();reached=[]
 def fault(name):
  reached.append(name)
  if len(reached)==4:raise RuntimeError('OWN_R16_FOURTH_WRITE_FAILURE')
 try:u.replace_code(tx,bundle,changes,fault)
 except RuntimeError as error:need(str(error)=='OWN_R16_FOURTH_WRITE_FAILURE','EXPECTED_FAULT')
 else:raise AssertionError('FAULT_NOT_REACHED')
 u.restore_code(tx,backup,changes);restored()
 delivery=root/'delivery/Zhumadian_Update_20261029_R16';archive=delivery/'Zhumadian_Public_Test_20261029_R16_From_R15.zip'
 with zipfile.ZipFile(archive) as z:
  expected={'web.config','update-manifest.json'}|{'payload/'+n for n in plan['files']};need(len(z.namelist())==len(expected) and set(z.namelist())==expected and z.testzip() is None,'CLOSED_ARCHIVE_MEMBERS')
  for name,row in plan['files'].items():raw=z.read('payload/'+name);need(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['SHA256'],'ACTUAL_ARCHIVE_BYTES')
  need(hashlib.sha256(z.read('update-manifest.json')).hexdigest()==build['manifestSHA256'],'EXACT_ARCHIVE_MANIFEST')
 for row in inputs.values():p=Path(row['path']);need(p.stat().st_size==row['bytes'] and p.stat().st_mtime_ns==row['mtimeNS'] and sha(p)==row['SHA256'],'READONLY_INPUT_DRIFT')
 from run_original_inventory_ownership_probe import state
 actual=state();need(actual['controllerPID']==4924 and Path(actual['run']).name=='j60' and sha(Q/'release-manifest.json')==LOCAL,'LOCAL_J60_UNCHANGED')
 for name,row in build['deliveryFiles'].items():need(sha(delivery/name)==row['SHA256'],'FIXED_DELIVERY_CHANGED')
 report={'at':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':sha(Path(__file__)),'baseReleaseSHA256':BASE,'newReleaseSHA256':build['newReleaseSHA256'],'compositionInputChecks':checks,'distinctReadonlyInputs':len(inputs),'replacementFiles':len(plan['files']),'obsoleteFrontendRemovals':len(plan['removedFrontendFiles']),'actualChangedPaths':len(changes),'actualFullFileApplyRestorePassed':True,'actualFourthWriteFailureRestorePassed':True,'releasePointerWrittenLast':True,'databaseUploadsCredentialsAndAssetsSyntheticCanariesPreserved':True,'allOtherPublicControllerAndNonTargetPayloadPinsUnchanged':True,'allFivePublicInitializersIncludingFindingAndNewTwoPreserved':True,'completeLocalEmergencyFrontendAndSecurityUnchanged':True,'newComposedObserverGatesReadActualLocalMetadata':True,'archiveMembersAndBytesMatched':True,'readonlyInputsUnchanged':True,'actualLocalJ60Unchanged':True,'networkDatabaseOrBusinessMethodsUsed':False,'freshPublicPreflightOrLifecycleProven':False,'serverDeployed':False,'fullCloneReady':False};(root/'verification.json').write_bytes(encode(report));(root/'composition-inputs.private.json').write_bytes(encode(inputs));clean(tx,variant);clean(backup,variant);print(json.dumps(report));return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);verify(p.parse_args().root)
