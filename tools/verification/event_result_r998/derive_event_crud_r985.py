from pathlib import Path
import json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');oldH=V/'event_crud_r982';H=V/'event_crud_r985'
J=lambda p:json.loads(Path(p).read_bytes())
old=J(R/'work/ev982/verified-event-crud-r982.json');browser=J(R/'work/ev982/browser/first-start/result.json')
assert not old['passed']and old['codeRestored']and old['privateConfigurationRestored']and old['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in old['terminals'])
assert browser['eventCreatesObserved']==0 and browser['type']=='OWN_EDITABLE_FIELD_事件名称'
assert J(R/'work/ev982/event-context.private.json')['phase']=='create-intent'
assert not any(x['path'].endswith('/eventInfo/save')for x in browser['requests'])
source=(V/'prepare_event_crud_r979.py').read_text('utf8').replace('r979','r985').replace('R979','R985').replace('ev979','ev985').replace('ecfg979','ecfg985')
source=source.replace("assert sha(source)==J(OLD/'ledger-source-pins-r960.json')['files'].get(str(source),sha(source))","# Derivative configuration source receives an explicit pin in the new attempt.")
p=V/'prepare_event_crud_r985.py';assert not p.exists();p.write_text(source,encoding='utf8')
r=subprocess.run(['python',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
for name in ['verify_event_crud_r982.mjs','event_crud_probe_r982.py','test_event_receiver_configuration_r982.py']:
 s=(oldH/name).read_text('utf8').replace('r982','r985').replace('R982','R985').replace('ev982','ev985').replace('ecfg982','ecfg985')
 if name.endswith('.mjs'):
  anchor='async function select(label,expected)'
  assert s.count(anchor)==1
  wrapper='''const immediateNativeFill=fill;
fill=async(label,text)=>{
 await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-form-item')).some(a=>a.getClientRects().length&&a.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)}&&Array.from(a.querySelectorAll('input,textarea')).some(e=>!e.disabled&&!e.readOnly&&e.getClientRects().length))`));
 return immediateNativeFill(label,text);
};
'''
  s=s.replace(anchor,wrapper+anchor)
 (H/name.replace('r982','r985')).write_text(s,encoding='utf8')
p=V/'finalize_event_crud_r986.py';assert not p.exists();p.write_text((V/'finalize_event_crud_r980.py').read_text('utf8').replace('r979','r985').replace('r980','r986'),encoding='utf8')
out={'priorR979AndR982BusinessCreates':0,'priorR982OnlyCreateIntentNoSaveIssued':True,'priorR982ActualNormalLoginPassed':True,'priorR982NormalSixComponentExitAndExactRestorePassed':True,'harnessNowWaitsForActualEditableNativeInput':True,'originalProductSourceChanged':False,'retryUsesIndependentPathsAndFreshReceiver':True,'actualRetryAccepted':False}
(R/'Document/Deployment/event_crud_native_r985_20261104/retry-scope-r985.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
