from pathlib import Path
import sys,json,subprocess,datetime
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T));sys.dont_write_bytecode=True
import build_avatar_full_r157_20261102 as base
from original_header_avatar_compat import header_avatar_override
from original_project_header_home_r167_20261102 import project_header_override
from original_workflow_pending_visibility_r178 import pending_visibility_override
from original_personal_workflow_routes_r195 import personal_workflow_override
from original_plan_exercise_retained_r221 import retained_plan_exercise_override
from original_task_attachment_guard_r224 import task_attachment_override, REL as TASK
from original_exercise_department_filter_r319 import exercise_department_override, REL as FILTER
W=R/'work/user_feedback_20261031/exercise-department-filter-r319';P=W/'source'
assert not W.exists();W.mkdir()
origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source';before=base.own_copy(origin,P)
with header_avatar_override(P)as avatar,project_header_override(P)as project,pending_visibility_override(P)as pending,personal_workflow_override(P)as workflow,retained_plan_exercise_override(P)as retained,task_attachment_override(P)as task,exercise_department_override(P)as department:
    actual=base.inventory(P);old=base.J(R/'work/user_feedback_20261031/personal-workflow-routes-r195/actual-compiled-source-files.json')
    changed={n for n in set(old)|set(actual)if old.get(n)!=actual.get(n)}
    assert changed==set(retained['files'])|{TASK} and len(changed)==14
    prior=base.J(R/'work/user_feedback_20261031/plan-exercise-retained-r224/actual-compiled-source-files.json')
    assert {n for n in set(prior)|set(actual)if prior.get(n)!=actual.get(n)}=={FILTER}
    base.dump(W/'actual-compiled-source-files.json',actual)
    for n in changed:
        q=W/'compiled-inputs'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((P/n).read_bytes())
    with(W/'build.log').open('wb')as log:
        built=base.normal_run(['D:/Program Files/nodejs/node.exe',str(T/'build_exercise_department_filter_r319.mjs')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert built.returncode==0,'RETAINED_PLAN_EXERCISE_FULL_BUILD_FAILED'
assert all([avatar['originalSourcesRestored'],project['sourceRestored'],pending['sourceRestored'],workflow['sourceRestored'],retained['sourceRestored'],task['sourceRestored'],department['sourceRestored']])
assert base.inventory(P)==base.inventory(origin)==before
files=base.inventory(W/'dist');assert files and(W/'dist/index.html').is_file()
js=b'\n'.join(p.read_bytes()for p in(W/'dist').rglob('*.js'))
for notice in ['保存未完成，请保留当前内容，核对应急预案或事件报送后重试。','EXERCISE_LIST_NAMES_UNCONFIRMED','请上传文件，全部上传完成后再提交']:
    assert notice.encode()in js,notice
proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'changedSourcePaths':sorted(changed),
       'allOtherActualR35CompiledInputsKept':True,'currentWorkflowAndOriginalLoginSourcePinsUnchanged':True,'onlyTaskAttachmentReadinessComposedWithExistingTaskGuards':True,
       'exerciseDepartmentFilter':department,'onlyOneInputComparedWithR224Changed':True,'retainedAdaptations':retained,'taskAttachmentReadiness':task,'compiledFiles':files,'fileCount':len(files),'sourceRestored':True,
       'baselineMissingRetainedPlanAndExerciseGuardsConfirmedInCompiledChunk':True,
       'actualNormalRoleBrowserAccepted':False,'publicInstalled':False,'fullCloneReady':False}
base.dump(W/'full-build-result.json',proof)
print(json.dumps({'passed':True,'compiledFiles':len(files),'changedSourcePaths':len(changed),'allOtherR35SourcePinsKept':True,'actualNativeBrowserStillPending':True}))
