from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r4'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not P.exists()and not(C/'r4').exists()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert J(C/'r3/controller-terminal.json')['exitCode']==0 and J(C/'r3-outer-terminal.json')['actualDescendantsZeroBeforeClose']and J(C/'prepared-r3/configuration-restored.json')['exactOriginalBytesRestored']
failed=J(C/'r3/workflow-browser-operator-resubmit/failure.json');assert failed['message']=='REAL_NATIVE_APPROVE_ACTION_REQUIRED'and not any('/FlowBefore/Audit/'in h['path']for h in failed['http'])
assert J(C/'r3/workflow-browser-operator-resubmit/native-resubmit-before.json')['actualPendingRecords']==[{'nodeName':'OWN_APPLY','userName':'own_operator_a','handleStatus':18}]
p=V/'verify_native_return_serial_browser_r163_20261102.mjs';s=p.read_text(encoding='utf-8')
old='   if(!await evaluate(\'Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==="通过")\'))throw Error(\'REAL_NATIVE_APPROVE_ACTION_REQUIRED\');'
assert s.count(old)==1
new=r'''   const actualAuditAction=wire.phaseName==='operator-resubmit'?'提交审核':'通过';
   await fs.writeFile(O+'/native-audit-actions-before-submit.json',JSON.stringify({expectedOriginalAction:actualAuditAction,actions:await evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio")).filter(e=>e.getClientRects().length).map(e=>({label:e.textContent.trim(),checked:e.classList.contains("is-checked")}))'),noSubmitYet:true},null,2));
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==='+JSON.stringify(actualAuditAction)+')'));
'''
s=s.replace(old,new);p.write_text(s,encoding='utf-8')
runner=(V/'run_return_resubmit_r165_20261102.py').read_text(encoding='utf-8').replace("attempt='r3'","attempt='r4'");ast.parse(runner);(V/'run_native_submit_r166_20261102.py').write_text(runner,encoding='utf-8')
scope=J(C/'prepared-r3/temporary-synthetic-config-scope.json');before={name:(A/name).read_bytes()for name in scope['files']};assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['beforeSHA256']for name,raw in before.items())
cfg=json.loads(before['private/server-configuration.json']);assert cfg['configuration']['business']['flow.code']==cfg['configuration']['business']['flow.event-task-handle']=='OWN_FORM_CODE';cfg['configuration']['business']['flow.code']=cfg['configuration']['business']['flow.event-task-handle']='OWN_SERIAL_R163_r1'
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();changed={'private/server-configuration.json':enc(cfg)};payload=json.loads(before['payload-manifest.json']);payload['files']['private/server-configuration.json']={'bytes':len(changed['private/server-configuration.json']),'sha256':hashlib.sha256(changed['private/server-configuration.json']).hexdigest()};changed['payload-manifest.json']=enc(payload);release=json.loads(before['release-manifest.json']);release['payloadManifestSHA256']=hashlib.sha256(changed['payload-manifest.json']).hexdigest();changed['release-manifest.json']=enc(release)
assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['afterSHA256']for name,raw in changed.items())
P.mkdir()
for name,raw in before.items():p=P/'before'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in ['own-serial-definition.json','controller-fixture-ready.json','temporary-synthetic-config-scope.json']:(P/name).write_bytes((C/'prepared-r3'/name).read_bytes())
(P/'workflow-context.private.json').write_bytes((C/'r3/workflow-context.private.json').read_bytes())
for name,raw in changed.items():p=A/name;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(raw)
(P/'continued-prior-evidence.json').write_text(json.dumps({'sameOriginalCreatedDisposedAndReturnedInstance':True,'priorAttemptDidNotSubmitAudit':True,'actualOriginalApplicantAction':'提交审核','browserSHA256':sha(V/'verify_native_return_serial_browser_r163_20261102.mjs'),'hostSHA256':sha(V/'verify_full_controller_return_serial_r163_20261102.py'),'runnerSHA256':sha(V/'run_native_submit_r166_20261102.py'),'contextSHA256':sha(P/'workflow-context.private.json'),'onlySameOwnFakeConfigurationReapplied':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sameReturnedInstancePrepared':True,'originalApplicantSubmitActionMatchedActualUI':True,'noPriorResubmitRequestReplayed':True,'newProductOrPublicChange':False}))
