"""Align the pinned original task point-name input with the supplied backend query DTO."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

RELATIVE='src/views/intelligentInspection/task/index.vue'
PIN='57848d1c8d75121c03cd3b29ea55ad4936a0867255bf5e4cc6b8838fb1cc2522'

def transform(raw):
 if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_INSPECTION_TASK_REQUIRED')
 old=b'prop: "routeName",';new=b'prop: "pointName",'
 if raw.count(old)!=1 or raw.count(new)!=0:raise ValueError('EXACT_ORIGINAL_POINT_NAME_FIELD_REQUIRED')
 adapted=raw.replace(old,new,1)
 return adapted,{'file':RELATIVE,'originalSHA256':PIN,'adaptedSHA256':sha256(adapted).hexdigest(),'onlySearchPropertyChanged':True,'oldQueryField':'routeName','backendQueryField':'pointName','labelsRoutesOtherFiltersAndPermissionsUnchanged':True}

def regular(p):
 return p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p

@contextmanager
def inspection_filter_override(project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_INSPECTION_BUILD_COPY_REQUIRED')
 target,origin=project/RELATIVE,reference/RELATIVE
 if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_INSPECTION_FILES_REQUIRED')
 raw=origin.read_bytes();updated,receipt=transform(raw)
 if target.read_bytes()!=raw:raise ValueError('INSPECTION_BUILD_COPY_DRIFT')
 target.write_bytes(updated);receipt.update(referenceChanged=False,sourceFileRestored=False)
 try:yield receipt
 finally:
  if target.read_bytes()!=updated:raise ValueError('INSPECTION_EXTERNAL_EDIT_PRESERVED')
  target.write_bytes(raw);receipt['sourceFileRestored']=True
