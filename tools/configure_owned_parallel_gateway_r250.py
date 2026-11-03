from pathlib import Path
import copy,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r121';f=P/'own-serial-definition.json'
assert json.loads((A.parent/'own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert not(C/'r121').exists()and not(P/'parallel-gateway-scope.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='redis-server.exe' OR Name='nginx.exe' OR Name='chrome.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
before=f.read_bytes();d=json.loads(before);assert d['syntheticInputOnly']and d['formBody']['enCode']=='OWN_SERIAL_R163_r121'
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
raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode();f.write_bytes(raw)
(P/'parallel-gateway-scope.json').write_text(json.dumps({'ownedSyntheticDefinitionOnly':True,'beforeSHA256':hashlib.sha256(before).hexdigest(),'afterSHA256':hashlib.sha256(raw).hexdigest(),'originalDesignerConditionType':'interflow','distinctBranchNodes':2,'perNodeCounterSign':0,'eachBranchOneOrdinaryApprover':True,'realTemplateOrProductChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'configuredSyntheticParallelBranchNodes':2,'productOrPublicChanged':False}))
