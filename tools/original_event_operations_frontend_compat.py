"""Preserve original event/exercise forms unless their Boolean SDK write succeeds."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from original_confirmed_operation_compat import regular,replace_owned
PINS={
 'disposal':('src/views/emergencyResponse/disposal/components/DisposalDialog.vue','d2618046b9c741a915fb0033952ec461177e7353984613429322004a0927e320'),
 'exercise':('src/views/emergencyPlans/structured/components/exerciseDialog.vue','5b0692738a87c9a6fd2be43536952ef28f918e70ada2d46edb67f459c9eaa997'),
 'eventDetail':('src/views/emergencyResponse/response/info/detail.vue','96f79d5373bdf2c7580abde20e95908d87f6e3c20c91f608b0ac2b055b2a36eb')}
NOTICE='操作未完成，请保留当前内容，核对事件、处置或演练记录状态后重试。'
def request(expression):
 return '''  let response: any;
  try {
    response = await '''+expression+''';
  } catch {
    return false;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("'''+NOTICE+'''");
    return false;
  }
'''
def one(text,old,new):
 if text.count(old)!=1:raise ValueError('EXACT_ORIGINAL_EVENT_OPERATION_ANCHOR_REQUIRED')
 return text.replace(old,new,1)
def transform(kind,raw):
 if kind not in PINS or sha256(raw).hexdigest()!=PINS[kind][1]:raise ValueError('PINNED_ORIGINAL_EVENT_OPERATION_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf8').replace('\r\n','\n');guards=1
 if kind=='disposal':text=one(text,'  await dialogProps.value.api!(params);\n',request('dialogProps.value.api!(params)'))
 elif kind=='exercise':
  text=one(text,'    participants: field.value.personIds.join(",")','    participants: (field.value.personIds ?? []).join(",")');text=one(text,'  await save(params);\n',request('save(params)'))
 else:
  text=one(text,'  await api(fieldJudge.value);\n',request('api(fieldJudge.value)'));start=text.index('const handleDel = row => {');end=text.index('\n};',start)+3;old=text[start:end];confirmStart=old.index('  ElMessageBox.confirm(');confirmEnd=old.index(').then(async () => {',confirmStart);confirm=old[confirmStart:confirmEnd+1];success=old[old.index('    init();'):old.index('\n  });')];new='''const handleDel = async row => {
  try {
'''+confirm.replace('  ElMessageBox.confirm(','    await ElMessageBox.confirm(',1)+''';
  } catch {
    return false;
  }
'''+request('removeDisposeById({ id: row.id })')+success.replace('    ','  ')+'''
  return true;
};''';text=one(text,old,new);guards=2
 updated=text.replace('\n',nl).encode('utf8');return updated,{'kind':kind,'file':PINS[kind][0],'originalSHA256':PINS[kind][1],'adaptedSHA256':sha256(updated).hexdigest(),'guardedWriteCalls':guards,'onlyCodeZeroBooleanTrueContinues':True,'APIRejectionKeepsInputsAndDoesNotDuplicateRequestLayerNotice':True,'originalTemplateStylesValidationAndPayloadPreserved':True,'optionalMissingParticipantsBecomeEmptyCSV':kind=='exercise','detailDeleteCancelSettlesWithoutMutation':kind=='eventDetail'}
def prepare(project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_EVENT_OPERATION_BUILD_COPY_REQUIRED')
 plans=[]
 for kind,(rel,pin) in PINS.items():
  target,origin=project/rel,reference/rel;regular(target);regular(origin)
  if target.samefile(origin) or target.read_bytes()!=origin.read_bytes():raise ValueError('EVENT_OPERATION_BUILD_COPY_DRIFT')
  raw=origin.read_bytes();updated,row=transform(kind,raw);plans.append((target,raw,updated,row))
 return plans,{'files':[row[3] for row in plans],'guardedWriteCalls':4,'allSourcesPrevalidated':True,'referenceChanged':False,'sourceFilesRestored':False}
@contextmanager
def event_operation_override(project,reference):
 plans,receipt=prepare(project,reference);applied=[]
 try:
  for target,raw,updated,row in plans:replace_owned(target,raw,updated);applied.append((target,raw,updated))
  yield receipt
 finally:
  errors=[]
  for target,raw,updated in reversed(applied):
   try:replace_owned(target,updated,raw)
   except Exception as error:errors.append({'file':str(target),'error':type(error).__name__})
  receipt['sourceFilesRestored']=not errors;receipt['externalEditsPreserved']=errors
  if errors:raise ValueError('EXTERNAL_EVENT_OPERATION_EDITS_PRESERVED:'+str(errors))
