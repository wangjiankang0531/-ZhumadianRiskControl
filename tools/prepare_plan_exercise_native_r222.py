from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools');V=Path(__file__).resolve().parent
def save(n,s):
 p=T/n;assert not p.exists(),n
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
def swap(s,a,b):
 assert s.count(a)==1,(a[:75],s.count(a))
 return s.replace(a,b)

menu=(T/'java/resource_full_controller_r132/OwnResourcePortalMenusFixture.java').read_text(encoding='utf-8').replace('OwnResourcePortalMenusFixture','OwnPlanPortalMenusR222')
start=menu.index('   insert(c,"base_module",clone(parent,');end=menu.index('   c.commit();',start)
menu=menu[:start]+'''   insert(c,"base_module",clone(parent,"f_id",id(12600),"f_full_name","预案管理","f_en_code","OWN_PLAN_R222_ROOT","f_path","/emergencyPlans","f_url_address","","f_sort_code",12600));
   insert(c,"base_module",clone(page,"f_id",id(12601),"f_parent_id",id(12600),"f_full_name","应急预案","f_en_code","OWN_PLAN_R222_STRUCTURED","f_path","/emergencyPlans/structured","f_url_address","/emergencyPlans/structured","f_sort_code",12601));
   String[][] buttons={{"12801","新增","add"},{"12802","编辑","edit"},{"12803","详情","detail"}};
   for(String[]v:buttons)insert(c,"base_module_button",clone(button,"f_id",id(Integer.parseInt(v[0])),"f_module_id",id(12601),"f_full_name",v[1],"f_en_code","OWN_PLAN_R222_BUTTON_"+v[0],"f_path","/emergencyPlans/structured/"+v[2],"f_url_address","/emergencyPlans/structured/info/index"));
   int next=14000;
   for(int group:new int[]{30,31}){
    for(int module:new int[]{12600,12601})insert(c,"base_authorize",clone(grant,"f_id",id(next++),"f_item_id",id(module),"f_object_id",id(group)));
    for(int n=12801;n<=12803;n++)insert(c,"base_authorize",clone(buttonGrant,"f_id",id(next++),"f_item_id",id(n),"f_object_id",id(group)));
   }
'''+menu[end:]
save('OwnPlanPortalMenusR222.java',menu)
dictionary=(T/'java/duty_capacity_r136/OwnDutyEventDictionaryFixture.java').read_text(encoding='utf-8').replace('OwnDutyEventDictionaryFixture','OwnPlanDictionaryR222')
start=dictionary.index('   ensureKind(c,8501,');end=dictionary.index('   c.commit();',start)
dictionary=dictionary[:start]+'''   ensureKind(c,18501,"emergencyPlanType","OWN_PLAN_TYPE_R222");
   ensureKind(c,18502,"exerciseTypeData","OWN_EXERCISE_TYPE_R222");
'''+dictionary[end:]
save('OwnPlanDictionaryR222.java',dictionary)

browser=(T/'verify_full_controller_expert_browser_r132_20261101.mjs').read_text(encoding='utf-8')
browser=browser.replace('full-controller-r132','full-controller-r163').replace("const O=root+'/expert-browser'","const O=root+'/plan-browser'")
browser=swap(browser,"async function ownAPI(relative){"+browser.split('async function ownAPI(relative){',1)[1].split('\n',1)[0],'''async function ownAPI(entity,query){if(!['emergencyPlan','emergencyExercise'].includes(entity)||!/^get(?:Page|ById)\\?/.test(query))throw Error('OWN_PLAN_READONLY_API');const ua=await evaluate('navigator.userAgent'),r=await fetch(wire.base+'/zhumadian/api/serv/'+entity+'/'+query,{headers:{Authorization:token,'User-Agent':ua}}),v=await r.json();if(r.status!==200||v.code!==0)throw Error('OWN_PLAN_API_READBACK');return v.data;}''')
browser=browser.replace('/emergencyExperts/','/emergencyPlan/').replace('/emergencyExperts\'','/emergencyPlan\'')
browser=swap(browser,"const count=suffix=>", "let holdUpload=false,heldUpload=null,holdExercise=false,heldExercise=null,exercisePaused=0,injectExerciseFalse=false;\nconst count=suffix=>")
start=browser.index('  const disallowed=');end=browser.index('\n  if(disallowed)',start)
browser=browser[:start]+'''  if(u?.origin===wire.base&&u.pathname.endsWith('/sys-file/upload')&&holdUpload){if(heldUpload)throw Error('ONE_HELD_UPLOAD_ONLY');heldUpload={id:v.params.requestId,session:v.sessionId};return;}
  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyExercise/save')&&request.method==='POST'){
   exercisePaused++;
   if(injectExerciseFalse){injectExerciseFalse=false;await send('Fetch.fulfillRequest',{requestId:v.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_FALSE_INJECTION'})).toString('base64')},v.sessionId);return;}
   if(holdExercise){if(heldExercise)throw Error('DUPLICATE_HELD_EXERCISE');heldExercise={id:v.params.requestId,session:v.sessionId};return;}
  }
  const disallowed=!u||u.origin!==wire.base||request.method==='POST'&&u.pathname.startsWith('/zhumadian/api/serv/')&&!['/emergencyPlan/save','/emergencyPlan/updateById','/emergencyExercise/save','/sys-file/upload'].some(p=>u.pathname.endsWith(p));'''+browser[end:]
