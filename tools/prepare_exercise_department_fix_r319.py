from pathlib import Path
import ast,hashlib,json,subprocess

R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/exercise_department_frontend_candidate_r319_20261103'
assert not D.exists()
old=R/'work/user_feedback_20261031/plan-exercise-retained-r224'
rel='src/views/emergencyPlans/structured/info/exerciseList.vue'
raw=(old/'compiled-inputs'/rel).read_bytes()
pin=json.loads((old/'actual-compiled-source-files.json').read_bytes())[rel]['sha256']
assert hashlib.sha256(raw).hexdigest()==pin and raw.count(b'v-model={searchParam.department}')==1

adapter='''"""Bind original exercise department search to its actual backend query field."""
from contextlib import contextmanager
from pathlib import Path
from hashlib import sha256

REL='src/views/emergencyPlans/structured/info/exerciseList.vue'
PIN=__PIN__

@contextmanager
def exercise_department_override(project):
    root=Path(project).absolute()
    allowed=Path('D:/Project/Zhumadian/work/user_feedback_20261031')
    if root.resolve()!=root or not root.is_relative_to(allowed):
        raise ValueError('ISOLATED_EXERCISE_FILTER_BUILD_ONLY')
    file=root/REL
    for parent in [file,*file.parents]:
        if parent.exists()and(parent.lstat().st_file_attributes&1024):
            raise ValueError('EXERCISE_FILTER_REPARSE_REFUSED')
        if parent==root:break
    before=file.read_bytes()
    if sha256(before).hexdigest()!=PIN:
        raise ValueError('EXACT_ACTUAL_COMPILED_EXERCISE_LIST_REQUIRED')
    anchor=b'v-model={searchParam.department}'
    if before.count(anchor)!=1:raise ValueError('EXACT_EXERCISE_DEPARTMENT_BINDING_REQUIRED')
    after=before.replace(anchor,b'v-model={searchParam.organizeDepartment}',1)
    receipt={'path':REL,'beforeSHA256':sha256(before).hexdigest(),'afterSHA256':sha256(after).hexdigest(),
             'onlyOriginalBackendQueryFieldBindingChanged':True,'sourceRestored':False}
    try:
        file.write_bytes(after)
        yield receipt
    finally:
        if file.read_bytes()!=after:raise ValueError('FOREIGN_EXERCISE_FILTER_SOURCE_CHANGE_PRESERVED')
        file.write_bytes(before)
        receipt['sourceRestored']=file.read_bytes()==before
'''.replace('__PIN__',repr(pin))
builder=(T/'build_plan_exercise_retained_r224.py').read_text(encoding='utf-8')
builder=builder.replace("from original_task_attachment_guard_r224 import task_attachment_override, REL as TASK", "from original_task_attachment_guard_r224 import task_attachment_override, REL as TASK\nfrom original_exercise_department_filter_r319 import exercise_department_override, REL as FILTER")
builder=builder.replace("plan-exercise-retained-r224';P=", "exercise-department-filter-r319';P=")
anchor='task_attachment_override(P)as task:'
assert builder.count(anchor)==1;builder=builder.replace(anchor,'task_attachment_override(P)as task,exercise_department_override(P)as department:')
anchor="    base.dump(W/'actual-compiled-source-files.json',actual)"
assert builder.count(anchor)==1
builder=builder.replace(anchor,"    prior=base.J(R/'work/user_feedback_20261031/plan-exercise-retained-r224/actual-compiled-source-files.json')\n    assert {n for n in set(prior)|set(actual)if prior.get(n)!=actual.get(n)}=={FILTER}\n"+anchor)
builder=builder.replace("str(T/'build_plan_exercise_retained_r224.mjs')", "str(T/'build_exercise_department_filter_r319.mjs')")
builder=builder.replace("task['sourceRestored']])", "task['sourceRestored'],department['sourceRestored']])")
builder=builder.replace("'retainedAdaptations':retained,", "'exerciseDepartmentFilter':department,'onlyOneInputComparedWithR224Changed':True,'retainedAdaptations':retained,")
node=(T/'build_plan_exercise_retained_r224.mjs').read_text(encoding='utf-8').replace('plan-exercise-retained-r224','exercise-department-filter-r319')
sources={'original_exercise_department_filter_r319.py':adapter,'build_exercise_department_filter_r319.py':builder,
         'build_exercise_department_filter_r319.mjs':node}
D.mkdir();pins={}
for name,text in sources.items():
    if name.endswith('.py'):ast.parse(text,filename=name)
    p=T/name;assert not p.exists();p.write_text(text,encoding='utf-8');pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
checked=subprocess.run(['node','--check',str(T/'build_exercise_department_filter_r319.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert checked.returncode==0
(D/'source-preparation-r319.json').write_text(json.dumps({'prepared':True,'sourcePins':pins,'exactPriorFrontendInputSHA256':pin,
 'onlyOrganizeDepartmentFieldBindingChanged':True,'candidateCompiledOrInstalled':False,'publicOrFormalOrDesktopChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'sources':len(pins),'onlyOneFieldBindingChanged':True,'candidateCompiledOrInstalled':False}))
