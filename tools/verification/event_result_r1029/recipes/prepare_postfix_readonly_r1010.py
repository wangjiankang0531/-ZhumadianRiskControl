from pathlib import Path
import ast,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');H=V/'event_crud_r1010';OLD=V/'event_crud_r1004'
J=lambda p:json.loads(Path(p).read_bytes())
old=J(R/'work/ev1004/verified-event-crud-r1004.json');context=J(R/'work/ev1004/event-context.private.json')
assert old['codeRestored']and old['privateConfigurationRestored']and old['originalCurrentPointerRestored']and len(old['terminals'])==2
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in old['terminals'])
assert context['phase']=='delete-and-false-save-verified'and J(R/'work/ev1004/browser/first-start/result.json')['passed']
assert J(R/'work/ev1004/browser/normal-restart/result.json')['type']=='EVENT_RESPONSE_OBSERVATION_FAILED'
source=(V/'prepare_event_crud_r1004.py').read_text('utf8').replace('r1004','r1010').replace('R1004','R1010').replace('ev1004','ev1010').replace('ecfg1004','ecfg1010')
p=V/'prepare_event_crud_r1010.py';assert not p.exists();p.write_text(source,encoding='utf8')
r=subprocess.run(['python',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
for name in ['verify_event_crud_r1004.mjs','event_crud_probe_r1004.py','test_event_receiver_configuration_r1004.py']:
 s=(OLD/name).read_text('utf8').replace('r1004','r1010').replace('R1004','R1010').replace('ev1004','ev1010').replace('ecfg1004','ecfg1010')
 if name.endswith('.mjs'):
  s=s.replace("contextFile=root+'/event-context.private.json'","contextFile='D:/Project/Zhumadian/work/ev1004/event-context.private.json'").replace("const name='OWN_EVENT_CRUD_R1010_'","const name='OWN_EVENT_CRUD_R1004_'")
  s=s.replace("!['first-start','normal-restart'].includes(w.phase)","w.phase!=='normal-restart'")
  s=s.replace("stage='start',proof,problem=null;","stage='start',proof,problem=null,expectedDetailId='';")
  s=s.replace('function observe(v){',"const critical=path=>['/oauth/Login','/oauth/CurrentUser','/eventInfo/getById'].some(s=>path.endsWith(s));\nfunction observe(v){")
  anchor='const u=new URL(v.params.request.url),sid=v.sessionId;';assert s.count(anchor)==1
  s=s.replace(anchor,anchor+"\n  if(u.origin===w.base&&/\\/eventInfo\\/(save|updateById|removeById|closeRecord)$/.test(u.pathname)){problem='READ_ONLY_MUTATION_REFUSED';send('Fetch.failRequest',{requestId:v.params.requestId,errorReason:'BlockedByClient'},sid).catch(()=>{});return}")
  anchor="tracked.set(key,{path:u.pathname,method:v.params.request.method,secondaryContext:v.sessionId!==firstSession});";assert s.count(anchor)==1
  s=s.replace(anchor,"tracked.set(key,{path:u.pathname,method:v.params.request.method,secondaryContext:v.sessionId!==firstSession,...(u.pathname.endsWith('/eventInfo/getById')?{expectedOwnDetailId:u.searchParams.get('id')===expectedDetailId}:{})});")
  anchor="const row=tracked.get(v.sessionId+':'+v.params.requestId);if(!row)return;";assert s.count(anchor)==1
  s=s.replace(anchor,anchor+"\n  if(!critical(row.path)){row.bodyNotInspected=true;row.bodySettled=true;requests.push(row);return}")
  s=s.replace("row.code=b.code;row.booleanResult=", "row.code=b.code;row.dataIsNull=b.data===null;row.booleanResult=")
  s=s.replace("}).catch(()=>{problem='EVENT_RESPONSE_OBSERVATION_FAILED'}).finally(()=>reads.delete(p));", "}).catch(()=>{row.observationFailed=true;requests.push(row);problem='CRITICAL_RESPONSE_OBSERVATION_FAILED:'+row.path}).finally(()=>{row.bodySettled=true;reads.delete(p)});")
  start=s.index(' let context;');end=s.index(' await Promise.all([...reads]);',start)
  body=''' const context=JSON.parse(await fs.readFile(contextFile,'utf8'));
 if(context.phase!=='delete-and-false-save-verified'||context.nonce!==w.nonce||context.name!==name||typeof context.id!=='string'||!context.id)throw Error('EXACT_EXISTING_DELETED_POSTFIX_CONTEXT');
 expectedDetailId=context.id;stage='read-only-restart-list-and-api';
 check((await exactRecord()).length===0,'normal-restart-retains-deleted-event-state-without-recreation');
 await search(false);await until(()=>evaluate('!!document.querySelector(".el-table__body-wrapper")'));
 check(!await evaluate(`!!(${rowExpr})`),'original-normal-list-excludes-only-target-deleted-record');
 check(await api('/eventInfo/getById?id='+encodeURIComponent(context.id))===null,'normal-original-api-returns-null-for-deleted-record');
 await until(()=>reads.size===0&&![...tracked.values()].some(r=>critical(r.path)&&!r.bodySettled));
 stage='actual-native-invalid-detail';
 await send('Page.navigate',{url:w.base+'/zhumadian/emergency/emergencyResponse/response/edit?type=edit&id='+encodeURIComponent(context.id)},session);
 await until(()=>evaluate('document.body.textContent.includes("详情未取得，请返回列表刷新后重试。")'));
 await until(()=>requests.some(r=>r.path.endsWith('/eventInfo/getById')&&r.expectedOwnDetailId&&r.code===0&&r.dataIsNull));
 check(true,'original-detail-UI-observes-real-null-and-displays-failure-notice');
 await until(async()=>await value('事件名称')!==null&&!!await value('上报人'));
 check(await value('事件名称')==='','invalid-detail-does-not-corrupt-default-form-object');
 check(count('/eventInfo/save')===0&&count('/eventInfo/updateById')===0&&count('/eventInfo/removeById')===0,'read-only-probe-business-mutations-zero');
'''
  s=s[:start]+body+s[end:]
  assert 'create-issued-do-not-retry'not in s and "await action('删除')"not in s
  s=s.replace("mutationsOnlyThroughOriginalUI:true","readOnlyOriginalUIAndAPI:true")
 (H/name.replace('r1004','r1010')).write_text(s,encoding='utf8')
p=H/'home_transfer_health_r906.py';s=p.read_text('utf8').replace('exactPublicR47ProgramAndControllerBytes','exactPreparedR48ProgramAndControllerBytes').replace("plan['onlyPrivateConfigurationManifestPinAdapted']","plan['onlySixOwnedDockReceiverURLsAndPrivateManifestPinsAdapted']").replace('exactR47UpdaterAndCoreUsed','exactPreparedR48UpdaterAndCoreUsed');p.write_text(s,encoding='utf8')
p=H/'run_event_crud_r1010.py';s=p.read_text('utf8');end=s.index('"""',3)+3;s='"""Read-only R48 resume: preserve the same already-deleted R1004 event and validate missing detail with critical response observation drained before navigation. No new business mutation branch exists."""'+s[end:]
s=s.replace("fixture_nonce=secrets.token_hex(16)","fixture_nonce=J(R/'work/ev1004/event-context.private.json')['nonce']").replace("for label in ['first-start','normal-restart']:","for label in ['normal-restart']:")
s=s.replace('len(checks)==2','len(checks)==1').replace('len(probeChecks)==2','len(probeChecks)==1').replace("'actualTwoSixComponentLifecycles'","'actualOneReadOnlyResumeLifecycle'")
s=s.replace("query=\"(Get-CimInstance","query=\"$ErrorActionPreference='Stop'; (Get-CimInstance")
s=s.replace("'actualIISTLSOrPublicAccepted':False,","'actualIISTLSOrPublicAccepted':False,'newR48SparsePublisherAcceptedByThisRun':False,'exactPreparedR48ProgramsUsed':True,")
ast.parse(s);p.write_text(s,encoding='utf8')
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_event_crud_r1010.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
D=R/'Document/Deployment/event_crud_native_r1010_20261105';(D/'prepared-readonly-r1010.json').write_text(json.dumps({'preparedOnly':True,'sameR1004DeletedContextReadOnly':True,'criticalJSONObservationOnlyAndDrainedBeforeNavigation':True,'allEventMutationsBlockedAndNoMutationMainBranch':True,'productSourcesUnchanged':True,'runtimeAccepted':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'readOnlyOnly':True,'newBusinessDataCreated':False}))
