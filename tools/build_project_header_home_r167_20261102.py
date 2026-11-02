from pathlib import Path
import sys,json,subprocess,datetime
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
import build_avatar_full_r157_20261102 as base
from original_header_avatar_compat import header_avatar_override,HEADER,EXTRA
from original_project_header_home_r167_20261102 import project_header_override,LAYOUT,ROUTES,ICON
W=R/'work/user_feedback_20261031/project-header-home-r167';P=W/'source'
assert not W.exists();W.mkdir()
origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'
before=base.own_copy(origin,P)
with header_avatar_override(P) as avatar,project_header_override(P) as project:
 captured=base.inventory(P);previous=base.J(R/'work/user_feedback_20261031/avatar-full-r157/emergency_pc/actual-compiled-source-files.json')
 changed={n for n in set(previous)|set(captured) if previous.get(n)!=captured.get(n)}
 assert changed=={LAYOUT,ROUTES,ICON},changed
 base.dump(W/'actual-compiled-source-files.json',captured)
 with (W/'build.log').open('wb') as log:
  run=base.normal_run(['D:/Program Files/nodejs/node.exe',str(T/'build_project_header_home_r167_20261102.mjs')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 assert run.returncode==0,'PROJECT_HEADER_FULL_BUILD_FAILED'
assert avatar['originalSourcesRestored'] and project['sourceRestored'] and base.inventory(P)==before and base.inventory(origin)==before
files=base.inventory(W/'dist');assert files and (W/'dist/index.html').is_file()
proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'previousR32ExactCompilerInputsCompared':True,'onlyThreeDeclaredSourcePathsChanged':sorted(changed),'sourceRestored':True,'avatarAdapter':avatar,'projectHeaderAdapter':project,'compiledFiles':files,'fileCount':len(files),'referenceFormalOrPublicChanged':False,'actualFullCompiledBrowserPassed':False,'fullCloneReady':False}
base.dump(W/'full-build-result.json',proof);print(json.dumps({'passed':True,'fileCount':len(files),'changedSourcePaths':sorted(changed),'sourceRestored':True}))
