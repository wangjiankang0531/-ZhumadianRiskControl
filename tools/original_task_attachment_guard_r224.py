"""Compose attachment readiness with the exact current task submit lock and confirmed-save behavior."""
from pathlib import Path
from contextlib import contextmanager
import hashlib
REL='src/views/emergencyResponse/taskSend/info/addOrEdit.vue'
PIN='051b321836b877e2f9caac77e5092b9db5b3f5d4960bad5b4c9461e4c708704a'
sha=lambda b:hashlib.sha256(b).hexdigest()
def transform(raw):
 if sha(raw)!=PIN:raise ValueError('EXACT_RETAINED_TASK_SUBMIT_FORM_REQUIRED')
 s=raw.decode('utf-8')
 def once(a,b):
  nonlocal s
  if s.count(a)!=1:raise ValueError('EXACT_TASK_ATTACHMENT_ANCHOR_REQUIRED')
  s=s.replace(a,b)
 once('<UploadFiles v-model:fileList="fileList" />','<UploadFiles ref="attachmentRef" v-model:fileList="fileList" :disabled="submitting" />')
 once('const fileList = ref','const attachmentRef = ref<InstanceType<typeof UploadFiles> | null>(null);\nconst fileList = ref')
 once('  if (submitting.value) return false;','  if (submitting.value || !attachmentRef.value?.ensureReady()) return false;')
 once('    if (!(await formRef.value!.validate())) return false;','    if (!(await formRef.value!.validate())) return false;\n    if (!attachmentRef.value?.ensureReady()) return false;')
 return s.encode('utf-8')
@contextmanager
def task_attachment_override(project):
 project=Path(project).absolute();p=project/REL
 if project.resolve()!=project or not project.is_relative_to(Path('D:/Project/Zhumadian/work/user_feedback_20261031')):raise ValueError('OWN_BUILD_ONLY')
 for q in [p,*p.parents]:
  if q.exists()and(q.is_symlink()or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('NO_REPARSE')
 before=p.read_bytes();after=transform(before)
 receipt={'path':REL,'beforeSHA256':sha(before),'afterSHA256':sha(after),'currentSubmitLockAndConfirmedSaveAndNativeWorkflowKept':True,'sourceRestored':False}
 p.write_bytes(after)
 try:yield receipt
 finally:
  if p.read_bytes()!=after:raise ValueError('FOREIGN_TASK_CHANGE_PRESERVED')
  p.write_bytes(before);receipt['sourceRestored']=p.read_bytes()==before
