"""Give the refreshed own browser a real click before testing its native beforeunload prompt."""
from pathlib import Path
import ast,json,re,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/fine_browser_original_r1748_20261107'
J=lambda p:json.loads(p.read_bytes())
r=J(R/'work/su1752/verified-result.json');t=J(D/'actual-parent-terminal-r1752.json');u=J(R/'work/su1752/ui-restart/result.json');h=J(R/'work/su1752/ui-restart/scene-file-http-summary.json')
assert not r['passed']and r['originalCodeRestored']and r['originalPointerRestored']and r['allActualJobsZeroBeforeClose']and t['actualOuterJobZero']and t['exitCode']==1
assert u['failure']=='WAIT_actual_normal_unsaved_leave_cancelled'and u['driverPhase']=='normal-unsaved-leave-cancel'and not u['dialogEvents']and h['successfulScenePOSTs']==0 and h['originalDLGPosts']==0
assert all(v==0 for v in r['actualTerminals'][0]['componentExitCodes'].values())
s=(V/'original_configuration_lifecycle_r1752.mjs').read_text('utf8');assert s.count(r'su1752\/ui-')==1;s=s.replace(r'su1752\/ui-',r'su1760\/ui-')
anchor=' await ev(`(()=>{const w=document.querySelector(\'iframe[title^="驻马店三维"]\').contentWindow,d=w.document,e=d.getElementById(\'model-overlay-x\');e.value=String(Number(e.value)+1);d.getElementById(\'model-overlay-apply\').click();})()`);'
assert s.count(anchor)==1
click=r'''
 const sceneTopicPoint=await ev(`(()=>{const f=document.querySelector('iframe[title^="驻马店三维"]'),r=f.getBoundingClientRect(),b=f.contentWindow.document.querySelector('[data-topic="scene-edit"]').getBoundingClientRect();if(!b.width||!b.height)throw Error('VISIBLE_SCENE_TOPIC_REQUIRED');return {x:r.left+f.clientLeft+b.left+b.width/2,y:r.top+f.clientTop+b.top+b.height/2};})()`);
 await send('Input.dispatchMouseEvent',{type:'mouseMoved',...sceneTopicPoint},editorSession);await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...sceneTopicPoint},editorSession);await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...sceneTopicPoint},editorSession);
 await until(()=>frameEval(`v.workspaceTopic==='scene-edit'&&!d.getElementById('model-overlay-panel').hidden&&d.getElementById('model-overlay-panel').getBoundingClientRect().width>0`),'VISIBLE_MODEL_PANEL_FOR_UNSAVED_EDIT');assert.equal(await frameEval('w.navigator.userActivation.hasBeenActive'),true);
'''
s=s.replace(anchor,click+anchor);s=s.replace('readOnlyExistingSceneAfterOriginalServiceRestart:true','readOnlyExistingSceneAfterOriginalServiceRestart:true,actualTrustedSceneTopicClickBeforeUnsavedLeave:true')
p=V/'original_configuration_lifecycle_r1760.mjs';assert not p.exists();p.write_text(s,encoding='utf8')
literal=re.search(r'if\(!(/\^D:.*?\$/)\.test\(O\)',s).group(1);probe=f"const r={literal};if(!r.test('D:/Project/Zhumadian/work/su1760/ui-restart')||r.test('D:/Project/Zhumadian/work/su1752/ui-restart'))throw Error('EXACT_NEW_SCOPE_REQUIRED');"
for args in [['--input-type=module','-e',probe],['--check',str(p)]]:
 cp=subprocess.run(['D:/Program Files/nodejs/node.exe',*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert cp.returncode==0
for old,new in [('run_original_configuration_lifecycle_r1752.py','run_original_configuration_lifecycle_r1760.py'),('launch_original_configuration_lifecycle_r1757.py','launch_original_configuration_lifecycle_r1760.py')]:
 s=(V/old).read_text('utf8').replace('r1752','r1760').replace('su1752','su1760');ast.parse(s);p=V/new;assert not p.exists();p.write_text(s,encoding='utf8')
proof={'prepared':True,'priorReadOnlyOriginalRestartAndRefreshConfirmed':True,'priorNativeBeforeunloadNotShownAndNoDialogRecorded':True,'freshNativeInputSceneTopicClickAndStickyUserActivationAssertionAdded':True,'modelControlsMustBeVisibleBeforeFreshUnsavedEdit':True,'beforeunloadProtectionProductAndFixedCandidateUntouched':True,'newDriverPathPositiveNegativeAndNodeSyntaxPassed':True,'originalEightNormal0ActualJobs0Restored':True,'scenePOSTsAllowed':0,'originalDLGPOSTsAllowed':0,'publicChanged':False}
p=D/'trusted-leave-driver-r1759.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
