"""Preserve original Axios errors in two pinned PC build copies; do not change business responses."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
PINS={'security_pc':'e9696aa0f4d812bc6990cfa2c237a71df542437aa5aff5743bf35d7ef0a446fe','emergency_pc':'7f4bb25205daba07f637c77ac17665da6d34f2c054e18ca3d0edacb94d02cce8'}
RELATIVE='src/utils/request.ts'
def transform(kind,raw):
 if kind not in PINS or sha256(raw).hexdigest()!=PINS[kind]:raise ValueError('PINNED_ORIGINAL_REQUEST_CLIENT_REQUIRED')
 old=b'const msg = error.response.data.message || error.response.data.msg;';replacement=b'const msg = error?.response?.data?.message || error?.response?.data?.msg || error?.message;'
 show=b'msg && ElMessage.error(msg);';guard=b'if (!axios.isCancel(error) && typeof msg === "string" && msg) ElMessage.error(msg);'
 newline=b'\r\n' if b'\r\n' in raw else b'\n';branch=old+newline+b'        '+show
 if raw.count(old)!=1 or raw.count(branch)!=1:raise ValueError('EXACT_ORIGINAL_ERROR_BRANCH_REQUIRED')
 updated=raw.replace(branch,replacement+newline+b'        '+guard,1)
 return updated,{'kind':kind,'file':RELATIVE,'originalSHA256':sha256(raw).hexdigest(),'adaptedSHA256':sha256(updated).hexdigest(),'originalErrorObjectPreserved':True,'successAndBusinessErrorAndLoginInterceptorsUnchanged':True,'authenticationOrPermissionChanged':False}
def regular(path):
 return path.is_file() and not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400 and path.resolve(strict=True)==path
@contextmanager
def request_error_override(kind,project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_REQUEST_BUILD_COPY_REQUIRED')
 target,origin=project/RELATIVE,reference/RELATIVE
 if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_REQUEST_FILES_REQUIRED')
 raw=origin.read_bytes()
 if target.read_bytes()!=raw:raise ValueError('REQUEST_BUILD_COPY_DRIFT')
 updated,receipt=transform(kind,raw);receipt.update(referenceChanged=False,sourceFileRestored=False);target.write_bytes(updated)
 try:yield receipt
 finally:
  if target.read_bytes()!=updated:raise ValueError('REQUEST_EXTERNAL_EDIT_PRESERVED')
  target.write_bytes(raw);receipt['sourceFileRestored']=True
