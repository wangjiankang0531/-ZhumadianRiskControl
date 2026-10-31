"""Bind the original workflow person's display label and native creatorUserId separately."""
from pathlib import Path
from contextlib import contextmanager
from hashlib import sha256

SOURCES={
 'src/components/workflow/index.vue':('index.vue','9c947291598cc15b639e80ce3a147080842a1080a041e713521c1382b0027959','9c35b88ab197308b443ba96c8308605eed965a879ea3216daba91573206a16aa'),
 'src/components/workflow/components/searchForm.vue':('components/searchForm.vue','2a638152ab876882d98ee74cbe0041170c42ca44f3005f5ca555c00a0bdb6de4','1727220c732f5e7ae4e8c1407abc54d378e45b5d811682a9d533ef4c68ef627e')}
def digest(raw):return sha256(raw).hexdigest()
def regular(p):return p.is_file()and not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p

@contextmanager
def workflow_initiator_ui_override(project,reference):
 project=Path(project).resolve(strict=True);reference=Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference)or reference.is_relative_to(project):raise ValueError('DISTINCT_WORKFLOW_BUILD_COPY_REQUIRED')
 adapters=Path(__file__).resolve().parent/'frontend/workflow';planned=[];receipt={'adapter':'original-workflow-initiator-ui-r1','files':{},'referenceModified':False,'authenticationOrPermissionModified':False,'sourceFilesRestored':False}
 for relative,(name,before,after)in SOURCES.items():
  target=project/relative;origin=reference/relative;candidate=adapters/name
  if not all(regular(p)for p in (target,origin,candidate))or target.samefile(origin):raise ValueError('DIRECT_DISTINCT_WORKFLOW_FILES_REQUIRED')
  raw=origin.read_bytes();changed=candidate.read_bytes()
  if digest(raw)!=before or target.read_bytes()!=raw or digest(changed)!=after:raise ValueError('WORKFLOW_INITIATOR_SOURCE_DRIFT')
  planned.append((target,raw,changed));receipt['files'][relative]={'originalSHA256':before,'adaptedSHA256':after}
 written=[]
 try:
  for target,raw,changed in planned:target.write_bytes(changed);written.append((target,raw,changed))
  yield receipt
 finally:
  drifted=[]
  for target,raw,changed in reversed(written):
   if not regular(target)or target.read_bytes()!=changed:drifted.append(str(target))
   else:target.write_bytes(raw)
  receipt['sourceFilesRestored']=not drifted
  if drifted:raise ValueError('WORKFLOW_EXTERNAL_SOURCE_DRIFT_NO_OVERWRITE')
