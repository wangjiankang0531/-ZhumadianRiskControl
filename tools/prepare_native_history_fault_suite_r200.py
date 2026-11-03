from pathlib import Path
import ast
V=Path(__file__).parent
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def save(name,s):
 p=V/name;assert not p.exists(),name
 if name.endswith('.py'):ast.parse(s)
 p.write_text(s,encoding='utf-8')
for old,new in [('prepare_personal_workflow_frontend_r199.py','prepare_personal_workflow_frontend_r200.py'),('restore_personal_workflow_frontend_r199.py','restore_personal_workflow_frontend_r200.py'),('restore_production_history_runtime_r199.py','restore_production_history_runtime_r200.py')]:save(new,(V/old).read_text(encoding='utf-8').replace('r199','r200').replace('r99','r100'))
s=(V/'prepare_production_history_runtime_r199.py').read_text(encoding='utf-8').replace('prepared-r99','prepared-r100').replace("C/'r99'","C/'r100'");save('prepare_production_history_runtime_r200.py',s)
java=(V/'OwnPersonalWorkflowMenuVisibilityR199.java').read_text(encoding='utf-8').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR200').replace('r99','r100');save('OwnPersonalWorkflowMenuVisibilityR200.java',java)
host=(V/'verify_full_controller_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r200').replace('r99','r100').replace('OwnPersonalWorkflowMenuVisibilityR199','OwnPersonalWorkflowMenuVisibilityR200').replace("add_type='2'","add_type='1'")
host=host.replace('native-after-addsign-history-regression','native-before-addsign-real-sql-fault-retry').replace('independentAfterAddsignOpinionRetained','independentBeforeAddsignOpinionRetained')
host=once(host,'menu_visibility_requested=False','menu_visibility_requested=False;history_fault_requested=False')
anchor="phase='created';http_observations=[]"
helper='''def own_history_fault(mode):
    context=read(root/'workflow-context.private.json');assert context['syntheticDataOnly']
    secret=read(app/'private/server-configuration.json')['seedRootPassword']
    args=[reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnNativeHistoryFaultR200',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),str(root),mode,context['flowId'],context['taskId'],context['taskName']]
    completed=subprocess.run(args,input=secret.encode(),capture_output=True,timeout=45,env=env,creationflags=subprocess.CREATE_NO_WINDOW);secret=None
    assert completed.returncode==0,'OWN_HISTORY_SQL_FAULT_'+mode.upper()+'_FAILED'
    result=json.loads(completed.stdout);assert result['passed']and result['onlyOwnSyntheticProcess']and not result['accountsOrSessionsRead'];return result

'''
host=once(host,anchor,helper+anchor)
anchor='        for label,account,actor,audit,readback in phases:'
host=once(host,anchor,"""        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(Path(__file__).parent/'OwnNativeHistoryFaultR200.java')],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_HISTORY_FAULT_HELPER_COMPILE_FAILED'
"""+anchor)
anchor="            with(root/('workflow-browser-'+label+'.private.log')).open('wb')as browserlog:"
host=once(host,anchor,"""            wire['expectNativeHistorySQLFault']=label=='reviewer-addsign'
            if label=='reviewer-addsign':
                history_fault_requested=True;checks['ownHistorySQLTriggerArmedBeforeAssignedReviewerPost']=own_history_fault('arm')['passed']
"""+anchor)
old="browser.communicate(json.dumps(wire).encode());wire.clear()"
new="""browser.stdin.write(json.dumps(wire).encode());browser.stdin.close();wire.clear()
                deadline=time.monotonic()+180;fault_observed=False
                while browser.poll()is None:
                    if label=='reviewer-addsign'and not fault_observed and(root/'native-history-browser-fault-observed.json').exists():
                        observed=read(root/'native-history-browser-fault-observed.json');assert observed['oneFailedPost']and observed['opinionAndSelectedUserRetained']
                        checks['nativeSQLFaultAllEightScopedTableFingerprintsIdentical']=own_history_fault('verify-drop')['allScopedDataFingerprintsUnchanged'];fault_observed=True
                        dump(root/'native-history-fault-removed-retry-ready.json',{'passed':True,'onlyExactOwnTriggerRemoved':True,'nativeTransactionAndEngineRowsUnchanged':True})
                    assert time.monotonic()<deadline,'OWN_NATIVE_BROWSER_FAULT_HANDSHAKE_TIMEOUT'
                    time.sleep(.1)
                if label=='reviewer-addsign':assert fault_observed,'OWN_NATIVE_SQL_FAULT_NOT_OBSERVED'
                browser.wait()"""
