from contextlib import contextmanager
from pathlib import Path
from hashlib import sha256
from original_event_creation_frontend_compat import PINS,transform

EVENT_REL=PINS['event'][0]
@contextmanager
def event_form_result_override(project):
 project=Path(project).absolute();expected=Path('D:/Project/Zhumadian/work/user_feedback_20261031/event-research-level-r418/source')
 if project!=expected or project.resolve()!=project:raise ValueError('EXACT_EXISTING_COMPLETE_BUILD_SOURCE_REQUIRED')
 p=project/EVENT_REL
 for q in [p,*p.parents]:
  if q.exists()and(q.is_symlink()or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('EVENT_FORM_REPARSE_REFUSED')
 before=p.read_bytes()
 if sha256(before).hexdigest()!=PINS['event'][1]:raise ValueError('EXACT_UNADAPTED_EVENT_FORM_REQUIRED')
 after=transform('event',before)
 receipt={'path':EVENT_REL,'beforeSHA256':sha256(before).hexdigest(),'adaptedSHA256':sha256(after).hexdigest(),'existingBooleanWriteAndDetailGuardReused':True,'sourceRestored':False}
 p.write_bytes(after)
 try:yield receipt
 finally:
  if p.read_bytes()!=after:raise ValueError('FOREIGN_EVENT_FORM_CHANGE_PRESERVED')
  p.write_bytes(before);receipt['sourceRestored']=p.read_bytes()==before
