from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent;A=Path('D:/Project/Zhumadian/Application')
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
def put(name,s):
    p=V/name;assert not p.exists();p.write_text(s,encoding='utf-8')
    if p.suffix=='.py':ast.parse(s)
host=(A/'tools/verify_full_controller_addsign_r172_20261102.py').read_text(encoding='utf-8')
host=once(host,'verify_native_addsign_browser_r172_20261102.mjs','verify_native_early_addsign_browser_r176_20261102.mjs')
host=once(host,"options.attempt in ['r72','r73','r74','r75']","options.attempt=='r76'")
host=once(host,"add_type='1' if options.attempt in ['r72','r74'] else '2'","add_type='1'")
host=once(host,"('reviewer-addsign','own_reviewer_b','reviewer',False,False),('operator-added'","('reviewer-addsign','own_reviewer_b','reviewer',False,False),('reviewer-early-probe','own_reviewer_b','reviewer',False,False),('operator-added'")
host=once(host,"'addsignType':add_type,'readbackOnly'","'addsignType':add_type,'probeEarlyApproval':label=='reviewer-early-probe','readbackOnly'")
host=once(host,"observe=label in ['reviewer-addsign','operator-added','reviewer-after-added']","observe=label in ['reviewer-addsign','reviewer-early-probe','operator-added','reviewer-after-added']")
host=host.replace('xnby.r172.original-addsign-association-check.v1','xnby.r176.original-early-addsign-order-check.v1')
host=once(host,"'actualAddsignAndRemainingReviewsCompleted':not options.completed_addsign_readback","'earlyOriginalReviewerNegativeUIProbeExecuted':True,'fullAddsignFeatureAccepted':False,'actualAddsignAndRemainingReviewsCompleted':not options.completed_addsign_readback")
put('verify_full_controller_early_addsign_r176_20261102.py',host)

