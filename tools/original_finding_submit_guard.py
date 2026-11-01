'''Prevent original-PC task completion while editable findings have no saved identity.

Only an independent build copy is patched; original API, roles and persisted state stay unchanged.
'''
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
RELATIVE='src/views/hiddenInvestigate/hazardInvestigation/info/index.vue'
PIN='fbf5d0b514742ca7c4e171af68455fc2597f7c203237c121761e844249673c62'
HELPER='''const canSubmitCheckPlan = () => {
  const items = field.value?.checkPlanItemsList;
  if (!field.value?.id || !Array.isArray(items) || items.some(item => !item || !Array.isArray(item.checkHiddenDangerList))) {
    ElMessage.error("排查信息尚未完整加载，请刷新确认后再提交");
    return false;
  }
  if (items.some(item => item.checkHiddenDangerList.some(danger => !danger?.id))) {
    ElMessage.error("还有未保存的隐患，请逐条保存或移除后再提交");
    return false;
  }
  return true;
};

'''
OPEN='const handleSave = async () => {\n'
CONFIRM='''  }).then(async () => {
    await submit({ id: field.value.id });'''
def transform(raw):
    if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_FINDING_INFO_REQUIRED')
    nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8').replace('\r\n','\n')
    if text.count(OPEN)!=1 or text.count(CONFIRM)!=1:raise ValueError('EXACT_FINDING_SUBMIT_BOUNDARIES_REQUIRED')
    out=text.replace(OPEN,HELPER+OPEN+'  if (!canSubmitCheckPlan()) return;\n',1).replace(CONFIRM,'  }).then(async () => {\n    if (!canSubmitCheckPlan()) return;\n    await submit({ id: field.value.id });',1).replace('\n',nl).encode('utf-8')
    return out,{'file':RELATIVE,'originalSHA256':PIN,'adaptedSHA256':sha256(out).hexdigest(),'checksBeforeConfirmationAndBeforeRequest':True,'newRowsMustBeSavedOrExplicitlyRemoved':True,'originalSubmitAPIAndPayloadPreserved':True,'validEmptyTaskSemanticsPreserved':True,'automaticSaveRemoveSubmitOrRoleChange':False,'backendSave500Fixed':False}
def regular(p):return p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p
@contextmanager
def finding_submit_guard_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_FINDING_BUILD_COPY_REQUIRED')
    target,origin=project/RELATIVE,reference/RELATIVE
    if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_FINDING_FILES_REQUIRED')
    raw=origin.read_bytes();updated,receipt=transform(raw)
    if target.read_bytes()!=raw:raise ValueError('FINDING_BUILD_COPY_DRIFT')
    target.write_bytes(updated);receipt.update(referenceChanged=False,sourceFileRestored=False)
    try:yield receipt
    finally:
        if target.read_bytes()!=updated:raise ValueError('FINDING_EXTERNAL_EDIT_PRESERVED')
        target.write_bytes(raw);receipt['sourceFileRestored']=True
