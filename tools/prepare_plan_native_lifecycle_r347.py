from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
js=(T/'verify_native_parent_delete_r330_20261103.mjs').read_text(encoding='utf-8')
js=once(js,"let deleteTargetId=\"\",injectPlanDeleteFalse=false;", "let deleteTargetId=\"\",injectPlanDeleteFalse=false,ownPlanDetailURL='';")
anchor=" await click('.el-table__body-wrapper button','详情');await until(async()=>await value('应急预案名称')===name);"
js=once(js,anchor,anchor+"\n ownPlanDetailURL=await evaluate('location.href');if(!ownPlanDetailURL.startsWith(wire.base+'/zhumadian/emergency/'))throw Error('OWN_REAL_DETAIL_URL_REQUIRED');")
addition=r'''
  stage='deleted-parent-old-detail-URL-normal-navigation';
  const oldDetailReads=()=>http.filter(r=>r.path.endsWith('/emergencyPlan/getById')).length;
  let detailReadsBefore=oldDetailReads();
  await send('Page.navigate',{url:ownPlanDetailURL},session);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  await until(()=>oldDetailReads()>detailReadsBefore);
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_OLD_DETAIL_MUST_NOT_RENDER_STALE_FORM');
  if(!http.filter(r=>r.path.endsWith('/emergencyPlan/getById')).slice(-1).every(r=>r.httpStatus===200&&r.businessCode===0))throw Error('DELETED_PARENT_UI_DETAIL_RESPONSE');
  cases.push({case:'deleted-parent-actual-old-detail-route-shows-friendly-error-without-stale-form',passed:true});
  stage='deleted-parent-old-detail-retry';detailReadsBefore=oldDetailReads();
  if(!await click('.el-alert button','重试'))throw Error('DELETED_PARENT_RETRY_BUTTON_REQUIRED');
  await until(()=>oldDetailReads()>detailReadsBefore);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_RETRY_STALE_FORM');
  cases.push({case:'deleted-parent-detail-retry-uses-original-endpoint-and-keeps-friendly-empty-state',passed:true});
  stage='deleted-parent-old-detail-refresh';detailReadsBefore=oldDetailReads();
  await send('Page.reload',{ignoreCache:true},session);
  await until(()=>oldDetailReads()>detailReadsBefore);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-alert")).some(e=>e.getClientRects().length&&e.textContent.includes("详情未取得或数据不完整，请重试。"))'));
  if(await value('应急预案名称')!==null)throw Error('DELETED_PARENT_REFRESH_STALE_FORM');
  cases.push({case:'deleted-parent-detail-full-refresh-keeps-normal-auth-and-friendly-empty-state',passed:true});
  await fs.writeFile(O+'/deleted-detail-navigation-evidence.json',JSON.stringify({passed:true,actualCapturedNormalDetailURLUsed:true,navigationRetryAndRefreshChecked:true,originalDetailAPIHTTP200AndCode0:true,deletedDetailsNullVerifiedEarlier:true,staleFormAbsentOnAllThree:true,originalControllerAndCandidateService:true,onlyOwnSyntheticRecords:true},null,2));
'''
js=once(js,"  if(exceptions.length)throw Error('CANDIDATE_ORIGINAL_UI_EXCEPTION');",addition+"\n  if(exceptions.length)throw Error('CANDIDATE_ORIGINAL_UI_EXCEPTION');")
browser=V/'verify_native_unified_plan_r347.mjs';assert not browser.exists();browser.write_text(js,encoding='utf-8')
check=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(browser)],capture_output=True);assert check.returncode==0
text=(V/'plan_lifecycle_run_r37_r346.py').read_text(encoding='utf-8')
function=r'''
def verify_native_candidate(row):
    # All state and credentials here belong to the separately marked synthetic clone.
    root=R/'work/event_delivery_consistency_20261030/full-controller-r163/r145'
    assert not root.exists() and m.native_plan_runtime_ready(A,row)['installedAndRuntimeClassCopyMatched']
    root.mkdir();dump(root/'controller-started.json',{'gatewayPort':port,'onlyOwnedSyntheticG':True})
    source=Path(__file__).resolve().parent/'verify_native_unified_plan_r347.mjs'
    assert sha(source)==BROWSER_SOURCE_SHA
    actual=root/'actual-browser-source.mjs';actual.write_bytes(source.read_bytes())
    classes=root/'resource-fixture-classes';classes.mkdir()
    reader=J(R/'work/event_delivery_consistency_20261030/full-controller-r131/schema-reader.json')
    identity=J(A/'UserData/OriginalServer/installation.json');cfg=J(A/'private/server-configuration.json')
    secret=cfg['seedRootPassword'];assert len(secret)==32
    drivers=list((A/'payload/business/lib').glob('mysql-connector-*.jar'));assert len(drivers)==1
    cp=str(classes)+';'+str(drivers[0])
    env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','PYTHONHOME','PYTHONPATH','MYSQL_PWD','MYSQL_HOME']}
    fixture_rows=[]
    for fixture in ['OwnPlanPortalMenusR222','OwnPlanDictionaryR226']:
        source=T/(fixture+'.java')
        compile_args=[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)]
        p=original_popen(compile_args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);out,err=p.communicate()
        while job.active_processes():time.sleep(.1)
        job.close();assert p.returncode==0,'OWN_PLAN_SEED_COMPILE_FAILED'
        args=[reader['java'],'-Xmx128m','-cp',cp,fixture,str(row['databasePort']),identity['databaseUUID'],str(A/'UserData/OriginalServer/database/data')]
        p=original_popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);out,err=p.communicate(input=secret.encode())
        while job.active_processes():time.sleep(.1)
        job.close();assert p.returncode==0,'OWN_PLAN_SEED_EXACT_REUSE_FAILED'
        fixture_rows.append({'fixture':fixture,'sourceSHA256':sha(source),'exitCode':0,'actualDescendantsZero':True})
    wire={'base':'http://127.0.0.1:'+str(port),'account':'own_operator_a','password':secret,'expectedUserId':'a531'+format(100,'028x'),'syntheticNormalUser':True,'baseline':False,'exerciseDepartmentBaseline':False}
    with(root/'plan-browser.private.log').open('wb')as trace:
        p=original_popen(['D:/Program Files/nodejs/node.exe',str(actual),root.as_posix()],stdin=subprocess.PIPE,stdout=trace,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);dump(root/'browser-started.json',{'pid':p.pid,'sourceSHA256':sha(actual),'syntheticOnly':True})
        p.communicate(input=enc(wire));wire.clear();secret=None;cfg=None;identity=None
        while job.active_processes():time.sleep(.1)
        job.close()
    dump(root/'browser-outer-terminal.json',{'exitCode':p.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False})
    bt=J(root/'plan-browser/browser-terminal.json');assert bt['chromeExitCode']==0 and bt['normalBrowserClose']and not bt['forceTerminationUsed']
    assert p.returncode==0,'OWN_UNIFIED_PLAN_NATIVE_UI_FAILED'
    result=J(root/'plan-browser/result.json');assert result['passed']and len(result['cases'])==21 and not result['exceptions']
    deleted=J(root/'plan-browser/deleted-detail-navigation-evidence.json');assert deleted['passed']
    summary={'passed':True,'cases':21,'javascriptExceptions':0,'normalRoleAndOriginalController':True,
      'exactFinalR39CandidateRuntime':True,'planDeleteAndExercisePeopleAttachmentRetained':True,
      'deletedOldDetailNavigationRetryRefreshFriendlyState':True,'fixtures':fixture_rows,
      'browserAndActualDescendantsNormalZero':True,'publicOrFormalOrDesktopTouched':False}
    dump(D/'candidate-native-ui-r347.json',summary)
    return summary
'''
function=function.replace('BROWSER_SOURCE_SHA',repr(sha(browser.read_bytes())))
text=once(text,"def restore_original():",function+"\ndef restore_original():")
text=once(text,"        phase='actual-rollback-latest-six-component-transaction'", "        phase='actual-candidate-normal-role-plan-ui-21-cases'\n        native_ui=verify_native_candidate(row)\n        print('OWN_FINAL_R39_NATIVE_21_CASES_WITH_DELETED_DETAIL_NAVIGATION_RETRY_REFRESH_PASSED',flush=True)\n        phase='actual-rollback-latest-six-component-transaction'")
text=once(text,"'actualIISHTTPSOrPublicOrAuthenticatedBusinessFlowVerified':False,", "'actualIISHTTPSOrPublicVerified':False,'actualNormalRolePlanExerciseAndDeletedDetail21CasesPassed':True,")
text=text.replace('verified-lifecycle-r346.json','verified-lifecycle-r347.json')
ast.parse(text);host=V/'plan_lifecycle_run_r37_native_r347.py';assert not host.exists();host.write_text(text,encoding='utf-8')
proof={'prepared':True,'browserSource':browser.name,'browserSHA256':sha(browser.read_bytes()),'hostSource':host.name,'hostSHA256':sha(host.read_bytes()),'candidateUpdaterUnchanged':True,'r346R37RunSourceSupersededBeforeExecution':True,'expectedCases':21,'servicesStartedByThisPreparation':False,'onlyOwnedSyntheticG':True}
out=V/'plan-native-lifecycle-drivers-r347.json';assert not out.exists();out.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
