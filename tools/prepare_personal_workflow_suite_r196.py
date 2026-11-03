from pathlib import Path
import ast
V=Path(__file__).parent
def once(s,old,new):
 assert s.count(old)==1,(old[:80],s.count(old));return s.replace(old,new)
host=(V/'verify_full_controller_addsign_history_r191_20261102.py').read_text(encoding='utf-8').replace('r191','r196').replace('r91','r96')
host=once(host,"for n,pin in history_scope['newFiles'].items():assert sha(app/n)==pin['sha256']","for n,pin in history_scope['newFiles'].items():\n    if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']\nfrontend_scope=read(prepared_base/'frontend-scope.json')\nfor n,pin in frontend_scope['newFiles'].items():assert sha(app/n)==pin['sha256']")
host=once(host,"process=None;job=None;row=None;failure=None;checks={};schema_process=None;schema_job=None","process=None;job=None;row=None;failure=None;checks={};schema_process=None;schema_job=None;menu_visibility_requested=False")
anchor="phase='created';http_observations=[]"
helper="""def own_menu_visibility(mode):
    secret=read(app/'private/server-configuration.json')['seedRootPassword']
    args=[reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnPersonalWorkflowMenuVisibility',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),mode,str(root)]
    completed=subprocess.run(args,input=secret.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);secret=None
    assert completed.returncode==0,'OWN_SYNTHETIC_MENU_VISIBILITY_'+mode.upper()+'_FAILED'
    result=json.loads(completed.stdout);assert result['passed']and not result['accountRoleOrGrantRowsChanged'];return result

"""
host=once(host,anchor,helper+anchor)
anchor="        for label,account,actor,audit,readback in phases:"
insert="""        menu_source=Path(__file__).parent/'OwnPersonalWorkflowMenuVisibility.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(menu_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_MENU_VISIBILITY_FIXTURE_COMPILE_FAILED'
        menu_visibility_requested=True;checks['onlyOwnWorkflowModulesHiddenBeforeNormalLogin']=own_menu_visibility('hide')['passed']
"""
host=once(host,anchor,insert+anchor)
host=once(host,"phases += [('reviewer-final','own_operator_a','reviewer',True,False),('operator-completed-readback','own_operator_a','operator',False,False)]","phases += [('reviewer-final','own_operator_a','reviewer',True,False),('reviewer-handled-readback','own_reviewer_b','reviewer',False,False),('operator-completed-readback','own_operator_a','operator',False,False)]")
host=once(host,"'expectedAfterAuditStatus':'1'}","'expectedAfterAuditStatus':'1','requireMissingWorkflowMenus':True,'handledReadback':label=='reviewer-handled-readback'}")
host=once(host,"label in ['reviewer-final','operator-completed-readback']","label in ['reviewer-final','reviewer-handled-readback','operator-completed-readback']")
anchor='    finally:\n        if schema_process:'
addition="""    finally:
        if menu_visibility_requested:
            try:checks['originalOwnedMenuModuleMarkersRestored']=own_menu_visibility('restore')['passed']
            except BaseException as menu_error:
                failure=failure or 'OwnMenuRestoreFailed';dump(root/'own-menu-restore-failed.json',{'failed':True,'type':type(menu_error).__name__,'noPublicOrAccountRowsOperated':True})
        if schema_process:"""
