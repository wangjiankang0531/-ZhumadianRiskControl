"""Restore verified plan/exercise adaptations in an exact retained full frontend build."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import original_plan_report_frontend_compat as plan
import original_event_operations_frontend_compat as event
import original_attachment_upload_compat as upload
import original_emergency_detail_compat as detail
import original_exercise_list_compat as listing
import original_plan_resource_selection_compat as resources

T=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()

def transformations(before):
    updates={}
    name=plan.PINS['plan'][0]
    updates[name]=upload.form(plan.transform('plan',before[name])[0])
    name=event.PINS['exercise'][0]
    updates[name]=upload.form(event.transform('exercise',before[name])[0])
    for kind,name in detail.FILES.items():updates[name]=detail.transform(kind,before[name])
    updates[listing.REL]=listing.transform(before[listing.REL])[0]
    for kind in resources.PINS:
        name=resources.BASE+kind+'.vue'
        updates[name]=resources.transform(kind,before[name])[0]
    for name,pin in upload.SHARED.items():
        if sha(before[name])!=pin:raise ValueError('EXACT_SHARED_UPLOAD_SOURCE_REQUIRED')
    updates['src/components/Upload/Files.vue']=(T/'frontend/OriginalAttachmentFiles.vue').read_bytes()
    api=before['src/api/upload/index.ts'].decode('utf-8')
    api=upload.one(api,'uploadFile = params =>','uploadFile = (params, signal?: AbortSignal) =>')
    updates['src/api/upload/index.ts']=upload.one(api,'params);','params, { signal });').encode()
    for name,stored in {
        'src/components/Upload/OriginalAttachmentUploadState.ts':'OriginalAttachmentUploadState.ts',
        'src/components/Detail/OriginalEmergencyReadonlyDetail.ts':'OriginalEmergencyReadonlyDetail.ts',
        listing.HELPER:'OriginalExerciseListUsers.ts'
    }.items():updates[name]=(T/'frontend'/stored).read_bytes()
    if len(updates)!=13:raise ValueError('EXACT_THIRTEEN_RETAINED_SOURCE_PATHS_REQUIRED')
    return updates

@contextmanager
def retained_plan_exercise_override(project):
    project=Path(project).absolute()
    if project.resolve()!=project or not project.is_relative_to(Path('D:/Project/Zhumadian/work/user_feedback_20261031')):
        raise ValueError('ISOLATED_BUILD_COPY_ONLY')
    names=[plan.PINS['plan'][0],event.PINS['exercise'][0],*detail.FILES.values(),listing.REL,
           *[resources.BASE+k+'.vue'for k in resources.PINS],*upload.SHARED]
    before={n:(project/n).read_bytes()for n in names}
    updates=transformations(before)
    for n in updates:
        p=project/n
        if n not in before and p.exists():raise ValueError('HELPER_ALREADY_EXISTS')
        for q in [p,*p.parents]:
            if q.exists()and(q.is_symlink()or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('BUILD_REPARSE_REFUSED')
    receipt={'files':{n:{'beforeSHA256':sha(before[n])if n in before else None,'afterSHA256':sha(b)}for n,b in updates.items()},
             'sourceRestored':False,'onlyPlanExerciseResourceSelectorsReadonlyDetailsAndSharedUploadChanged':True,
             'taskFormsWorkflowLoginPermissionsAndBackendUnchanged':True}
    applied=[]
    try:
        for n,b in updates.items():
            p=project/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);applied.append(n)
        yield receipt
    finally:
        for n in applied:
            p=project/n
            if not p.exists()or p.read_bytes()!=updates[n]:raise ValueError('FOREIGN_RETAINED_SOURCE_CHANGE_PRESERVED')
        for n in applied:
            p=project/n
            if n in before:p.write_bytes(before[n])
            else:p.unlink()
        receipt['sourceRestored']=all((project/n).read_bytes()==b for n,b in before.items())and all(not(project/n).exists()for n in updates if n not in before)
