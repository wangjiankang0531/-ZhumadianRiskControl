"""Actual sparse code backup/replace/restore, isolated physical program fixtures.

No service orchestration, IIS, real configuration, data or public acceptance.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');W=R/'work/f482'
D=V/'r48-retained-preflight-r2-r1013'
OUT=R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-sparse-code-recovery-r1022.json'
J=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()if Path(p).is_file()else None
assert not OUT.exists() and J(R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-real-files-r1018.json')['passed']
assert shutil.disk_usage(R).free>2*1024**3+256*1024**2
spec=importlib.util.spec_from_file_location('exact_r2_sparse_r1022',D/'source/original_public_test_update.py')
wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
cases=[]
for label in ['r45','r47']:
 app=W/label;bundle=W/('b'+label[1:]);m=wrapper.runtime()
 plan=J(bundle/'update-manifest.json');old=J(app/'release-manifest.json')
 formal=J(D/('update-from-'+label+'.json'));formal_base=next(iter(formal['acceptedOldReleases']))
 binding=copy.deepcopy(m.R48_BASES[formal_base]);binding['accepted']['payloadManifestSHA256']=old['payloadManifestSHA256']
 m.R48_BASES={sha(app/'release-manifest.json'):binding};m.R48_PLAN_COMMON={**m.R48_PLAN_COMMON,'targetApplication':app.as_posix()}
 checked,oldsha,changes=m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app.as_posix(),expected_port=18892)
 assert checked==plan
 protected={n:sha(app/n)for n in ['private/server-configuration.json','release-manifest.json','payload-manifest.json']}
 for mode in ['normal','fourth-write-fault','concurrent-edit-refused','backup-drift-refused']:
  attempt=W/'code-recovery-r1022'/(label+'-'+mode)
  assert not attempt.exists()
  assert all(sha(app/n)==p['before']for n,p in changes.items())
  m.backup_code(app,attempt,changes)
  touched=[]
  def after(name):
   touched.append(name)
   if mode=='fourth-write-fault' and len(touched)==4:raise RuntimeError('OWN_FOURTH_WRITE_FAULT')
  try:m.replace_code(app,bundle,changes,after_each=after)
  except RuntimeError as exc:assert mode=='fourth-write-fault'and str(exc)=='OWN_FOURTH_WRITE_FAULT'and len(touched)==4
  else:
   assert mode!='fourth-write-fault' and touched[-1]=='release-manifest.json'
   assert all(sha(app/n)==p['after']for n,p in changes.items())
  if mode in ['concurrent-edit-refused','backup-drift-refused']:
   rel=next(n for n,p in changes.items()if n.startswith('frontend/')and p['before']is not None and p['after']is not None)
   target=app/rel if mode=='concurrent-edit-refused'else attempt/'before'/rel
   original=target.read_bytes();m.atomic(target,original+b'\nowned-drift\n')
   snapshot={n:sha(app/n)for n in changes}
   try:m.restore_code(app,attempt,changes)
   except (ValueError,FileNotFoundError):pass
   else:raise AssertionError('UNRELATED_DRIFT_RESTORE_ACCEPTED')
   assert snapshot=={n:sha(app/n)for n in changes},'PARTIAL_RESTORE_OCCURRED_BEFORE_PREFLIGHT_REFUSAL'
   m.atomic(target,original)
  m.restore_code(app,attempt,changes)
  assert all(sha(app/n)==p['before']for n,p in changes.items())
  assert all(sha(app/n)==p for n,p in protected.items())
  cases.append({'base':label,'mode':mode,'passed':True,'changedAndRetiredPaths':len(changes),
                'actualBackupReplaceRestoreFunctionsUnmodified':True,'allCodePreimagesRestored':True})
  print(json.dumps({'base':label,'mode':mode,'passed':True}),flush=True)
out={'passed':True,'checks':len(cases),'cases':cases,
 'realFileReadersHashBackupReplaceAndRestoreFunctionsNotMocked':True,
 'onlyOwnedProgramFixtureTargetAndSyntheticPrivateMetadataBindingsAdapted':True,
 'actualApplyUpdateServiceIISOrTLSLifecycleExecuted':False,
 'realBusinessDatabaseUploadsCredentialsGISAndUserDataNotCopiedOrChanged':True,
 'fullCloneReady':False}
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'checks':len(cases),'fullServiceUpdateClaimed':False}))
