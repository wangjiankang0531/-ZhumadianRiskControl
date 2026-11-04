"""Read-only reproduction of the failed picker query; no callback rebind or task submit."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;D=V/'event_picker_r883'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
 assert s.count(a)==1,a[:120]
 return s.replace(a,b)
def main():
 assert not D.exists();D.mkdir()
 s=(V/'feedback_r880/create_task_browser_r880.mjs').read_text('utf8')
 s=one(s,"const O=root+'/ui-create-r880';", "const O='D:/Project/Zhumadian/work/event-picker-browser-r883';")
 s=one(s,"let eventRows=[],eventPageCount=0", "let loginToken='',lastQuery='',queryDiagnostics=[];let eventRows=[],eventPageCount=0")
 a=s.index("  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventTask/save'){")
 b=s.index("  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventInfo/updateById'){",a)
 s=s[:a]+"  if(u.origin===w.base&&u.pathname==='/zhumadian/api/serv/eventTask/save'){allowed=false;problem='DIAGNOSTIC_TASK_MUTATION_REFUSED';}\n"+s[b:]
 s=one(s,"if(row.endpoint.endsWith('/oauth/Login')){logged=", "if(row.endpoint.endsWith('/oauth/Login')){loginToken=body.data?.token||'';logged=")
 a="tracked.set(v.params.requestId,{endpoint:u.pathname,method:r.method,...u.pathname.endsWith('/eventInfo/getPage')?{confirmedFilterMatched:u.searchParams.get('researchStatus')==='1'}:{}});"
 b="""tracked.set(v.params.requestId,{endpoint:u.pathname,method:r.method,...u.pathname.endsWith('/eventInfo/getPage')?{confirmedFilterMatched:u.searchParams.get('researchStatus')==='1',eventNameEqualsExpected:u.searchParams.get('eventName')===w.eventName,eventNameSHA256:createHash('sha256').update(u.searchParams.get('eventName')||'').digest('hex'),eventNameLength:(u.searchParams.get('eventName')||'').length,eventContentEmpty:!u.searchParams.get('eventContent'),page:u.searchParams.get('current'),size:u.searchParams.get('size')}:{}});
  if(u.pathname.endsWith('/eventInfo/getPage'))lastQuery=u.search;"""
 s=one(s,a,b)
 start=s.index(" const before=eventPageCount;await fill('事件名称',w.eventName,true);")
 end=s.index('}catch(error){proof=',start)
 body=r'''
 const initialOwnPresent=eventRows.some(r=>r.id===w.eventId);
 if(!initialOwnPresent)throw Error('EXPECTED_OWN_CONFIRMED_EVENT_NOT_IN_INITIAL_PICKER');
 const ua=await evaluate('navigator.userAgent');
 async function compare(base,path,query){
  const response=await fetch(base+path+query,{headers:{Authorization:loginToken,'User-Agent':ua},redirect:'error',signal:AbortSignal.timeout(15000)});
  const value=await response.json();return{httpStatus:response.status,businessCode:value.code,ownEventPresent:Array.isArray(value.data?.records)&&value.data.records.some(r=>r.id===w.eventId),rows:Array.isArray(value.data?.records)?value.data.records.length:null};
 }
 if(!Number.isInteger(w.businessPort)||w.businessPort<1025||w.businessPort>65535||[8767,18891,18892].includes(w.businessPort))throw Error('EXACT_OWN_BUSINESS_PORT_REQUIRED');
 for(const sample of [w.eventName,'Own','workflow','']){
  stage='original-picker-search';const before=eventPageCount;await fill('事件名称',sample,true);
  const input=await evaluate(`(()=>{const item=Array.from(document.querySelectorAll('.el-dialog')).find(e=>e.getClientRects().length)?.querySelector('.el-dialog__body');const e=Array.from(item.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\s:：]/g,'')==='事件名称')?.querySelector('input');return{domValueMatches:e?.value===${JSON.stringify(sample)},domValueLength:e?.value.length??null}})()`);
  await clickButton('搜索',true);await until(()=>eventPageCount>before);
  await Promise.all([...reads]);const row=requests.filter(r=>r.endpoint.endsWith('/eventInfo/getPage')).at(-1);
  const direct=await compare('http://127.0.0.1:'+w.businessPort,'/eventInfo/getPage',lastQuery);
  const gateway=await compare(w.base,'/zhumadian/api/serv/eventInfo/getPage',lastQuery);
  queryDiagnostics.push({sample:sample===w.eventName?'full-spaced-name':sample||'empty',...input,query:row,direct,gateway});
 }
 const canonical='?current=1&size=10&researchStatus=1&eventName='+encodeURIComponent(w.eventName);
 const plus='?current=1&size=10&researchStatus=1&eventName='+new URLSearchParams({eventName:w.eventName}).get('eventName');
 const variants=[];
 for(const [encoding,query] of [['percent20',canonical],['plus','?current=1&size=10&researchStatus=1&'+new URLSearchParams({eventName:w.eventName}).toString()]]){
  variants.push({encoding,direct:await compare('http://127.0.0.1:'+w.businessPort,'/eventInfo/getPage',query),gateway:await compare(w.base,'/zhumadian/api/serv/eventInfo/getPage',query)});
 }
 proof={passed:true,diagnosticCompleted:true,queryDiagnostics,variants,cases,requests,initialOwnEventPresent:initialOwnPresent,
  taskSaveRequests:saveAttempts,researchRequests:researchAttempts,callbackRebindingPerformed:false,businessMutationPerformed:false,
  readOnlyDirectAndGatewayComparisonUsed:true,APIsMocked:false,publicOrDesktopTouched:false,fullCloneReady:false};
'''
 s=s[:start]+body+s[end:]
 s=one(s," w.password='';current=null;", " w.password='';loginToken='';current=null;")
 q=D/'event_picker_browser_r883.mjs';q.write_text(s,encoding='utf8');assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(q)],capture_output=True).returncode==0
 s=(V/'probe_r45_original_backend_r850.py').read_text('utf8')
 s=s.replace("V/'r45_original_backend_health_r849.py'","V.parent/'r45_original_backend_health_r849.py'")
 s=s.replace('component-bootstrap-r850','event-picker-r883').replace('bootstrap-browser-r850','event-picker-browser-r883')
 s=s.replace("V/'verify_r45_original_backend_browser_r850.mjs'","V/'event_picker_browser_r883.mjs'")
 begin=s.index("    link=props(W/'snapshot-r810-submitted.properties')");end=s.index("    source=G/'tools/original_server_windows_job.py'",begin)
 s=s[:begin]+'''    flight=props(W/'flight.private.properties');assert flight['nonce']==nonce
    wire={'base':'http://127.0.0.1:'+str(gateway_port),'businessPort':row['businessPort'],'account':'own_operator_a',
      'password':J(G/'private/server-configuration.json')['seedRootPassword'],'expectedUserId':identity['accounts']['own_operator_a']['id'],
      'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True,'researchRequired':False,
      'eventId':'a5320000000000000000000000000006','eventNumber':'OWN-NORMAL-WORKFLOW-EVENT','eventName':'Own workflow event',
      'taskName':flight['taskName'],'taskContent':'Own task UI dispatch '+nonce}
'''+s[end:]
 s=one(s,"    result=J(OUT/'result.json');assert result['passed']and result['approvalRequests']==0 and not result['APIsMocked']", "    result=J(OUT/'result.json');assert result['passed']and result['taskSaveRequests']==result['researchRequests']==0 and not result['APIsMocked']")
 begin=s.index('    proof=dict(passed=True,actualCompiledApplicationAndOriginalSDK=True,');end=s.index("    return proof",begin)
 s=s[:begin]+'''    proof=dict(passed=True,diagnosticCompleted=True,businessMutationPerformed=False,callbackRebindingPerformed=False,
      queryDiagnostics=result['queryDiagnostics'],encodingVariants=result['variants'],actualCompiledApplicationAndOriginalSDK=True,publicOrDesktopTouched=False)
    (stage/'business-result-r883.json').write_text(json.dumps(proof,indent=2)+'\\n',encoding='utf8')
'''+s[end:]
 q=D/'event_picker_probe_r883.py';q.write_text(s,encoding='utf8');ast.parse(s)
 s=(V/'run_task_status_sequence_r875.py').read_text('utf8')
 s=s.replace("W=O/'task-ui-r806';P=O/'task-status-sequence-r875';Z=R/'work/task-status-full-r875'", "W=O/'feedback-r880';P=O/'event-picker-r883';Z=R/'work/ep883'")
 s=s.replace("V/'r45_original_backend_health_r849.py'","V.parent/'r45_original_backend_health_r849.py'")
 s=s.replace("V/'probe_task_status_sequence_r875.py'","V/'event_picker_probe_r883.py'")
 s=s.replace("V/'r45-compatibility-source-pins-r850.json'","V.parent/'r45-compatibility-source-pins-r850.json'")
 s=s.replace("V/'task-status-source-pins-r875.json'","V/'event-picker-source-pins-r883.json'")
 s=s.replace('task-status-not-started-r875.json','event-picker-not-started-r883.json').replace('verified-task-status-sequence-r875.json','verified-event-picker-r883.json').replace('task-status-full-result-r875.json','event-picker-full-result-r883.json')
 s=s.replace('actualReadOnlyCompletedTaskReopen','actualReadOnlyEventPickerDiagnostic').replace('normalLoginReadOnlyRoutesAndExistingDetailAccepted','normalLoginAndPickerQueryDiagnosticAccepted')
 s=one(s,"prior=J(R/'work/original-backend-full-r850/verified-component-bootstrap-r850.json')", "prior=J(R/'work/fb880/verified-feedback-chain-r880.json')")
 s=one(s,"assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']", "assert not prior['passed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']")
 s=one(s,"assert 'phase=restored'in(W/'resume-r810/manager-directory.private.properties').read_text('ascii').splitlines()", "assert 'phase=restored'in(W/'runtime/manager-directory.private.properties').read_text('ascii').splitlines()")
 q=D/'run_event_picker_full_r883.py';q.write_text(s,encoding='utf8');ast.parse(s)
 pins={str(q):sha(q) for q in D.glob('*')if q.is_file()}
 (D/'event-picker-source-pins-r883.json').write_text(json.dumps({'files':pins},indent=2)+'\n',encoding='utf8')
 print(json.dumps({'preparedFiles':len(pins),'readOnlyQueriesOnly':True,'callbackRebinding':False,'servicesStarted':False}))
if __name__=='__main__':main()
