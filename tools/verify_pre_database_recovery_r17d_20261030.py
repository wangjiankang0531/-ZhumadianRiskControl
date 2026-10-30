from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,tempfile,shutil,hashlib
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/server_directory_migration_20261030_r17d';P=json.loads((D/'delivery/migration-manifest.json').read_bytes());checks=[]
for case in ['never-started-safe','database-metadata-changed','unknown-start-state','database-start-requested','mysql-child-present','database-client-marker-present','unknown-code-present','normal-mysql-exited-zero','unknown-image-retained','partial-known-restoration']:
 spec=importlib.util.spec_from_file_location('recovery_'+case,D/'delivery/migrate_zdm_directory_20261029.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 with tempfile.TemporaryDirectory(prefix='pre-db-r17d-',dir=R/'work') as folder:
  f=Path(folder);m.NEW=f/'new/Application';m.OLD=f/'old/Application';m.STAGE=f/'stage';m.STATUS=m.STAGE/'status.json';m.NEW.mkdir(parents=True);root=m.NEW/m.BACKUP;root.mkdir(parents=True)
  for n,row in P['replacements'].items():
   dest=m.NEW/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(D/'delivery/payload'/n,dest)
   dest=root/'before'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(D/'baseline'/n,dest)
  for n in m.POINTERS:m.write(m.NEW/n,{'current':'synthetic'});m.write(root/'before'/n,{'before':'synthetic'})
  db=m.NEW/'UserData/OriginalServer/database';db.mkdir(parents=True);(db/'synthetic.data').write_bytes(b'never-real-business-data');m.write(root/'protected-after-move.json',{'UserData/OriginalServer/database':m.metadata_tree(db)})
  run=m.NEW/'UserData/OriginalServer/runs/j1';run.mkdir(parents=True);receipt={'run':str(run),'controllerPID':12345,'allOwnedChildrenExited':True,'databaseStartRequested':False,'children':{'store':12346},'exitCodesBeforeJobClose':{'store':0}}
  if case=='database-metadata-changed':(db/'synthetic.data').write_bytes(b'changed synthetic only')
  if case=='unknown-start-state':receipt.pop('databaseStartRequested')
  if case=='database-start-requested':receipt['databaseStartRequested']=True
  if case=='mysql-child-present':receipt['children']['mysql']=12347
  if case=='database-client-marker-present':(run/'mysql-client.private.cnf').write_text('synthetic-only')
  if case=='unknown-code-present':(m.NEW/'tools/serve_original_server_release.py').write_text('not a known original or candidate')
  if case=='normal-mysql-exited-zero':receipt['databaseStartRequested']=True;receipt['children']['mysql']=12347;receipt['exitCodesBeforeJobClose']['mysql']=0
  if case=='partial-known-restoration':shutil.copyfile(D/'baseline/release-manifest.json',m.NEW/'release-manifest.json')
  m.write(run/'receipt.json',receipt);m.write(root/'launch-state.json',{'controllerPID':12345});m.write(m.NEW/'UserData/OriginalServer/current-run.json',{'controllerPID':0})
  m.updater=lambda *args,**kwargs:SimpleNamespace(process_owned=lambda *args:False);m.all_root_images=lambda *args:[{'ProcessId':12348}] if case=='unknown-image-retained' else [];m.set_mapping=lambda *args:None;m.status=lambda *args,**kwargs:None
  before={n:m.sha(m.NEW/n) for n in P['replacements']};error=None
  try:m.rollback_stop(P)
  except ValueError as e:error=str(e)
  success=case in ('never-started-safe','normal-mysql-exited-zero','partial-known-restoration')
  if success:
   assert error is None,(case,error)
   assert all(m.sha(m.NEW/n)==row['before'] for n,row in P['replacements'].items())
   assert all(m.read(m.NEW/n)=={'before':'synthetic'} for n in m.POINTERS)
  else:assert error and before=={n:m.sha(m.NEW/n) for n in P['replacements']},(case,error)
  checks.append({'case':case,'passed':True,'accepted':success,'failureCode':error,'rejectedWithoutRestorationWrites':not success})
v={'schema':'xnby.pre-database-start-recovery.verification.v1','actualRecoveryFunctionUsed':True,'syntheticLifecycleAndIISOnly':True,'allPassed':True,'tests':checks};(D/'pre-database-recovery-verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8');print(json.dumps(v))