browser=(A/'tools/verify_native_addsign_browser_r172_20261102.mjs').read_text(encoding='utf-8')
browser=once(browser,"'reviewer-after-added'].includes(wire.phaseName)","'reviewer-after-added','reviewer-early-probe'].includes(wire.phaseName)")
needle=" expectedContext=context;";assert browser.count(needle)==1
probe=r'''
 if(wire.probeEarlyApproval){
  if(wire.account!=='own_reviewer_b'||wire.phaseName!=='reviewer-early-probe'||!context.originalReviewerRoute)throw Error('EXACT_OWN_ORIGINAL_REVIEWER_PROBE_SCOPE');
  stage='normal-original-reviewer-pending-list-before-added-review';
  const agent=await evaluate('navigator.userAgent');
  const readNative=async path=>{const r=await fetch(wire.base+'/zhumadian/api/jnpf'+path,{headers:{Authorization:token,'User-Agent':agent}}),v=await r.json();if(r.status!==200||v.code!==200)throw Error('OWN_ORIGINAL_PROBE_READ_FAILED');return v.data;};
  let page=1,seen=0,found=false,total=0;
  for(;;){const d=await readNative('/workflow/Engine/FlowBefore/List/1?currentPage='+page+'&pageSize=100');total=Number(d.pagination?.total);if(!Array.isArray(d.list)||!Number.isFinite(total)||total<0||total>500)throw Error('OWN_BOUNDED_PENDING_LIST_REQUIRED');found ||= d.list.some(x=>x.processInstanceId===context.flowId||x.id===context.flowId);seen+=d.list.length;if(seen>=total)break;if(!d.list.length||page>=5)throw Error('OWN_COMPLETE_PENDING_SCAN_REQUIRED');page++;}
  const originalRoute=new URL(context.originalReviewerRoute,wire.base);if(originalRoute.origin!==wire.base||!originalRoute.pathname.startsWith('/zhumadian/emergency/workflow/flowTodo/'))throw Error('ONLY_SAVED_OWN_REVIEW_ROUTE_ALLOWED');
  const originalOperator=originalRoute.searchParams.get('id'),originalTemplate=originalRoute.searchParams.get('flowId');if(!originalOperator||!originalTemplate)throw Error('OWN_SAVED_NATIVE_OPERATOR_AND_TEMPLATE_REQUIRED');
  const detailPath='/workflow/Engine/FlowBefore/'+encodeURIComponent(originalOperator)+'?taskNodeId='+encodeURIComponent(originalOperator)+'&taskOperatorId='+encodeURIComponent(originalOperator)+'&flowId='+encodeURIComponent(originalTemplate);
  const before=await ownTask(),selected=t=>JSON.stringify(['id','flowId','infoId','uploadUrl','taskStatus','feedbackInfo','evaluationSum','disposeTime'].map(k=>[k,t[k]]));
  const providerBefore=await readNative(detailPath);if(providerBefore.flowTaskInfo?.id!==context.flowId)throw Error('SAME_OWN_INSTANCE_MUST_BE_READ');
  const recordSignature=d=>JSON.stringify((d.flowTaskOperatorRecordList||[]).map(x=>[x.taskOperatorId,x.taskNodeId,x.handleId,x.handleStatus,x.handleTime,x.handleOpinion]));
  const signatureBefore=recordSignature(providerBefore);
  const detailBefore=http.filter(x=>x.path.endsWith('/FlowBefore/'+originalOperator)).length;
  await send('Page.navigate',{url:originalRoute.href},session);
  await until(()=>http.filter(x=>x.path.endsWith('/FlowBefore/'+originalOperator)&&x.businessCode===200).length>detailBefore);
  await until(()=>evaluate('document.body.textContent.includes("审批记录")&&document.body.textContent.includes("流程状态")'));
  const active=await evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio")).some(e=>e.getClientRects().length&&e.textContent.trim()==="通过")');
  let attempted=false,status=null,code=null;
  if(active){
   stage='one-negative-original-ui-early-approval';
   if(!await click('.audit-form .el-radio','通过'))throw Error('ORIGINAL_AUDIT_RADIO_REQUIRED');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".audit-form .el-radio.is-checked")).some(e=>e.textContent.trim()==="通过")'));
   if(!await evaluate('(()=>{const e=document.querySelector(".audit-form textarea");if(!e)return false;e.value="OWN_R176_EARLY_ORIGINAL_PROBE";e.dispatchEvent(new Event("input",{bubbles:true}));return true})()'))throw Error('OWN_EARLY_PROBE_OPINION_REQUIRED');
   const count=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length;
   if(!await click('.audit-form button','提交'))throw Error('OWN_ORIGINAL_EARLY_PROBE_SUBMIT_REQUIRED');
   await until(()=>http.filter(x=>x.path.includes('/FlowBefore/Audit/')).length>count);
   const sent=http.filter(x=>x.path.includes('/FlowBefore/Audit/')).slice(count);if(sent.length!==1||sent[0].method!=='POST')throw Error('ONLY_ONE_EARLY_PROBE_REQUEST_ALLOWED');
   attempted=true;status=sent[0].httpStatus;code=sent[0].businessCode;
   if(status===200&&code===200){await fs.writeFile(O+'/early-approval-observation.json',JSON.stringify({earlyApprovalIncorrectlyAccepted:true,pendingListContainedInstance:found,originalPageExposedApproval:true,backendApprovalRejected:false},null,2));throw Error('ORIGINAL_REVIEWER_APPROVED_BEFORE_ADDED_REVIEWER');}
   if(status!==200||code!==400)throw Error('ORIGINAL_PROVIDER_EXPLICIT_BUSINESS_REJECTION_REQUIRED');
  }
  const after=await ownTask(),providerAfter=await readNative(detailPath);
  if(selected(before)!==selected(after)||recordSignature(providerAfter)!==signatureBefore)throw Error('NEGATIVE_EARLY_PROBE_MUST_NOT_MUTATE_TASK_OR_AUDIT_RECORDS');
  const observation={earlyApprovalIncorrectlyAccepted:false,pendingListContainedInstance:found,allPendingPagesScanned:true,originalSavedDetailApprovalVisible:active,oneEarlyApprovalProbeSubmitted:attempted,HTTPStatus:status,businessCode:code,backendApprovalRejected:attempted&&code===400,UIBlocksEarlyApproval:!active,businessTaskAndAuditRecordSignatureUnchanged:true,addedReviewerNotYetProcessed:true};
  await fs.writeFile(O+'/early-approval-observation.json',JSON.stringify(observation,null,2));cases.push({case:'original-before-addsign-original-reviewer-early-order-protection',passed:true,...observation});
  wire.expectEmptyFlowRejection=true;
 }
'''
browser=browser.replace(needle,needle+probe)
needle="   stage='original-ui-transfer-required-target';";assert browser.count(needle)==1
browser=browser.replace(needle,"   context.originalReviewerRoute=await evaluate('location.pathname+location.search');await fs.writeFile(root+'/workflow-context.private.json',JSON.stringify(context));\n"+needle)
put('verify_native_early_addsign_browser_r176_20261102.mjs',browser)
runner=(A/'tools/run_addsign_r172_20261102.py').read_text(encoding='utf-8')
runner=once(runner,"attempt=sys.argv[1]if len(sys.argv)==2 else'';assert attempt in ['r72','r73','r74','r75'];","attempt='r76';assert len(sys.argv)==1;")
runner=once(runner,'verify_full_controller_addsign_r172_20261102.py','verify_full_controller_early_addsign_r176_20261102.py')
put('run_early_addsign_r176_20261102.py',runner)
r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_early_addsign_browser_r176_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode()
print(json.dumps({'sourcePrepared':3,'syntaxPassed':True,'onlyOwnedSyntheticAttempt':'r76','oneNegativeUIProbeMaximum':True,'productOrConfigurationChanged':False}))