host=once(host,old,new)
anchor='    finally:\n        if menu_visibility_requested:'
host=once(host,anchor,"""    finally:
        if history_fault_requested:
            try:checks['ownHistoryFaultTriggerRemoved']=own_history_fault('cleanup')['triggerRemoved']
            except BaseException as trigger_error:
                failure=failure or 'OwnHistoryFaultCleanupFailed';dump(root/'own-history-trigger-cleanup-failed.json',{'failed':True,'type':type(trigger_error).__name__})
        if menu_visibility_requested:""")
save('verify_full_controller_personal_workflow_r200_20261103.py',host)
browser=(V/'verify_native_personal_workflow_r199_20261103.mjs').read_text(encoding='utf-8')
anchor="   stage='original-transfer-one-real-post';"
insert="""   if(wire.expectNativeHistorySQLFault){
    stage='one-real-native-history-sql-failure-preserves-input';
    if(!await click('.audit-form button','提交'))throw Error('OWN_FAULT_POST_SUBMIT_REQUIRED');
    await until(()=>http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).length>before);
    const failed=http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).slice(before);
    if(failed.length!==1||failed[0].method!=='POST'||failed[0].httpStatus===200&&failed[0].businessCode===200)throw Error('REAL_SQL_FAULT_MUST_FAIL_EXACTLY_ONE_ORIGINAL_POST');
    await until(()=>evaluate('document.querySelector(".audit-form textarea")?.value==="OWN_R172_ADDSIGN_OPERATOR"&&document.querySelector(".audit-form input[placeholder=请选择加签人员]")?.value==="own_operator_a"&&Array.from(document.querySelectorAll(".audit-form button")).some(e=>e.textContent.trim()==="提交"&&!e.disabled)'));
    await fs.writeFile(root+'/native-history-browser-fault-observed.json',JSON.stringify({oneFailedPost:true,opinionAndSelectedUserRetained:true,realServerErrorObserved:true}));
    await until(async()=>{try{return JSON.parse(await fs.readFile(root+'/native-history-fault-removed-retry-ready.json','utf8')).passed===true;}catch{return false;}},60000);
    cases.push({case:'real-native-sql-fault-preserves-ui-and-eight-scoped-table-fingerprints-before-retry',passed:true});
   }
"""
browser=once(browser,anchor,insert+anchor)
browser=once(browser,"const sent=http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).slice(before);","const sent=http.filter(x=>x.path.includes('/FlowBefore/freeApprover/')).slice(before+(wire.expectNativeHistorySQLFault?1:0));")
browser=once(browser,'nativeAddsignRequests:1,addsignType:wire.addsignType','nativeSuccessfulAddsignRequests:1,nativeFailedAddsignRequests:wire.expectNativeHistorySQLFault?1:0,addsignType:wire.addsignType')
save('verify_native_personal_workflow_r200_20261103.mjs',browser)
save('run_personal_workflow_r200_20261103.py',(V/'run_personal_workflow_r199_20261103.py').read_text(encoding='utf-8').replace('r199','r200').replace('r99','r100'))
print('ORIGINAL_NATIVE_HISTORY_SQL_FAULT_ROLLBACK_INPUT_RETENTION_AND_ONE_RETRY_SUITE_PREPARED')
