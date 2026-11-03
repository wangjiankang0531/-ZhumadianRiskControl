from pathlib import Path
import ast
V=Path(__file__).parent
def save(n,s):
 p=V/n;assert not p.exists(),n
 if n.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
mapping=[('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103'),('r34-pending-visibility-candidate-r1','r35-personal-workflow-candidate-r1'),('d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af','ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3'),('5f214688ed3038ecdc75f7cf03fb209f94b28f2233c219c26a9fc46e1dd65b5f','ccede060e9c329d44e65aef3200d86f8666c73d071d743cc1535031ab15d0ca4'),('workflow-pending-visibility-r178/dist','personal-workflow-routes-r195/dist'),('len(expected)==1174','len(expected)==1176'),('r34verify','r35verify'),('R34-static-verifier','R35-static-verifier'),('xnby.r34.','xnby.r35.')]
s=(V/'verify_public_r34_https.py').read_text(encoding='utf-8')
for a,b in mapping:assert a in s,a;s=s.replace(a,b)
save('verify_public_r35_https.py',s)
s=(V/'verify_public_readonly_r194.mjs').read_text(encoding='utf-8').replace('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103').replace('public-ui-r194','public-ui-r202').replace('r34','r35').replace('R34','R35')
start=s.index(" stage='public-readonly-pending-and-handled-ui';");end=s.index(" check(businessWritesBlocked===0",start)
replacement=''' stage='public-readonly-personal-workflow-three-entries-and-detail';
 for(const item of [{label:'待办事宜',kind:'pending',route:'/workflow/flowTodo'},{label:'已办事宜',kind:'handled',route:'/workflow/completedMatters'},{label:'我发起的',kind:'initiated',route:'/workflow/startWithMeTwo'}]){
  const responseStart=workflowResponses.length;
  check(await evaluate('(()=>{const e=document.querySelector(\\'img[title="返回首页"]\\');if(!e)return false;e.click();return true})()'),'original-project-mark-returns-home-'+item.kind);
  await until(()=>evaluate('document.querySelectorAll("[data-workflow-route]").length===3'));
  check(await evaluate('(()=>{const e=Array.from(document.querySelectorAll("[data-workflow-route]")).find(e=>e.textContent.trim()==='+JSON.stringify(item.label)+');if(!e)return false;e.click();return true})()'),'normal-personal-home-entry-click-'+item.kind);
  await until(()=>evaluate('!!document.querySelector(".work-list")'));
  await until(()=>evaluate('!Array.from(document.querySelectorAll(".el-loading-mask")).some(e=>e.getClientRects().length&&getComputedStyle(e).display!=="none")'));
  await until(()=>workflowResponses.slice(responseStart).some(r=>r.listType===item.kind&&r.status===200&&r.json));
  check(await evaluate('location.pathname==='+JSON.stringify('/zhumadian/emergency'+item.route)),'native-public-route-registered-'+item.kind);
  const count=await evaluate('document.querySelectorAll(".work-item").length');check(Number.isInteger(count)&&count>=0,'native-public-list-rendered-'+item.kind);
  checks.push({case:'public-authorized-list-observation-'+item.kind,passed:true,visibleItems:count,rawNamesOrRowsRecorded:false});
  const refreshStart=workflowResponses.length;await send('Page.reload',{ignoreCache:true},session);
  await until(()=>workflowResponses.slice(refreshStart).some(r=>r.listType===item.kind&&r.status===200&&r.json));
  await until(()=>evaluate('location.pathname==='+JSON.stringify('/zhumadian/emergency'+item.route)+'&&!!document.querySelector(".work-list")'));
  check(true,'normal-personal-list-refresh-keeps-route-'+item.kind);
  await until(()=>evaluate('!Array.from(document.querySelectorAll(".el-loading-mask")).some(e=>e.getClientRects().length&&getComputedStyle(e).display!=="none")'));await sleep(800);
  if(count){
   await mouse('.work-item');await until(()=>evaluate('(document.body?.textContent||"").includes("审批记录")&&(document.body?.textContent||"").includes("流程状态")&&(document.body?.textContent||"").includes("流程图")'));await sleep(1500);
   const state=await evaluate('({auditVisible:!!document.querySelector(".audit-content .audit-form"),pendingVerificationNotice:!!document.querySelector(".audit-content [role=status],.audit-content .el-alert"),readOnlyFields:!document.querySelector(".left-content input:not(:disabled),.left-content textarea:not(:disabled)"),businessFormPresent:!!document.querySelector(".left-content .form-content"),not404:!(document.body?.textContent||"").includes("404")})');
   check(state.readOnlyFields&&state.businessFormPresent&&state.not404,'public-workflow-detail-business-form-present-and-readonly-'+item.kind);
   if(item.kind!=='pending')check(!state.auditVisible,'public-closed-or-initiated-detail-does-not-offer-approval-'+item.kind);
   checks.push({case:'public-native-detail-and-approval-area-'+item.kind,passed:true,...state,detailExercised:true,approvalSubmitted:false});
   await send('Page.reload',{ignoreCache:true},session);await until(()=>evaluate('(document.body?.textContent||"").includes("审批记录")&&!!document.querySelector(".left-content .form-content")'));
   check(true,'normal-personal-detail-refresh-keeps-route-'+item.kind);
  }else checks.push({case:'public-current-list-has-no-detail-sample-'+item.kind,passed:true,detailExercised:false});
  check(await evaluate('!Array.from(document.querySelectorAll(".el-message,.el-message-box")).some(e=>e.getClientRects().length&&/登录验证暂不可用|登录状态已过期/.test(e.textContent))'),'no-authentication-unavailable-during-personal-flow-'+item.kind);
 }
'''
s=s[:start]+replacement+s[end:]
s=s.replace('onlyEmergencyHomeHeaderAndOwnPendingInitiatedReadOnlyViews:true,publicHandledRouteNotPresentInEmergencySource:true','onlyEmergencyHomeHeaderAndOwnPersonalWorkflowReadOnlyViews:true,publicHandledRoutePresent:true')
save('verify_public_personal_workflow_r202.mjs',s)
s=(V/'run_public_readonly_r194.py').read_text(encoding='utf-8').replace('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103').replace('public-ui-r194','public-ui-r202').replace('verify_public_readonly_r194.mjs','verify_public_personal_workflow_r202.mjs').replace('R34','R35');save('run_public_personal_workflow_r202.py',s)
print('R35_EXACT_1176_HTTPS_AND_THREE_PERSONAL_PAGES_READONLY_NORMAL_LOGIN_PROBE_PREPARED')
