"""Reject provided business SDK error-code envelopes on /serv/ without changing success/login/transport behavior."""
from pathlib import Path
from contextlib import contextmanager
from hashlib import sha256
from original_request_error_compat import transform as preserve_error, PINS as PC_PINS
PINS={**PC_PINS,'mobile':'2e5a239176d23e87d2668dcd7fc4eb21f1e72cce9ecfbc685b0e859fc036bdf5'}

def relative(kind):return 'src/utils/http.ts' if kind=='mobile' else 'src/utils/request.ts'
def transform(kind,raw):
 if kind not in PINS or sha256(raw).hexdigest()!=PINS[kind]:raise ValueError('PINNED_ORIGINAL_BUSINESS_RESULT_CLIENT_REQUIRED')
 base=raw if kind=='mobile' else preserve_error(kind,raw)[0]
 scope='options.url?.startsWith("/serv/")' if kind=='mobile' else 'res.config?.url?.startsWith("/serv/")'
 old=b'if (res.data.code === 400) {'
 new=('if (res.data.code === 400 || ('+scope+' && Number.isInteger(res.data.code) && res.data.code >= 100000 && res.data.code <= 2147483647)) {').encode('utf-8')
 if base.count(old)!=1:raise ValueError('EXACT_ORIGINAL_BUSINESS_FAILURE_BRANCH_REQUIRED')
 updated=base.replace(old,new,1)
 return updated,{'kind':kind,'file':relative(kind),'originalSHA256':sha256(raw).hexdigest(),'requiredPreimageSHA256':sha256(base).hexdigest(),'adaptedSHA256':sha256(updated).hexdigest(),'scope':'relative /serv/ SDK integral error code 100000..2147483647','SDKSuccessZeroAndPlatform200Preserved':True,'existing400600AndHTTPErrorBranchesPreserved':True,'authenticationOrPermissionChanged':False}

def regular(p):return p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p
@contextmanager
def business_result_override(kind,project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_BUSINESS_RESULT_COPY_REQUIRED')
 rel=relative(kind);target,origin=project/rel,reference/rel
 if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_BUSINESS_RESULT_FILES_REQUIRED')
 raw=origin.read_bytes();updated,receipt=transform(kind,raw);base=raw if kind=='mobile' else preserve_error(kind,raw)[0]
 if target.read_bytes()!=base:raise ValueError('BUSINESS_RESULT_BUILD_COPY_PREIMAGE_DIFFERS')
 target.write_bytes(updated);receipt.update(referenceChanged=False,sourceFileRestored=False)
 try:yield receipt
 finally:
  if target.read_bytes()!=updated:raise ValueError('BUSINESS_RESULT_EXTERNAL_EDIT_PRESERVED')
  target.write_bytes(base);receipt['sourceFileRestored']=True
