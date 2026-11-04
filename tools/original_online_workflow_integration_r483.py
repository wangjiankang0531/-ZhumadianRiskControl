from pathlib import Path
from contextlib import contextmanager
import hashlib,json,os
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/original_online_workflow_integration_r475_20261104'
sha=lambda b:hashlib.sha256(b).hexdigest()
@contextmanager
def online_workflow_override(project):
 project=Path(project).absolute();assert project==R/'work/user_feedback_20261031/event-research-level-r418/source'
 assert project.resolve()==project
 plan=json.loads((D/'prepared-candidate-r481.json').read_bytes());old=json.loads((D/'prepared-candidate-r475.json').read_bytes())['parentPins']
 source=R/'Application/source-review/original-online-integration-r481';saved={};after={}
 for name,pin in plan['candidatePins'].items():
  target=project/name
  for p in [target,*target.parents]:
   if p.exists():assert not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'BUILD_SOURCE_REPARSE_REFUSED'
  raw=(source/name).read_bytes();assert len(raw)==pin['bytes']and sha(raw)==pin['sha256']
  if name in old:
   before=target.read_bytes();assert {'bytes':len(before),'sha256':sha(before)}==old[name]
   origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'/name
   assert not os.path.samefile(target,origin),'SHARED_SOURCE_EDIT_REFUSED'
  else:assert not target.exists();before=None
  saved[name]=before;after[name]=raw
 applied=[];proof={'files':plan['candidatePins'],'onlyTwoExistingAndTwoNewSources':True,'sourceRestored':False}
 try:
  for name,raw in after.items():
   target=project/name
   if saved[name]is None:
    with target.open('xb')as f:f.write(raw)
   else:target.write_bytes(raw)
   applied.append(name)
  yield proof
 finally:
  for name in applied:assert(project/name).read_bytes()==after[name],'FOREIGN_SOURCE_CHANGE_REFUSE_RESTORE'
  for name in reversed(applied):
   target=project/name
   if saved[name]is None:target.unlink()
   else:target.write_bytes(saved[name])
  proof['sourceRestored']=all((project/name).read_bytes()==before if before is not None else not(project/name).exists()for name,before in saved.items())
