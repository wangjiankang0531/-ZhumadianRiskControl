from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r3'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert not P.exists()and not(C/'r3').exists()
assert J(C/'r2/controller-terminal.json')['exitCode']==0 and J(C/'r2-outer-terminal.json')['actualDescendantsZeroBeforeClose']and J(C/'r2/result.json')['allPassed']
assert J(C/'prepared-r2/configuration-restored.json')['exactOriginalBytesRestored']
assert J(C/'r2/state-operator-readback.json')['pendingEngineTasks']==1 and not J(C/'r2/state-operator-readback.json')['originalEngineHistoryHasEndTime']
ctx=J(C/'r2/workflow-context.private.json');assert ctx['syntheticDataOnly']and ctx['taskName']=='Own serial workflow R163 r1'
p=V/'verify_native_return_serial_browser_r163_20261102.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("'reviewer-final','operator-readback']","'reviewer-final','operator-readback','operator-resubmit','reviewer-again','operator-completed-readback']",1)
anchor="   if(wire.actor!=='reviewer')throw Error('ONLY_OWN_ASSIGNED_REVIEWER_UI_APPROVES');"
assert s.count(anchor)==1
extra=r'''
   if(wire.phaseName==='operator-resubmit'){
    const definition=JSON.parse(await fs.readFile(root+'/own-serial-definition.json','utf8'));const startTitle=JSON.parse(JSON.parse(definition.templateBody.flowTemplateJson)[0].flowTemplateJson).properties.title;
    const pending=nativeRecords.filter(x=>!x.handleTime&&x.nodeName===startTitle&&String(x.userName).includes('own_operator_a'));
    await fs.writeFile(O+'/native-resubmit-before.json',JSON.stringify({actualPendingRecords:nativeRecords.filter(x=>!x.handleTime).map(x=>({nodeName:x.nodeName,userName:x.userName,handleStatus:x.handleStatus})),configuredStartTitle:startTitle,sameReturnedTaskAndNativeInstance:true},null,2));
    if(pending.length!==1)throw Error('RETURNED_APPLICANT_ORIGINAL_PENDING_START_NODE_REQUIRED');
    cases.push({case:'original-returned-start-node-assigned-to-normal-applicant',passed:true});
   }
'''
s=s.replace(anchor,extra+anchor)
s=s.replace('e.value="Own UI approval R122";','e.value='+"'+JSON.stringify(wire.phaseName==='operator-resubmit'?'OWN_R165_APPLICANT_RESUBMIT':'OWN_R165_'+wire.phaseName)+'"+';')
anchor=" if(exceptions.length)throw Error('ORIGINAL_WORKFLOW_UI_EXCEPTION');"
assert s.count(anchor)==1
completed=r'''
 if(wire.phaseName==='operator-completed-readback'){
  const task=await ownTask();if(task.flowId!==context.flowId||task.infoId!==context.eventId||task.uploadUrl!==context.uploadedPath||task.taskStatus!=='1'||!feedbackMatches(task))throw Error('COMPLETED_RETURN_RESUBMIT_ASSOCIATIONS_REQUIRED');
  if(await evaluate('!!document.querySelector(".audit-content .audit-form")'))throw Error('COMPLETED_INITIATOR_VIEW_MUST_NOT_OFFER_ACTIVE_AUDIT');
  if(!nativeRecords.some(x=>x.handleOpinion==='OWN_R163_RETURN_FOR_REVISION'&&x.handleTime)||!nativeRecords.some(x=>x.handleOpinion==='OWN_R165_APPLICANT_RESUBMIT'&&x.handleTime))throw Error('ORIGINAL_RETURN_AND_RESUBMIT_RECORDS_REQUIRED');
  cases.push({case:'completed-return-resubmit-two-review-chain-native-records-and-file-feedback-retained',passed:true});
 }
'''
s=s.replace(anchor,completed+anchor);p.write_text(s,encoding='utf-8')
host=V/'verify_full_controller_return_serial_r163_20261102.py';h=host.read_text(encoding='utf-8')
h=h.replace("parser.add_argument('--return-existing-pending',action='store_true');options=parser.parse_args()","parser.add_argument('--return-existing-pending',action='store_true');parser.add_argument('--resubmit-returned',action='store_true');options=parser.parse_args()")
h=h.replace('if options.closed_readback_only or options.return_existing_pending:', 'if options.closed_readback_only or options.return_existing_pending or options.resubmit_returned:')
anchor="        if options.closed_readback_only:phases="
assert h.count(anchor)==1
h=h.replace(anchor,"        if options.resubmit_returned:phases=[('operator-resubmit','own_operator_a','reviewer',True,False),('reviewer-again','own_reviewer_b','reviewer',True,False),('reviewer-final','own_operator_a','reviewer',True,False),('operator-completed-readback','own_operator_a','operator',False,False)]\n"+anchor)
old="observe=label in ['reviewer-first','operator-readback'];ended=None if observe else False;business_status='observe'if observe else('2'if label=='operator'else'1');pending_expected='observe'if observe else'1';ended_expected='observe'if observe else'false'"
assert old in h
h=h.replace(old,"observe=label in ['reviewer-first','operator-readback'];ended=None if observe else label in ['reviewer-final','operator-completed-readback'];business_status='observe'if observe else('2'if label=='operator'else'1');pending_expected='observe'if observe else('0'if ended else'1');ended_expected='observe'if observe else('true'if ended else'false')")
h=h.replace("'resubmissionNotExecuted':True", "'resubmissionNotExecuted':not options.resubmit_returned,'actualReturnResubmitAndTwoFinalReviewsCompleted':options.resubmit_returned")
ast.parse(h);host.write_text(h,encoding='utf-8')
runner=(V/'run_return_continuation_r164_20261102.py').read_text(encoding='utf-8').replace("attempt='r2'","attempt='r3'").replace("'--return-existing-pending'","'--resubmit-returned'")
ast.parse(runner);(V/'run_return_resubmit_r165_20261102.py').write_text(runner,encoding='utf-8')
scope=J(C/'prepared-r2/temporary-synthetic-config-scope.json');before={name:(A/name).read_bytes()for name in scope['files']};assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['beforeSHA256']for name,raw in before.items())
cfg=json.loads(before['private/server-configuration.json']);assert cfg['configuration']['business']['flow.code']==cfg['configuration']['business']['flow.event-task-handle']=='OWN_FORM_CODE';cfg['configuration']['business']['flow.code']=cfg['configuration']['business']['flow.event-task-handle']='OWN_SERIAL_R163_r1'
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();changed={'private/server-configuration.json':enc(cfg)};payload=json.loads(before['payload-manifest.json']);payload['files']['private/server-configuration.json']={'bytes':len(changed['private/server-configuration.json']),'sha256':hashlib.sha256(changed['private/server-configuration.json']).hexdigest()};changed['payload-manifest.json']=enc(payload);release=json.loads(before['release-manifest.json']);release['payloadManifestSHA256']=hashlib.sha256(changed['payload-manifest.json']).hexdigest();changed['release-manifest.json']=enc(release)
assert all(hashlib.sha256(raw).hexdigest()==scope['files'][name]['afterSHA256']for name,raw in changed.items())
P.mkdir()
for name,raw in before.items():p=P/'before'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in ['own-serial-definition.json','controller-fixture-ready.json','temporary-synthetic-config-scope.json']:(P/name).write_bytes((C/'prepared-r2'/name).read_bytes())
(P/'workflow-context.private.json').write_bytes((C/'r2/workflow-context.private.json').read_bytes())
for name,raw in changed.items():p=A/name;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(raw)
(P/'continued-prior-evidence.json').write_text(json.dumps({'sameOriginalR1TaskAndReturnedNativeInstance':True,'originalReturnAndInitiatorReadbackPreviouslyPassed':True,'originalEnginePendingTaskCount':1,'originalEngineHistoryNotEnded':True,'sourceContextSHA256':sha(P/'workflow-context.private.json'),'browserSHA256':sha(V/'verify_native_return_serial_browser_r163_20261102.mjs'),'hostSHA256':sha(host),'runnerSHA256':sha(V/'run_return_resubmit_r165_20261102.py'),'onlyExactSameOwnFakeFlowConfigReapplied':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sameReturnedTaskContinuationPrepared':True,'nativeApplicantTodoThenTwoReviewsThenCompletedReadback':True,'noDuplicateTaskOrTemplateCreate':True,'actualResubmitNotYetExecuted':True}))
