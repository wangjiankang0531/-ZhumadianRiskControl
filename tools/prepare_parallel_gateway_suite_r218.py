from pathlib import Path
import ast,json

T=Path('D:/Project/Zhumadian/Application/tools')
def save(name,s):
    p=T/name
    assert not p.exists(),name
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s,encoding='utf-8')
def swap(s,a,b):
    assert s.count(a)==1,(a[:90],s.count(a))
    return s.replace(a,b)

for name in ['prepare_personal_workflow_frontend_r216.py','restore_personal_workflow_frontend_r216.py',
             'prepare_production_history_runtime_r216.py','restore_production_history_runtime_r216.py',
             'OwnPersonalWorkflowMenuVisibilityR216.java']:
    save(name.replace('r216','r218').replace('R216','R218'),
         (T/name).read_text(encoding='utf-8').replace('r216','r218').replace('R216','R218').replace('r107','r108'))

config='''from pathlib import Path
import copy,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r108';f=P/'own-serial-definition.json'
assert json.loads((A.parent/'own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert not(C/'r108').exists()and not(P/'parallel-gateway-scope.json').exists()
query="(Get-CimInstance Win32_Process -Filter \\"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='redis-server.exe' OR Name='nginx.exe' OR Name='chrome.exe'\\" | Where-Object {($_.CommandLine -replace '\\\\\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
before=f.read_bytes();d=json.loads(before);assert d['syntheticInputOnly']and d['formBody']['enCode']=='OWN_SERIAL_R163_r108'
versions=json.loads(d['templateBody']['flowTemplateJson']);assert len(versions)==1;tree=json.loads(versions[0]['flowTemplateJson']);first=tree['childNode'];assert first['nodeId']=='approve'and first['properties']['counterSign']==0
final=first['childNode'];assert final['nodeId']=='approve_final_r163'
branches=[]
for suffix,user in [('a','a5310000000000000000000000000064--user'),('b','a5310000000000000000000000000065--user')]:
    node=copy.deepcopy(first);node.update(nodeId='own_parallel_'+suffix+'_r218',prevId=tree['nodeId'],childNode=None,conditionNodes=None,conditionType=None,isInterflow=True)
    node['properties'].update(title='OWN_PARALLEL_'+suffix.upper(),approvers=[user],counterSign=0,autoSubmit=False)
    assert not node['properties']['endFuncConfig']['on']
    branches.append(node)
tree.update(conditionType='interflow',conditionNodes=branches,childNode=final);final['prevId']=tree['nodeId']
versions[0]['flowTemplateJson']=json.dumps(tree);d['templateBody']['flowTemplateJson']=json.dumps(versions)
d.update(onlySyntheticParallelGatewayConfigured=True,parallelBranchNodes=2,firstReviewer='two_distinct_parallel_nodes',originalNangangTemplate=False)
raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\\n').encode();f.write_bytes(raw)
(P/'parallel-gateway-scope.json').write_text(json.dumps({'ownedSyntheticDefinitionOnly':True,'beforeSHA256':hashlib.sha256(before).hexdigest(),'afterSHA256':hashlib.sha256(raw).hexdigest(),'originalDesignerConditionType':'interflow','distinctBranchNodes':2,'perNodeCounterSign':0,'eachBranchOneOrdinaryApprover':True,'realTemplateOrProductChanged':False},indent=2)+'\\n',encoding='utf-8')
print(json.dumps({'configuredSyntheticParallelBranchNodes':2,'productOrPublicChanged':False}))
'''
save('configure_owned_parallel_gateway_r218.py',config)

java=(T/'OwnOrSignWorkflowReadbackR216.java').read_text(encoding='utf-8').replace('OwnOrSignWorkflowReadbackR216','OwnParallelGatewayReadbackR218')
java=swap(java,'import java.io.*;import java.nio.file.*;import java.sql.*;','import java.io.*;import java.nio.file.*;import java.sql.*;import java.util.*;')
java=swap(java,'a.length==12','a.length==13')
java=swap(java,'a[10].matches("[01]|observe")','a[10].matches("[012]|observe")')
java=swap(java,'c.rollback();boolean passed=', '''stage="PARALLEL_TASK_KEYS";Set<String> keys=new HashSet<>();try(PreparedStatement p=c.prepareStatement("SELECT TASK_DEF_KEY_ FROM jnpf.act_ru_task WHERE PROC_INST_ID_=?")){p.setString(1,a[3]);try(ResultSet r=p.executeQuery()){while(r.next())need(keys.add(r.getString(1)));}}
   Set<String> expected;if(Set.of("operator","operator-disposal","reviewer-preview").contains(a[12]))expected=Set.of("own_parallel_a_r218","own_parallel_b_r218");else if(Set.of("operator-added","operator-waiting-parallel-b").contains(a[12]))expected=Set.of("own_parallel_b_r218");else if(a[12].equals("reviewer-after-added"))expected=Set.of("approve_final_r163");else if(Set.of("reviewer-final","reviewer-handled-readback","operator-completed-readback").contains(a[12]))expected=Set.of();else throw new Exception("OWN_PARALLEL_UNKNOWN_PHASE");need(keys.equals(expected));
   c.rollback();boolean passed=''' )
java=swap(java,'serial=model!=null&&model.contains("approve_final_r163");','serial=model!=null&&model.contains("approve_final_r163")&&model.contains("interflow")&&model.contains("own_parallel_a_r218")&&model.contains("own_parallel_b_r218");')
java=swap(java,'System.out.println("OWN_PROOF:passed:"+passed);','System.out.println("OWN_PROOF:parallelDistinctTaskDefinitionKeysMatchExpected:"+keys.equals(expected));System.out.println("OWN_PROOF:passed:"+passed);')
save('OwnParallelGatewayReadbackR218.java',java)

