"""Restore original exam editor time and required identity from existing UI data.

Only edits an independent build copy; no schema, API, permission or Reference edit.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

RELATIVE='src/views/safetyBasic/trainingAssessmentInfo/components/List1/FormDialog.vue'
PIN='72cc138530ffdc0b27390938fcc3faa3fa8105881b70665d786b2677136a2c0d'
DATE_OLD='  form.field.dateList =\n'
DATE_NEW='  form.field.userTime =\n'
USERS_OLD='  userOptions.value = res.data.records;\n'
USERS_NEW='''  userOptions.value = res.data.records;
  if (form.field.userId && !form.field.idCard) {
    const selectedUser = userOptions.value.find(item => item.id === form.field.userId);
    if (selectedUser?.userCard) form.field.idCard = selectedUser.userCard;
  }
'''

def transform(raw):
    if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_TRAINING_ASSESSMENT_FORM_REQUIRED')
    newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8').replace('\r\n','\n')
    if text.count(DATE_OLD)!=1 or text.count(USERS_OLD)!=1:raise ValueError('EXACT_ORIGINAL_EXAM_BINDING_ANCHORS_REQUIRED')
    text=text.replace(DATE_OLD,DATE_NEW,1).replace(USERS_OLD,USERS_NEW,1)
    out=text.replace('\n',newline).encode('utf-8')
    return out,{'file':RELATIVE,'originalSHA256':PIN,'adaptedSHA256':sha256(out).hexdigest(),
      'timeEditorBoundToOriginalUserTime':True,'missingIdentityFromExistingSelectedUserOnly':True,
      'storedNameDepartmentScoreAndExamTimesPreserved':True,'requiredFieldsAndOriginalCallbackPreserved':True,
      'schemaAPIAndPermissionChanges':False}

def regular(p):return p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p

@contextmanager
def training_assessment_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_EXAM_BUILD_COPY_REQUIRED')
    target,origin=project/RELATIVE,reference/RELATIVE
    if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_EXAM_FILES_REQUIRED')
    raw=origin.read_bytes();adapted,receipt=transform(raw)
    if target.read_bytes()!=raw:raise ValueError('EXAM_BUILD_COPY_DRIFT')
    target.write_bytes(adapted);receipt.update(referenceChanged=False,sourceFileRestored=False)
    try:yield receipt
    finally:
        if target.read_bytes()!=adapted:raise ValueError('EXAM_EXTERNAL_EDIT_PRESERVED')
        target.write_bytes(raw);receipt['sourceFileRestored']=True