host=once(host,anchor,addition)
browser=(V/'verify_native_addsign_history_browser_r191_20261102.mjs').read_text(encoding='utf-8')
browser=once(browser,"'reviewer-after-added'].includes(wire.phaseName)","'reviewer-after-added','reviewer-handled-readback'].includes(wire.phaseName)")
browser=once(browser,"x.workflowMenusReturned)","(wire.requireMissingWorkflowMenus?!x.workflowMenusReturned:x.workflowMenusReturned))")
start=browser.index('async function menu(label,endpoint)');end=browser.index('\n',start)
old=browser[start:end]
new='''async function menu(label,endpoint){
 stage='menu-'+label;
 await until(()=>evaluate("!location.pathname.includes('/login')"));
 const before=http.filter(x=>x.path.endsWith(endpoint)).length;
 const route=label==='我发起的'?'/zhumadian/emergency/workflow/startWithMeTwo':label==='我已处理'?'/zhumadian/emergency/workflow/completedMatters':'/zhumadian/emergency/workflow/flowTodo';
 const alreadyOnRoute=await evaluate('location.pathname==='+JSON.stringify(route));
 if(wire.requireMissingWorkflowMenus){
  if(!await evaluate('(()=>{const e=document.querySelector("img[title=返回首页]");if(!e)return false;e.click();return true;})()'))throw Error('ORIGINAL_PROJECT_HOME_LINK_REQUIRED');
  await until(()=>evaluate('document.querySelectorAll("[data-workflow-route]").length===3'));
  if(!await click('[data-workflow-route]',label==='我已处理'?'已办事宜':label))throw Error('NORMAL_HOME_PERSONAL_WORKFLOW_ENTRY_REQUIRED');
 }else if(!await click('.el-menu-item',label))throw Error('OWN_WORKFLOW_MENU_MISSING');
 await until(()=>http.filter(x=>x.path.endsWith(endpoint)).length>before||alreadyOnRoute&&before>0);
 await until(()=>evaluate('location.pathname==='+JSON.stringify(route)));
 const result=http.filter(x=>x.path.endsWith(endpoint)).at(-1);
 if(result.httpStatus!==200||result.businessCode!==200||!result.listIsArray||!result.paginationPresent)throw Error('NATIVE_WORKFLOW_LIST_CONTRACT');
 await until(()=>evaluate(`document.querySelectorAll('.work-item').length===${result.listCount}`));
 if(!await evaluate("!!document.querySelector('.work-list')"))throw Error('WORKFLOW_VIEW_NOT_RENDERED');
 cases.push({case:label+'-native-home-entry-and-list-without-server-workflow-menu',rows:result.listCount,passed:true});return lists.get(result.path).list;
}'''
assert new!=old;browser=browser[:start]+new+browser[end:]
old="const endpoint=wire.actor==='operator'?'/Engine/FlowLaunch':'/FlowBefore/List/1',label=wire.actor==='operator'?'我发起的':'待办事宜';"
new="const endpoint=wire.handledReadback?'/FlowBefore/List/2':wire.actor==='operator'?'/Engine/FlowLaunch':'/FlowBefore/List/1',label=wire.handledReadback?'我已处理':wire.actor==='operator'?'我发起的':'待办事宜';"
browser=once(browser,old,new)
browser=once(browser,"row.path.endsWith('/FlowBefore/List/1')","(row.path.endsWith('/FlowBefore/List/1')||row.path.endsWith('/FlowBefore/List/2'))")
anchor=" if(wire.phaseName==='operator-completed-readback'){"
browser=once(browser,anchor," if(wire.handledReadback){if(await evaluate('!!document.querySelector(\".audit-content .audit-form\")'))throw Error('HANDLED_DETAIL_MUST_NEVER_OFFER_APPROVAL');cases.push({case:'original-handled-list-and-detail-accessible-without-workflow-menu-and-remains-readonly',passed:true});}\n"+anchor)
for name,s in [('verify_full_controller_personal_workflow_r196_20261103.py',host),('verify_native_personal_workflow_r196_20261103.mjs',browser)]:
 if name.endswith('.py'):ast.parse(s)
 (V/name).write_text(s,encoding='utf-8')
hostfile=V/'verify_full_controller_personal_workflow_r196_20261103.py';s=hostfile.read_text(encoding='utf-8').replace('verify_native_addsign_history_browser_r196_20261102.mjs','verify_native_personal_workflow_r196_20261103.mjs');hostfile.write_text(s,encoding='utf-8')
runtime=(V/'prepare_native_history_runtime_r191.py').read_text(encoding='utf-8').replace('r191','r196').replace('r91','r96').replace('runtime-module-r196','runtime-module-r191');ast.parse(runtime);(V/'prepare_native_history_runtime_r196.py').write_text(runtime,encoding='utf-8')
front=(Path('D:/Project/Zhumadian/Application/tools/prepare_pending_visibility_runtime_r178.py')).read_text(encoding='utf-8').replace('workflow-pending-visibility-r178','personal-workflow-routes-r195').replace('r78','r96').replace('len(new)==338','len(new)==340');ast.parse(front);(V/'prepare_personal_workflow_frontend_r196.py').write_text(front,encoding='utf-8')
restore=(Path('D:/Project/Zhumadian/Application/tools/restore_pending_visibility_runtime_r178.py')).read_text(encoding='utf-8').replace('r78','r96').replace('r178','r196');ast.parse(restore);(V/'restore_personal_workflow_frontend_r196.py').write_text(restore,encoding='utf-8')
restore=(V/'restore_native_history_runtime_r191.py').read_text(encoding='utf-8').replace('r191','r196').replace('r91','r96');ast.parse(restore);(V/'restore_native_history_runtime_r196.py').write_text(restore,encoding='utf-8')
runner=(V/'run_native_history_r191_20261102.py').read_text(encoding='utf-8').replace('r191','r196').replace('r91','r96').replace('verify_full_controller_addsign_history_r196_20261102.py','verify_full_controller_personal_workflow_r196_20261103.py')
anchor="restored=subprocess.run([sys.executable,str(V/'restore_native_history_runtime_r196.py')]"
assert runner.count(anchor)==1;runner=runner.replace(anchor,"frontend=subprocess.run([sys.executable,str(V/'restore_personal_workflow_frontend_r196.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)\nassert frontend.returncode==0 and json.loads(frontend.stdout)['passed'],'OWN_FRONTEND_RESTORE_FAILED'\n"+anchor)
ast.parse(runner);(V/'run_personal_workflow_r196_20261103.py').write_text(runner,encoding='utf-8')
print('COMBINED_ORIGINAL_MENUS_ABSENT_NATIVE_WORKFLOW_AND_HISTORY_TIME_SUITE_PREPARED')
