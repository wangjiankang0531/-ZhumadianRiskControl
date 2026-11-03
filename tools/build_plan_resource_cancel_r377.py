from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,subprocess,sys,time
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
sys.path.insert(0,str(T));sys.dont_write_bytecode=True
memory=(ctypes.c_ulonglong*8)();memory[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>3*1024**3,'FULL_FRONTEND_BUILD_REQUIRES_THREE_GIB_AVAILABLE'
import build_avatar_full_r157_20261102 as base
from original_header_avatar_compat import header_avatar_override
from original_project_header_home_r167_20261102 import project_header_override
from original_workflow_pending_visibility_r178 import pending_visibility_override
from original_personal_workflow_routes_r195 import personal_workflow_override
from original_plan_exercise_retained_r221 import retained_plan_exercise_override
from original_task_attachment_guard_r224 import task_attachment_override
spec=importlib.util.spec_from_file_location('resource_cancel',V/'original_plan_resource_cancel_compat_r376.py');cancel_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cancel_module)
spec=importlib.util.spec_from_file_location('own_build_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
W=R/'work/plan-resource-cancel-r377';P=W/'source';assert not W.exists();W.mkdir()
component=base.J(R/'work/plan-resource-cancel-r375/candidate/result.json');assert component['passed']and component['actualUnhandledRejections']==0
before=base.own_copy(R/'work/user_feedback_20261031/emergency-workflow-source-r17/source',P)
failure=None;result=None
with(header_avatar_override(P)as avatar,project_header_override(P)as project,pending_visibility_override(P)as pending,
     personal_workflow_override(P)as workflow,retained_plan_exercise_override(P)as retained,task_attachment_override(P)as task,
     cancel_module.resource_cancel_override(P)as cancelled):
    actual=base.inventory(P);old=base.J(R/'work/user_feedback_20261031/plan-exercise-retained-r224/actual-compiled-source-files.json')
    changed={n for n in set(old)|set(actual)if old.get(n)!=actual.get(n)}
    expected={cancel_module.BASE+k+'.vue'for k in cancel_module.PINS};assert changed==expected
    base.dump(W/'actual-compiled-source-files.json',actual)
    for n in changed:
        out=W/'compiled-inputs'/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((P/n).read_bytes())
        kind=Path(n).stem;assert hashlib.sha256((P/n).read_bytes()).hexdigest()==hashlib.sha256((R/'work/plan-resource-cancel-r375/candidate-sources'/(kind+'.vue')).read_bytes()).hexdigest()
    with(W/'build.private.log').open('wb')as log:
        env={k:v for k,v in os.environ.items()if k not in ['NODE_OPTIONS','BROWSER']};env['BROWSER']='none'
        p=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=768',str(V/'build_plan_resource_cancel_r377.mjs')],stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p)
        print(json.dumps({'fullFrontendBuildStarted':True,'pid':p.pid,'memoryAvailableGiBBefore':round(memory[2]/1024**3,3),'nodeHeapLimitMiB':768,'changedSourceFiles':3,'noBackendOrDesktop':True}),flush=True)
        while p.poll()is None:
            try:p.wait(timeout=20)
            except subprocess.TimeoutExpired:print('OWN_FULL_FRONTEND_BUILD_STILL_LIVE_NO_FORCE_OR_RESTART',flush=True)
        while job.active_processes():time.sleep(.1)
        job.close();result={'nodeExitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False}
        base.dump(W/'build-terminal.json',result)
assert all([avatar['originalSourcesRestored'],project['sourceRestored'],pending['sourceRestored'],workflow['sourceRestored'],retained['sourceRestored'],task['sourceRestored'],cancelled['sourceRestored']])
assert base.inventory(P)==base.inventory(R/'work/user_feedback_20261031/emergency-workflow-source-r17/source')==before
base.dump(W/'source-restored.json',{'passed':True,'allSevenOverrideLayersRestored':True,'originalSourceTreeExact':True,'referenceRuntimeAndDatabaseUnchanged':True})
assert result['nodeExitCode']==0,'FULL_RESOURCE_CANCEL_FRONTEND_BUILD_FAILED_SOURCES_RESTORED'
files=base.inventory(W/'dist');assert files and(W/'dist/index.html').is_file()
proof={'passed':True,'changedSourcePaths':sorted(changed),'allOtherActualR224CompiledInputsKept':True,'actualComponentCandidateBytesEqualCompiledInputs':True,
 'compiledFiles':files,'fileCount':len(files),'resourceCancelOverride':cancelled,'nodeHeapLimitMiB':768,'actualNodeAndDescendantsNormalZero':True,
 'actualFullCompiled29CaseNormalRoleBrowserAccepted':False,'sameR39BackendClassPlannedButNotNewRuntimeProof':True,
 'r39FrozenManifestSHA256':hashlib.sha256((R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery-manifest.json').read_bytes()).hexdigest(),
 'public184FrozenManifestSHA256':hashlib.sha256((R/'Document/Deployment/public_source_plan_delivery_r369_20261103/public-git-sync-r369-manifest.json').read_bytes()).hexdigest(),
 'publicInstalledOrDesktopChanged':False,'fullCloneReady':False}
base.dump(W/'full-build-result.json',proof);print(json.dumps({'passed':True,'changedSources':3,'compiledFiles':len(files),'allOtherR224InputsKept':True,'normalRole29CaseStillPending':True,'actualDescendantsNormalZero':True}),flush=True)