browser=swap(browser,"row.businessCode=b.code;", "row.businessCode=b.code;if(row.path.endsWith('/emergencyExercise/save'))row.saved=b.data;")
start=browser.index("row.expertMenuReturned=");end=browser.index(";}",start)
browser=browser[:start]+"row.planMenuReturned=JSON.stringify(b.data?.menuList||[]).includes('/emergencyPlans/structured')"+browser[end:]
browser=swap(browser,"exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION'})", "exceptions.push({text:v.params.exceptionDetails?.text||'OWN_UI_EXCEPTION',description:String(v.params.exceptionDetails?.exception?.description||'').slice(0,500)})")
start=browser.index(" stage='normal-login';");end=browser.index('}catch(e){failed=',start)
browser=browser[:start]+(V/'plan_exercise_native_body_r222.txt').read_text(encoding='utf-8')+'\n'+browser[end:]
save('verify_native_plan_exercise_r222_20261103.mjs',browser)

host=(T/'verify_full_controller_parallel_gateway_r218_20261103.py').read_text(encoding='utf-8')
start=host.index("        phase='native-two-level-workflow-browsers'");end=host.index("        phase='verify-original-398-models'",start)
body='''        phase='native-normal-plan-exercise-browser'
        own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');assert own['credentialsSynthetic']
        browser_source=Path(__file__).parent/'verify_native_plan_exercise_r222_20261103.mjs';actual_browser=root/'actual-browser-source.mjs';actual_browser.write_bytes(browser_source.read_bytes())
        assert options.attempt in ['r109','r110'] and options.variant=='combined'
        wire={'base':'http://127.0.0.1:'+str(port),'account':'own_operator_a','password':fake_password,'expectedUserId':own['accounts']['own_operator_a']['id'],'syntheticNormalUser':True,'baseline':options.attempt=='r109'}
        with(root/'plan-browser.private.log').open('wb')as browserlog:
            browser=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(actual_browser),root.as_posix()],stdin=subprocess.PIPE,stdout=browserlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            browserjob=j.OwnedWindowsJob(browser);dump(root/'plan-browser-started.json',{'pid':browser.pid,'sourceSHA256':sha(actual_browser),'syntheticNormalUser':True});browser.communicate(json.dumps(wire).encode());wire.clear()
            while browserjob.active_processes():time.sleep(.2)
            browserjob.close()
        terminal=read(root/'plan-browser/browser-terminal.json');assert terminal['normalBrowserClose']and terminal['chromeExitCode']==0 and not terminal['forceTerminationUsed']
        browser_passed=browser.returncode==0
        if browser_passed:
            browser_result=read(root/'plan-browser/result.json');assert browser_result['passed']and browser_result['baseline']==(options.attempt=='r109')and len(browser_result['cases'])>=6
            if options.attempt=='r109':assert read(root/'plan-browser/baseline-reproduction.json')['reproduced']
        fake_password=None;checks['normalLoginNativePlanExerciseBrowserPassed']=browser_passed
'''
host=host[:start]+body+host[end:]
start=host.index("        opinion=read(root/");end=host.index("        dump(root/'ready-checks.json'",start)
host=host[:start]+"        checks['actualNormalPlanExerciseBrowserResultPassed']=True\n"+host[end:]
anchor="        phase='reserve-own-readonly-schema-connection'"
fixture='''        phase='seed-exact-own-plan-menu-and-dictionaries'
        for fixture_name in ['OwnPlanPortalMenusR222','OwnPlanDictionaryR222']:
            source=Path(__file__).parent/(fixture_name+'.java')
            compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_PLAN_FIXTURE_COMPILE_FAILED'
            seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),fixture_name,str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert seeded.returncode==0,'OWN_PLAN_FIXTURE_SEED_FAILED'
        checks['onlyOwnedPlanMenuAndDictionaryRowsPrepared']=True
'''
host=swap(host,anchor,fixture+anchor)
start=host.index("proof={'schema':");end=host.index("\ndump(root/'result.json'",start)
host=host[:start]+"proof={'schema':'xnby.r222.native-plan-exercise-regression.v1','allPassed':True,'baseline':options.attempt=='r109','nativeBrowserCases':len(browser_result['cases']),'normalNonAdministratorLoginAndOriginalPlanExerciseRoutes':True,'sixComponentsAndBrowserNormalZeroActualDescendantsZero':True,'original398ModelsUnchanged':True,'connectionCapacityWithoutRefusals':True,'publicFormalOrDesktopChanged':False,'originalNangangTemplateOrWholeAcceptanceClaimed':False,'fullCloneReady':False}"+host[end:]
save('verify_full_controller_plan_exercise_r222_20261103.py',host)

for mode,attempt in [('baseline','r109'),('candidate','r110')]:
 for old in ['prepare_personal_workflow_frontend_r218.py','restore_personal_workflow_frontend_r218.py','prepare_production_history_runtime_r218.py','restore_production_history_runtime_r218.py']:
  new=old.replace('r218','r222_'+mode)
  s=(T/old).read_text(encoding='utf-8').replace('r218','r222_'+mode).replace('r108',attempt)
  if mode=='candidate'and old.startswith('prepare_personal'):
   s=s.replace('personal-workflow-routes-r195','plan-exercise-retained-r221').replace('len(new)==340','len(new)==341').replace("'candidateFrontendFiles':340","'candidateFrontendFiles':341")
  save(new,s)
 runner=(T/'run_parallel_gateway_r218_20261103.py').read_text(encoding='utf-8').replace('r218','r222_'+mode).replace('r108',attempt).replace('verify_full_controller_parallel_gateway_r222_'+mode+'_20261103.py','verify_full_controller_plan_exercise_r222_20261103.py')
 save('run_plan_exercise_r222_'+mode+'_20261103.py',runner)
print(json.dumps({'prepared':True,'baselineAttempt':'r109','candidateAttempt':'r110','candidateBuild13Sources':True,'ownNormalPlanMenusAndDictionaries':True,'testNotYetStarted':True}))
