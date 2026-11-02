from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent
def once(s,a,b):
    assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b)
def put(name,s):
    p=V/name;assert not p.exists();p.write_text(s,encoding='utf-8')
    if p.suffix=='.py':ast.parse(s)
host=(V/'verify_full_controller_early_addsign_r176_20261102.py').read_text(encoding='utf-8')
host=once(host,"options.attempt=='r76'","options.attempt=='r77'")
host=once(host,'verify_native_early_addsign_browser_r176_20261102.mjs','verify_native_pending_visibility_r177_20261102.mjs')
host=once(host,"('reviewer-early-probe','own_reviewer_b','reviewer',False,False),('operator-added'","('reviewer-early-probe','own_reviewer_b','reviewer',False,False),('operator-membership-unavailable','own_operator_a','reviewer',False,False),('operator-added'")
host=once(host,"'probeEarlyApproval':label=='reviewer-early-probe'","'probeEarlyApproval':label=='reviewer-early-probe','injectMembershipFailure':label=='operator-membership-unavailable'")
host=once(host,"['reviewer-addsign','reviewer-early-probe','operator-added','reviewer-after-added']","['reviewer-addsign','reviewer-early-probe','operator-membership-unavailable','operator-added','reviewer-after-added']")
host=host.replace('xnby.r176.original-early-addsign-order-check.v1','xnby.r177.pending-visibility-native-controller-check.v1')
host=once(host,"'productCodeChanged':False","'isolatedCandidateFrontendChanged':True,'installedProductCodeChanged':False")
put('verify_full_controller_pending_visibility_r177_20261102.py',host)

s=(V/'verify_native_early_addsign_browser_r176_20261102.mjs').read_text(encoding='utf-8')
s=once(s,"'reviewer-early-probe'].includes(wire.phaseName)","'reviewer-early-probe','operator-membership-unavailable'].includes(wire.phaseName)")
s=once(s,"const nativeTargetEvents=[];","let membershipFailureArmed=false,membershipFailureInjected=0;const nativeTargetEvents=[];")
needle="const u=new URL(v.params.request.url);if(u.origin===wire.base||"
replacement="const u=new URL(v.params.request.url);if(wire.injectMembershipFailure&&membershipFailureArmed&&membershipFailureInjected===0&&u.origin===wire.base&&u.pathname.endsWith('/Engine/FlowBefore/List/1')){membershipFailureInjected++;send('Fetch.fulfillRequest',{requestId:v.params.requestId,responseCode:503,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({code:503,msg:'OWN_PENDING_LOOKUP_UNAVAILABLE'})).toString('base64')},session).catch(()=>{});return;}if(u.origin===wire.base||"
s=once(s,needle,replacement)
s=once(s,"  await send('Page.navigate',{url:originalRoute.href},session);","  const lookupBefore=http.filter(x=>x.path.endsWith('/Engine/FlowBefore/List/1')).length;\n  await send('Page.navigate',{url:originalRoute.href},session);")
s=once(s,"  const active=await evaluate(","  await until(()=>http.filter(x=>x.path.endsWith('/Engine/FlowBefore/List/1')).length>lookupBefore);\n  await until(()=>evaluate('document.body.textContent.includes(\"当前任务暂不可审批，请在待办列表中查看最新状态\")&&!document.body.textContent.includes(\"正在核实待办状态\")'));\n  const active=await evaluate(")
s=once(s,"  let attempted=false,status=null,code=null;","  if(active)throw Error('STALE_OWN_REVIEW_DETAIL_MUST_NOT_RENDER_AUDIT_ACTION');\n  let attempted=false,status=null,code=null;")
s=once(s,"if(!wire.listsOnly){stage='actual-native-detail';await evaluate(","if(!wire.listsOnly){stage='actual-native-detail';membershipFailureArmed=!!wire.injectMembershipFailure;await evaluate(")
needle="  if(wire.addsignOnce){"
fault=r'''  if(wire.injectMembershipFailure){
   if(wire.account!=='own_operator_a'||wire.phaseName!=='operator-membership-unavailable')throw Error('ONLY_OWN_ACTIVE_ADDED_REVIEWER_LOOKUP_FAILURE');
   stage='active-added-reviewer-membership-lookup-unavailable';
   await until(()=>membershipFailureInjected===1);
   await until(()=>evaluate('document.body.textContent.includes("暂时无法核实待办状态，请刷新后重试")'));
   if(await evaluate('!!document.querySelector(".audit-content .audit-form")'))throw Error('UNCONFIRMED_PENDING_STATE_MUST_HIDE_AUDIT_ACTIONS');
   if(http.some(x=>x.path.includes('/FlowBefore/Audit/')))throw Error('NO_AUDIT_POST_WHEN_MEMBERSHIP_CHECK_UNAVAILABLE');
   const task=await ownTask();if(task.flowId!==context.flowId||task.uploadUrl!==context.uploadedPath||!feedbackMatches(task))throw Error('MEMBERSHIP_FAILURE_MUST_RETAIN_BUSINESS_ASSOCIATIONS');
   const result={passed:true,onlyOnePendingLookupFailureInjected:true,normalOwnActiveRole:true,approvalFormHidden:true,retryMessageVisible:true,auditRequests:0,taskEventFileAndFeedbackPreserved:true};
   await fs.writeFile(O+'/membership-lookup-failure-check.json',JSON.stringify(result,null,2));cases.push({case:'normal-active-reviewer-pending-lookup-failure-does-not-offer-approval',...result});
  }
'''
s=once(s,needle,fault+needle)
put('verify_native_pending_visibility_r177_20261102.mjs',s)

runner=(V/'run_early_addsign_r176_20261102.py').read_text(encoding='utf-8')
runner=once(runner,"attempt='r76'","attempt='r77'")
runner=once(runner,'verify_full_controller_early_addsign_r176_20261102.py','verify_full_controller_pending_visibility_r177_20261102.py')
needle="restored=subprocess.run([sys.executable,str(V/'restore_owned_return_serial_r163_20261102.py')"
replacement="frontend=subprocess.run([sys.executable,str(V/'restore_pending_visibility_runtime_r177.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)\nassert frontend.returncode==0 and json.loads(frontend.stdout)['passed'],'OWN_FRONTEND_RESTORE_NOT_PASSED'\n"+needle
runner=once(runner,needle,replacement)
put('run_pending_visibility_r177_20261102.py',runner)
r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_pending_visibility_r177_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode()
print(json.dumps({'preparedSources':3,'syntaxPassed':True,'candidateStages':9,'staleDetailAndActiveRoleFaultChecks':True,'noRuntimeOrPublicChanges':True}))