browser=(T/'verify_native_parallel_countersign_r215_20261103.mjs').read_text(encoding='utf-8')
browser=swap(browser,"'operator-waiting-parallel-b'].includes(wire.phaseName)","'operator-waiting-parallel-b','reviewer-preview'].includes(wire.phaseName)")
start=browser.index("   if(['operator-added','reviewer-after-added'].includes(wire.phaseName)){")
end=browser.index("   if(wire.phaseName==='reviewer-final'",start)
browser=browser[:start]+'''   if(['operator-added','reviewer-after-added'].includes(wire.phaseName)){
    const isA=wire.phaseName==='operator-added',expectedUser=isA?'a5310000000000000000000000000064--user':'a5310000000000000000000000000065--user';
    if(nativeNodeProperties.counterSign!==0||nativeNodeProperties.title!==(isA?'OWN_PARALLEL_A':'OWN_PARALLEL_B')||JSON.stringify(nativeNodeProperties.approvers)!==JSON.stringify([expectedUser]))throw Error('ACTUAL_DISTINCT_PARALLEL_BRANCH_AND_SINGLE_ASSIGNEE_REQUIRED');
    if(!isA){const first=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_operator-added'&&x.nodeName==='OWN_PARALLEL_A'&&x.handleTime);if(first.length!==1)throw Error('BRANCH_A_DONE_B_STILL_PENDING_REQUIRED');}
    cases.push({case:'distinct-parallel-branch-single-normal-assignee-'+wire.phaseName,passed:true});
   }
'''+browser[end:]
browser=swap(browser,"  if(wire.approveOnce){\n",'''  if(wire.phaseName==='reviewer-preview'){
   if(nativeNodeProperties.title!=='OWN_PARALLEL_B'||nativeNodeProperties.counterSign!==0)throw Error('SECOND_DISTINCT_BRANCH_MUST_BE_PENDING_BEFORE_FIRST_APPROVAL');
   cases.push({case:'second-distinct-parallel-node-already-pending-before-first-node-approval',passed:true});
  }
  if(wire.approveOnce){
''')
browser=browser.replace('SECOND_COUNTERSIGN_APPROVAL_MUST_ADVANCE_TO_FINAL_NODE','BOTH_PARALLEL_BRANCHES_REQUIRED_BEFORE_FINAL_NODE')
browser=swap(browser,"  if(first.length!==1||second.length!==1||final.length!==1||Number(first[0].handleTime)>Number(second[0].handleTime)||Number(second[0].handleTime)>Number(final[0].handleTime))", "  if(first.length!==1||second.length!==1||final.length!==1||first[0].nodeName!=='OWN_PARALLEL_A'||second[0].nodeName!=='OWN_PARALLEL_B'||final[0].nodeName!=='OWN_FINAL_REVIEW'||Number(first[0].handleTime)>Number(second[0].handleTime)||Number(second[0].handleTime)>Number(final[0].handleTime))")
browser=browser.replace('parallel-countersign-observation.json','parallel-gateway-observation.json').replace('bothOrdinaryApproversAndFinalNodeOpinionsExactlyOnce','distinctBranchAndFinalNodeOpinionsExactlyOnce').replace('COUNTERSIGN','PARALLEL_GATEWAY')
save('verify_native_parallel_gateway_r218_20261103.mjs',browser)

host=(T/'verify_full_controller_parallel_countersign_r215_20261103.py').read_text(encoding='utf-8').replace('r215','r218').replace('R215','R218').replace('r106','r108').replace('OwnParallelWorkflowReadback','OwnParallelGatewayReadback').replace('verify_native_parallel_countersign','verify_native_parallel_gateway')
start=host.index('        phases=[');end=host.index('\n        state_source=',start)
host=host[:start]+"        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('reviewer-preview','own_reviewer_b','reviewer',False,False),('operator-added','own_operator_a','reviewer',True,False),('operator-waiting-parallel-b','own_operator_a','operator',False,False),('reviewer-after-added','own_reviewer_b','reviewer',True,False),('reviewer-final','own_operator_a','reviewer',True,False),('reviewer-handled-readback','own_reviewer_b','reviewer',False,False),('operator-completed-readback','own_operator_a','operator',False,False)]"+host[end:]
host=swap(host,"pending_expected='0' if ended else 'observe'", "pending_expected='0' if ended else '2' if label in ['operator','operator-disposal','reviewer-preview'] else '1'")
host=swap(host,'business_status,pending_expected,ended_expected]', 'business_status,pending_expected,ended_expected,label]')
host=host.replace('parallel-countersign-observation.json','parallel-gateway-observation.json').replace('bothOrdinaryApproversAndFinalNodeOpinionsExactlyOnce','distinctBranchAndFinalNodeOpinionsExactlyOnce').replace('TwoApproverCountersign','DistinctParallelBranches').replace('ParallelCountersign','ParallelGateway').replace('ordinaryCountersign','ordinaryParallelGateway').replace('native-parallel-countersign-regression','native-parallel-gateway-regression')
save('verify_full_controller_parallel_gateway_r218_20261103.py',host)
runner=(T/'run_parallel_countersign_r215_20261103.py').read_text(encoding='utf-8').replace('r215','r218').replace('r106','r108').replace('verify_full_controller_parallel_countersign','verify_full_controller_parallel_gateway')
save('run_parallel_gateway_r218_20261103.py',runner)
print(json.dumps({'suitePrepared':True,'attempt':'r108','distinctOriginalDesignerInterflowBranches':2,'normalBrowserPhases':9,'actualPendingKeysAndCountsRequired':True,'productPublicOrDesktopChanged':False}))
