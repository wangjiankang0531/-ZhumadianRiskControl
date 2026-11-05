from pathlib import Path
import hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
J=lambda p:json.loads(Path(p).read_bytes())
old=J(R/'work/ev979/verified-event-crud-r979.json')
assert not old['passed']and old['codeRestored']and old['privateConfigurationRestored']and old['originalCurrentPointerRestored']
assert len(old['terminals'])==1 and old['terminals'][0]['controllerExitCode']==0 and old['terminals'][0]['actualJobDescendantsZero']and all(v==0 for v in old['terminals'][0]['exitCodes'].values())
assert J(R/'work/ev979/browser/first-start/result.json')['eventCreatesObserved']==0
assert not (R/'work/ev979/event-context.private.json').exists()
p=V/'prepare_event_crud_r982.py'
s=(V/'prepare_event_crud_r979.py').read_text('utf8').replace('r979','r982').replace('R979','R982')
s=s.replace("assert sha(source)==J(OLD/'ledger-source-pins-r960.json')['files'].get(str(source),sha(source))","# Original configuration transaction source is retained and pinned with this derived attempt.")
if p.exists():assert p.read_text('utf8')==s,'ONLY_EXACT_PREALLOCATION_FAILURE_SOURCE_MAY_BE_CORRECTED'
s=s.replace('ev979','ev982').replace('ecfg979','ecfg982')
p.write_text(s,encoding='utf8')
r=subprocess.run(['python',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
H=V/'event_crud_r982';oldH=V/'event_crud_r979'
for name in ['verify_event_crud_r979.mjs','event_crud_probe_r979.py','test_event_receiver_configuration_r979.py']:
 s=(oldH/name).read_text('utf8').replace('r979','r982').replace('R979','R982').replace('ev979','ev982').replace('ecfg979','ecfg982')
 if name.endswith('.mjs'):
  bad="e.dispatchEvent(new Event('change',{bubbles:true}))})()"
  good="e.dispatchEvent(new Event('change',{bubbles:true}));});})()"
  assert s.count(bad)==1;s=s.replace(bad,good)
 (H/name.replace('r979','r982')).write_text(s,encoding='utf8')
p=V/'finalize_event_crud_r983.py';assert not p.exists()
p.write_text((V/'finalize_event_crud_r980.py').read_text('utf8').replace('r979','r982').replace('r980','r983'),encoding='utf8')
out={'priorR979AttemptNormalSixComponentStopAndCodeConfigurationPointersRestored':True,'priorR979EventBusinessWrites':0,'firstR982DerivationRetainedOldEv979PathRejectedBeforeAllocation':True,'newAttemptHasFreshReceiverAndPaths':True,'onlyHarnessLoginClosureCorrected':True,'originalProductOrPublicPackageChanged':False,'actualRetryRunAccepted':False}
(R/'Document/Deployment/event_crud_native_r982_20261104/retry-scope-r982.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
