"""Retain failed pre-browser scope proof; use a precise fresh driver output path."""
from pathlib import Path
import ast,json,re,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/fine_browser_original_r1748_20261107'
J=lambda p:json.loads(p.read_bytes())
r=J(R/'work/su1751/verified-result.json');t=J(D/'actual-parent-terminal-r1751.json')
assert not r['passed']and r['originalCodeRestored']and r['originalPointerRestored']and r['allActualJobsZeroBeforeClose']and t['exitCode']==1 and t['actualOuterJobZero']
assert all(v==0 for v in r['actualTerminals'][0]['componentExitCodes'].values())and not(R/'work/su1751/ui-restart').exists()
stderr=(R/'work/su1751/ui-restart.stderr.private.log').read_text('utf8');assert 'Error: EXACT_OWN_ORIGINAL_SCENE_SCOPE_REQUIRED'in stderr
s=(V/'original_configuration_lifecycle_r1751.mjs').read_text('utf8');old=r'su1749\/ui-';assert s.count(old)==1;s=s.replace(old,r'su1752\/ui-')
assert s.count("readFile('D:/Project/Zhumadian/work/su1749/scene-file-write-intent.private.json'")==1
assert "scene-file-write-intent.private.json',JSON.stringify"not in s
p=V/'original_configuration_lifecycle_r1752.mjs';assert not p.exists();p.write_text(s,encoding='utf8')
literal=re.search(r'if\(!(/\^D:.*?\$/)\.test\(O\)',s).group(1)
check=f"const r={literal};if(!r.test('D:/Project/Zhumadian/work/su1752/ui-restart')||r.test('D:/Project/Zhumadian/work/su1751/ui-restart')||r.test('D:/Project/Zhumadian/work/su1749/ui-restart'))throw Error('EXACT_NEW_DRIVER_SCOPE_REQUIRED');"
cp=subprocess.run(['D:/Program Files/nodejs/node.exe','--input-type=module','-e',check],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert cp.returncode==0
cp=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert cp.returncode==0
for old,new in [('run_original_configuration_lifecycle_r1751.py','run_original_configuration_lifecycle_r1752.py'),('launch_original_configuration_lifecycle_r1751.py','launch_original_configuration_lifecycle_r1752.py')]:
 s=(V/old).read_text('utf8').replace('r1751','r1752').replace('su1751','su1752')
 if new.startswith('run_'):
  anchor="value=json.loads(out);out=b'';save('normal-login-'"
  assert s.count(anchor)==1;s=s.replace(anchor,"assert out.strip(),'NORMAL_LOGIN_DRIVER_EMPTY_OUTPUT_CHECK_OWN_PRIVATE_TERMINAL';value=json.loads(out);out=b'';save('normal-login-'")
 ast.parse(s);p=V/new;assert not p.exists();p.write_text(s,encoding='utf8')
proof={'prepared':True,'failedR1751DriverScopeBeforeBrowserNoScenePOST':True,'failedOriginalEightNormal0JobsZeroCodePointerRestored':True,'newOutputScopePositiveAndTwoPriorNegativeNodeChecksPassed':True,'sameConfirmedSceneOnlyRead':True,'productAndOriginalLifecycleChanges':False,'originalSourceAndFailureRetained':True,'publicChanged':False}
p=D/'readonly-driver-scope-r1752.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
