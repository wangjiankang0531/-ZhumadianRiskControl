from pathlib import Path
import json,hashlib,ast,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r2'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not P.exists()and not(C/'r2').exists()
assert J(C/'r1/controller-terminal.json')['exitCode']==0 and J(C/'r1-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert J(C/'prepared-r1/configuration-restored.json')['exactOriginalBytesRestored']
for phase in ['operator','operator-disposal']:assert J(C/f'r1/workflow-browser-{phase}/result.json')['passed']and J(C/f'r1/state-{phase}.json')['passed']
failed=J(C/'r1/workflow-browser-reviewer-first/failure.json');assert failed['message']=='ORIGINAL_CONFIGURED_RETURN_NODE_MUST_BE_SELECTED'and not any('/FlowBefore/Reject/'in h['path']for h in failed['http'])
context=J(C/'r1/workflow-context.private.json');assert context['syntheticDataOnly']and context['taskName']=='Own serial workflow R163 r1'
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
p=V/'verify_native_return_serial_browser_r163_20261102.mjs';s=p.read_text(encoding='utf-8')
old='   const target=await evaluate('
assert s.count(old)==1
wait=r'''   const definition=JSON.parse(await fs.readFile(root+'/own-serial-definition.json','utf8'));const configuredStart=JSON.parse(JSON.parse(definition.templateBody.flowTemplateJson)[0].flowTemplateJson).properties.title;
   await until(()=>evaluate('(()=>{const f=Array.from(document.querySelectorAll(".audit-form .el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="退回节点");return !!f&&f.textContent.includes('+JSON.stringify(configuredStart)+')})()'));
'''
s=s.replace(old,wait+old,1)
s=s.replace('selectedText:f?.querySelector(".el-select__selected-item")?.textContent.trim()||i?.value||"",','selectedText:Array.from(f?.querySelectorAll(".el-select__selected-item")||[]).map(e=>e.textContent.trim()).find(v=>v.includes('+"'+JSON.stringify(configuredStart)+'"+'))||i?.value||(f?.textContent.includes('+"'+JSON.stringify(configuredStart)+'"+')?'+"'+JSON.stringify(configuredStart)+'"+':""),')
# Prefer the verified displayed configured node over any hidden editable search input.
s=s.replace("if(!target.present||!target.selectedText||/请选择/.test(target.selectedText))", "if(!target.present||!target.selectedText||!target.selectedText.includes(configuredStart))")
p.write_text(s,encoding='utf-8')
host=V/'verify_full_controller_return_serial_r163_20261102.py';h=host.read_text(encoding='utf-8')
h=h.replace("parser.add_argument('--closed-readback-only',action='store_true');options=parser.parse_args()","parser.add_argument('--closed-readback-only',action='store_true');parser.add_argument('--return-existing-pending',action='store_true');options=parser.parse_args()")
h=h.replace("if options.closed_readback_only:(root/'workflow-context.private.json')","if options.closed_readback_only or options.return_existing_pending:(root/'workflow-context.private.json')")
h=h.replace("        if options.closed_readback_only:phases=", "        if options.return_existing_pending:phases=[('reviewer-first','own_reviewer_b','reviewer',False,False),('operator-readback','own_operator_a','operator',False,False)]\n        if options.closed_readback_only:phases=")
h=h.replace("'actualOriginalFourBrowserPhases':len(phases)","'actualExecutedNativeBrowserPhases':len(phases),'continuedSamePriorCreateFeedbackInstance':options.return_existing_pending")
ast.parse(h);host.write_text(h,encoding='utf-8')
runner=(V/'run_return_workflow_r163_20261102.py').read_text(encoding='utf-8')
runner=runner.replace("attempt=sys.argv[1]if len(sys.argv)==2 else'r1';assert attempt in['r1','r2','r3'];", "attempt='r2';assert len(sys.argv)==1;")
runner=runner.replace("'--event-dictionaries']","'--event-dictionaries','--return-existing-pending']")
ast.parse(runner);(V/'run_return_continuation_r164_20261102.py').write_text(runner,encoding='utf-8')
# Journal exact same owned flow-code change; r1 has restored all original bytes.
scope=J(C/'prepared-r1/temporary-synthetic-config-scope.json');before={name:(A/name).read_bytes()for name in scope['files']}
assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['beforeSHA256']for name,raw in before.items())
cfg=json.loads(before['private/server-configuration.json']);assert cfg['configuration']['business']['flow.code']=='OWN_FORM_CODE'and cfg['configuration']['business']['flow.event-task-handle']=='OWN_FORM_CODE'
cfg['configuration']['business']['flow.code']=cfg['configuration']['business']['flow.event-task-handle']='OWN_SERIAL_R163_r1'
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
changed={'private/server-configuration.json':enc(cfg)};payload=json.loads(before['payload-manifest.json']);payload['files']['private/server-configuration.json']={'bytes':len(changed['private/server-configuration.json']),'sha256':hashlib.sha256(changed['private/server-configuration.json']).hexdigest()};changed['payload-manifest.json']=enc(payload);release=json.loads(before['release-manifest.json']);release['payloadManifestSHA256']=hashlib.sha256(changed['payload-manifest.json']).hexdigest();changed['release-manifest.json']=enc(release)
assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['afterSHA256']for name,raw in changed.items())
P.mkdir()
for name,raw in before.items():p=P/'before'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in ['own-serial-definition.json','controller-fixture-ready.json']:(P/name).write_bytes((C/'prepared-r1'/name).read_bytes())
(P/'workflow-context.private.json').write_bytes((C/'r1/workflow-context.private.json').read_bytes());(P/'temporary-synthetic-config-scope.json').write_bytes((C/'prepared-r1/temporary-synthetic-config-scope.json').read_bytes())
for name,raw in changed.items():p=A/name;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(raw)
(P/'continued-prior-evidence.json').write_text(json.dumps({'sameR1CreateAndFeedbackInstance':True,'noReturnPreviouslySubmitted':True,'sourceContextSHA256':sha(P/'workflow-context.private.json'),'onlySameOwnFakeFlowCodeReapplied':True,'browserSHA256':sha(V/'verify_native_return_serial_browser_r163_20261102.mjs'),'hostSHA256':sha(host),'runnerSHA256':sha(V/'run_return_continuation_r164_20261102.py')},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'continueSameR1TaskAfterNormalRestart':True,'noDuplicateTaskCreateOrFeedbackReplay':True,'configuredReturnNodeRenderingWaitAdded':True,'exactSameOwnTemporaryConfigPinsReapplied':True,'servicesNotYetStarted':True}))
