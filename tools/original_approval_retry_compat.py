"""Precisely restore submit controls after approval failures; preserve business bodies and API authorization."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
RELATIVE='src/components/workflow/components/auditForm.vue'
ORIGINAL_SHA256='1c4cbd5d5d036a42744838e3bbc4c91286eb3b41e36d0d7a840c1f375ec45242'
def transform(raw):
 if sha256(raw).hexdigest()!=ORIGINAL_SHA256:raise ValueError('PINNED_ORIGINAL_APPROVAL_COMPONENT_REQUIRED')
 newline=b'\r\n' if b'\r\n' in raw else b'\n'
 old=newline.join([b'  if (!id) return;',b'  await obj?.api!(id as string, params);',b'  ElMessage.success(ruleForm.auditType + "\xe6\x88\x90\xe5\x8a\x9f");',b'  isSubmit.value = false;',b'  emit("submit", params);'])
 new=newline.join([b'  if (!id || typeof obj?.api !== "function") {',b'    isSubmit.value = false;',b'    return;',b'  }',b'  try {',b'    await obj.api(id as string, params);',b'    ElMessage.success(ruleForm.auditType + "\xe6\x88\x90\xe5\x8a\x9f");',b'    isSubmit.value = false;',b'    emit("submit", params);',b'  } catch {',b'    // The original request client owns error notifications; a rejected operation is not a success.',b'  } finally {',b'    isSubmit.value = false;',b'  }'])
 if raw.count(old)!=1:raise ValueError('EXACT_APPROVAL_SUBMIT_BRANCH_REQUIRED')
 updated=raw.replace(old,new,1)
 return updated,{'file':RELATIVE,'originalSHA256':sha256(raw).hexdigest(),'adaptedSHA256':sha256(updated).hexdigest(),'failedOrMissingOperationDoesNotEmitSuccess':True,'loadingReleasedAfterFailure':True,'formDataAPIPathsAuthenticationPermissionsOrActionListChanged':False}
def regular(path):return path.is_file() and not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400 and path.resolve(strict=True)==path
@contextmanager
def approval_retry_override(project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_APPROVAL_BUILD_COPY_REQUIRED')
 target,origin=project/RELATIVE,reference/RELATIVE
 if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_APPROVAL_FILES_REQUIRED')
 raw=origin.read_bytes()
 if target.read_bytes()!=raw:raise ValueError('APPROVAL_BUILD_COPY_DRIFT')
 updated,receipt=transform(raw);receipt.update(referenceChanged=False,sourceFileRestored=False);target.write_bytes(updated)
 try:yield receipt
 finally:
  if target.read_bytes()!=updated:raise ValueError('APPROVAL_EXTERNAL_EDIT_PRESERVED')
  target.write_bytes(raw);receipt['sourceFileRestored']=True
