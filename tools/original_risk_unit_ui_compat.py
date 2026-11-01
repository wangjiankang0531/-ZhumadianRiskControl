"""Refresh the native risk-unit list tab after successful creation."""
from pathlib import Path
from contextlib import contextmanager
from hashlib import sha256

SOURCES={'src/views/hiddenInvestigate/riskAnalysisUnit/info/addOrEdit.vue': ('addOrEdit.vue', 'e6858453831914ecdebc6e33b1afb9ff2114f63cfa3015694a6b41f5bd9245d7', 'c38115076cfc31c68a2dbdc9c24c66631828002e458b22ebd2b6a8ab67d449a4')}

def digest(raw):return sha256(raw).hexdigest()
def regular(p):return p.is_file()and not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p

@contextmanager
def risk_unit_ui_override(project,reference):
 project=Path(project).resolve(strict=True);reference=Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference)or reference.is_relative_to(project):raise ValueError('DISTINCT_RISK_UNIT_BUILD_COPY_REQUIRED')
 adapters=Path(__file__).resolve().parent/'frontend/risk-unit';planned=[];receipt={'adapter':'original-risk-unit-add-return-r1','files':{},'referenceModified':False,'authenticationOrPermissionModified':False,'sourceFilesRestored':False}
 for relative,(name,before,after)in SOURCES.items():
  target=project/relative;origin=reference/relative;candidate=adapters/name
  if not all(regular(p)for p in (target,origin,candidate))or target.samefile(origin):raise ValueError('DIRECT_DISTINCT_RISK_UNIT_FILES_REQUIRED')
  raw=origin.read_bytes();changed=candidate.read_bytes()
  if digest(raw)!=before or target.read_bytes()!=raw or digest(changed)!=after:raise ValueError('RISK_UNIT_INITIATOR_SOURCE_DRIFT')
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
  if drifted:raise ValueError('RISK_UNIT_EXTERNAL_SOURCE_DRIFT_NO_OVERWRITE')
