from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';D=R/'Document/Deployment/event_crud_native_r990_20261104'
J=lambda p:json.loads(Path(p).read_bytes())
def pin(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert not (D/'cleanup-plan-r997.json').exists()
audit=J(D/'independent-restore-r994.json');assert audit['passed']and not audit['nativeEventCRUDProductAcceptance']and audit['actualOwnGProcessReferences']==0
assert J(D/'confirmed-event-false-save-defect-r994.json')['confirmedProductDefect']
plan=J(D/'full-source-and-restore-plan.private.json');rows=dict(plan['mutations'])
for k,v in plan['retiredKnownFrontendPaths'].items():rows[k]={'before':v}
for k,v in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():rows[k]={'before':v}
targets=[]
for n in [979,982,985,990]:
 z=R/('work/ev'+str(n));proof=J(z/('verified-event-crud-r'+str(n)+'.json'))
 assert proof['codeRestored']and proof['privateConfigurationRestored']and all(t['actualJobDescendantsZero']and t['controllerExitCode']==0 for t in proof['terminals'])
 before=z/'code-transaction/before';assert before.is_dir()
 files=[p for p in before.rglob('*')if p.is_file()]
 for p in files:
  rel=p.relative_to(before).as_posix();assert rel in rows and rows[rel]['before']is not None
  assert pin(p)==rows[rel]['before']and pin(G/rel)==rows[rel]['before']
 targets.append({'path':str(before.resolve()),'kind':'verified-restored-independent-code-preimages','logicalBytes':sum(p.stat().st_size for p in files),'files':len(files)})
 for phase in ['first-start','normal-restart']:
  folder=z/'browser'/phase
  if not folder.exists():continue
  b=J(folder/'browser-terminal.json');parent=J(z/(phase+'-browser-terminal.json'))
  assert b['normalBrowserClosed']and b['exitCode']==0 and parent['actualJobDescendantsZero']
  profile=folder/'chrome-profile';assert profile.is_dir()
  pf=[p for p in profile.rglob('*')if p.is_file()]
  targets.append({'path':str(profile.resolve()),'kind':'owned-headless-profile-all-actual-handles-exited','logicalBytes':sum(p.stat().st_size for p in pf),'files':len(pf)})
for target in targets:
 p=Path(target['path']);assert p.is_relative_to(R/'work')and any(p.is_relative_to(R/('work/ev'+str(n)))for n in [979,982,985,990])
 for item in [p,*p.parents,*p.rglob('*')]:
  if item.exists():assert not item.is_symlink()and not item.lstat().st_file_attributes&0x400
out={'schema':'xnby.own-event-test-cleanup.v1','targets':targets,'allCodeConfigAndPointersIndependentlyRestored':True,'allOwnProcessReferencesZeroBeforePlan':True,'businessDataPDFUploadsModelsJournalsSourcesAndPrivateConfigurationPreimagesRetained':True,'logicalBytesNotClaimedAsPhysicalSpace':True}
(D/'cleanup-plan-r997.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'prepared':True,'directories':len(targets),'logicalBytes':sum(t['logicalBytes']for t in targets)}))
