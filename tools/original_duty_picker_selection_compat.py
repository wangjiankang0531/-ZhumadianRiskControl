"""Preserve original duty personnel picker, with explicit feedback for an empty selection."""
import hashlib
REL='src/views/dutyManage/dutySchedule/info/personList.vue'
INPUT_SHA256='85c4745be3137ca5770ad3f0f70fd1f4bef2841959578aeb707c79583aa6d1ee'
def transform(raw):
    before=hashlib.sha256(raw).hexdigest()
    if before!=INPUT_SHA256:raise ValueError('ORIGINAL_DUTY_PICKER_INPUT_CHANGED')
    old=b'// import { ElMessage } from "element-plus";'
    anchor=b'  const { id, name, phoneNumber, jobTitle, gender, age, personDept } = nowRow;'
    if raw.count(old)!=1 or raw.count(anchor)!=1:raise ValueError('ORIGINAL_DUTY_PICKER_ANCHOR_CHANGED')
    eol=b'\r\n'if b'\r\n'in raw else b'\n'
    guard=eol.join([b'  if (!nowRow) {','    ElMessage.warning("请选择值班人员");'.encode(),b'    return;',b'  }',b''])
    after=raw.replace(old,b'import { ElMessage } from "element-plus";',1).replace(anchor,guard+anchor,1)
    return after,{'beforeSHA256':before,'afterSHA256':hashlib.sha256(after).hexdigest(),'onlyOriginalImportAndEmptySelectionGuardChanged':True,'originalSelectionEmissionAndDialogCloseKept':True}
