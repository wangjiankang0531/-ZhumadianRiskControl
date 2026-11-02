from pathlib import Path
import ast,json,hashlib
V=Path(__file__).parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_pending_visibility_r34_20261102';W=R/'work/user_feedback_20261031';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((W/'r34-pending-visibility-candidate-r1/bundle/payload/payload-manifest.json').read_bytes());count=sum(n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))for n in q['files'])
s=(V/'verify_public_r33_https.py').read_text(encoding='utf-8')
for old,new in [('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102'),('r33-project-header-candidate-r1','r34-pending-visibility-candidate-r1'),('ac0c9b0fbd6f882399ba0c0ad82c96d9d78b1b79963b9def8ee25d3fa40044f5','d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af'),('330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13','5f214688ed3038ecdc75f7cf03fb209f94b28f2233c219c26a9fc46e1dd65b5f'),('project-header-home-r167/dist','workflow-pending-visibility-r178/dist'),('assert len(expected)==1174','assert len(expected)=='+str(count)),('r33verify','r34verify'),('R33-static-verifier','R34-static-verifier'),('xnby.r33.','xnby.r34.')]:assert old in s,old;s=s.replace(old,new)
ast.parse(s);(V/'verify_public_r34_https.py').write_text(s,encoding='utf-8')
s=(V/'verify_public_r33_home_ui.mjs').read_text(encoding='utf-8').replace('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102').replace('public-ui-r2','public-ui-r1').replace('r33','r34').replace('R33','R34')
s=s.replace('let ws,chrome,session,seq=0,stage=', 'let ws,chrome,session,seq=0,businessWritesBlocked=0,stage=')
old="const u=new URL(v.params.request.url),allow=u.origin===BASE||['data:','about:'].includes(u.protocol);"
new="const u=new URL(v.params.request.url),mutating=/\\/Engine\\/FlowBefore\\/(Audit|freeApprover|Transfer|Cancel|Delete|Create)\\//i.test(u.pathname)||/\\/eventTask\\/(save|updateById|remove|delete)/i.test(u.pathname),allow=(u.origin===BASE||['data:','about:'].includes(u.protocol))&&!mutating;if(mutating)businessWritesBlocked++;"
assert old in s;s=s.replace(old,new)
anchor=" check(await evaluate('!Array.from(document.querySelectorAll(\".el-message,.el-message-box\")).some(e=>e.getClientRects().length&&/登录验证暂不可用|登录状态已过期/.test(e.textContent))'),'no-visible-public-authentication-unavailable-error');"
assert s.count(anchor)==1
addition="""
 stage='public-readonly-pending-and-handled-ui';
 const clickLabel=async(selector,label)=>evaluate('(()=>{const e=Array.from(document.querySelectorAll('+JSON.stringify(selector)+')).find(e=>e.getClientRects().length&&e.textContent.trim()==='+JSON.stringify(label)+');if(!e)return false;e.click();return true})()');
 for(const item of [{label:'待办事宜',pending:true},{label:'已办事宜',pending:false}]){
  check(await clickLabel('.el-sub-menu__title','审批管理')||await evaluate('Array.from(document.querySelectorAll(".el-menu-item")).some(e=>e.getClientRects().length&&e.textContent.trim()==="待办事宜")'),'native-approval-menu-accessible-'+item.label);
  // Opening an already expanded submenu may collapse it. Reopen only if its leaf is hidden.
  if(!await clickLabel('.el-menu-item',item.label)){check(await clickLabel('.el-sub-menu__title','审批管理'),'native-approval-submenu-reopen');check(await clickLabel('.el-menu-item',item.label),'native-approval-leaf-open-'+item.label);}
  await until(()=>evaluate('!!document.querySelector(".el-loading-mask")===false'));await sleep(1500);
  const count=await evaluate('document.querySelectorAll(".work-item").length');check(Number.isInteger(count)&&count>=0,'native-public-list-rendered-'+item.label);
  checks.push({case:'public-authorized-list-observation-'+item.label,passed:true,visibleItems:count,rawNamesOrRowsRecorded:false});
  if(count){
   await mouse('.work-item');await until(()=>evaluate('document.body.textContent.includes("审批记录")&&document.body.textContent.includes("流程状态")&&document.body.textContent.includes("流程图")'));await sleep(1200);
   const state=await evaluate('({auditVisible:!!document.querySelector(".audit-content .audit-form"),pendingVerificationNotice:!!document.querySelector(".audit-content [role=status],.audit-content .el-alert"),readOnlyFields:!document.querySelector(".left-content input:not(:disabled),.left-content textarea:not(:disabled)")})()');
   check(state.readOnlyFields,'public-workflow-detail-business-form-readonly-'+item.label);
   if(!item.pending)check(!state.auditVisible,'public-handled-detail-does-not-offer-approval');
   checks.push({case:'public-native-approval-area-observation-'+item.label,passed:true,...state,approvalSubmitted:false});
  }else checks.push({case:'public-current-list-has-no-sample-'+item.label,passed:true,detailExercised:false});
 }
 check(businessWritesBlocked===0,'no-public-business-write-attempted');
"""
s=s.replace(anchor,anchor+addition)
s=s.replace('onlyEmergencyHomeAndHeaderViewed:true','onlyEmergencyHomeHeaderAndOwnPendingHandledReadOnlyViews:true').replace("'PUBLIC_UI_CHECK_FAILED'","'PUBLIC_UI_CHECK_FAILED_'+name")
(V/'verify_public_r34_pending_ui.mjs').write_text(s,encoding='utf-8')
runner=(V/'run_public_r33_home_ui.py').read_text(encoding='utf-8').replace('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102').replace('public-ui-r2','public-ui-r1').replace('verify_public_r33_home_ui.mjs','verify_public_r34_pending_ui.mjs').replace('R33','R34');ast.parse(runner);(V/'run_public_r34_pending_ui.py').write_text(runner,encoding='utf-8')
print(json.dumps({'prepared':True,'exactStaticFileCount':count,'publicUIOnlyNormalLoginAndReadOnlyPendingHandled':'no business submission','sourceControlsPreparedOnly':True}))
