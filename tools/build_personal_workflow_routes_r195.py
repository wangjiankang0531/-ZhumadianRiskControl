from pathlib import Path
import sys,json,subprocess,datetime
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;T=R/'Application/tools';sys.dont_write_bytecode=True;sys.path[:0]=[str(V),str(T)]
import build_avatar_full_r157_20261102 as base
from original_header_avatar_compat import header_avatar_override
from original_project_header_home_r167_20261102 import project_header_override
from original_workflow_pending_visibility_r178 import pending_visibility_override
from original_personal_workflow_routes_r195 import personal_workflow_override,ROUTES,HOME,DONE,DONE_INFO
W=R/'work/user_feedback_20261031/personal-workflow-routes-r195';P=W/'source';assert not W.exists();W.mkdir();origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source';before=base.own_copy(origin,P)
with header_avatar_override(P)as avatar,project_header_override(P)as project,pending_visibility_override(P)as pending,personal_workflow_override(P)as workflow:
 captured=base.inventory(P);old=base.J(R/'work/user_feedback_20261031/workflow-pending-visibility-r178/actual-compiled-source-files.json');changed={n for n in set(old)|set(captured)if old.get(n)!=captured.get(n)};assert changed=={ROUTES,HOME,DONE,DONE_INFO},changed
 base.dump(W/'actual-compiled-source-files.json',captured)
 for n in [ROUTES,HOME,DONE,DONE_INFO]:p=W/'compiled-inputs'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((P/n).read_bytes())
 with(W/'build.log').open('wb')as log:run=base.normal_run(['D:/Program Files/nodejs/node.exe',str(V/'build_personal_workflow_routes_r195.mjs')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 assert run.returncode==0,'PERSONAL_WORKFLOW_FULL_BUILD_FAILED'
assert all([avatar['originalSourcesRestored'],project['sourceRestored'],pending['sourceRestored'],workflow['sourceRestored']])and base.inventory(P)==before and base.inventory(origin)==before
files=base.inventory(W/'dist');assert files and (W/'dist/index.html').is_file();proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'changedSourcePaths':sorted(changed),'exactR34OtherCompilerInputsKept':True,'originalLoginGuardAndNativeAPIsUnchanged':True,'adapters':[avatar,project,pending,workflow],'compiledFiles':files,'fileCount':len(files),'sourceRestored':True,'actualFullBrowserAccepted':False,'publicInstalled':False,'fullCloneReady':False};base.dump(W/'full-build-result.json',proof);print(json.dumps({'passed':True,'files':len(files),'changedSourcePaths':sorted(changed),'sourceRestored':True}))
