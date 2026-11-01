"""Keep native duty log inputs when selected personnel options have not loaded yet."""
import hashlib
REL='src/views/dutyManage/dutyLog/info/addOrEdit.vue'
INPUT_SHA256='32b961fe51486c3f4320e843f0f8f74cb5421bf4ab81d9dacc84f47316a474b2'
def transform(raw):
    before=hashlib.sha256(raw).hexdigest()
    if before!=INPUT_SHA256:raise ValueError('ORIGINAL_DUTY_LOG_CONTEXT_CHANGED')
    anchor=b'  const dutyPersonnelId = field.value.dutyPersonnelId;'
    mapping=b'dutyPersonnelId.map(el => userList.value.find(item => item.personId == el).name).join(",")'
    if raw.count(anchor)!=1 or raw.count(mapping)!=1:raise ValueError('ORIGINAL_DUTY_LOG_ANCHOR_CHANGED')
    eol=b'\r\n'if b'\r\n'in raw else b'\n'
    guard=eol.join([b'',b'  const selectedPeople = dutyPersonnelId.map(el => userList.value.find(item => item.personId == el));',b'  if (selectedPeople.some(item => !item)) {','    ElMessage.warning("值班人员信息尚未加载完成，请等待加载或重新选择人员后提交。");'.encode(),b'    return;',b'  }'])
    after=raw.replace(anchor,anchor+guard,1).replace(mapping,b'selectedPeople.map(item => item.name).join(",")',1)
    return after,{'beforeSHA256':before,'afterSHA256':hashlib.sha256(after).hexdigest(),'missingOptionsShowNoticeWithoutWriteAndKeepInputs':True,'validSelectedPeopleNamesIDsOrderAndSaveResultGuardKept':True}
