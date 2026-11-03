from pathlib import Path
import json,hashlib,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r106';f=P/'own-serial-definition.json'
assert json.loads((A.parent/'own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert not(C/'r106').exists()and not(P/'countersign-scope.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='redis-server.exe' OR Name='nginx.exe' OR Name='chrome.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
before=f.read_bytes();d=json.loads(before);assert d['syntheticInputOnly']and d['formBody']['enCode']=='OWN_SERIAL_R163_r106'
versions=json.loads(d['templateBody']['flowTemplateJson']);assert len(versions)==1;tree=json.loads(versions[0]['flowTemplateJson']);node=tree['childNode'];assert node['nodeId']=='approve'and node['properties']['counterSign']==0 and node['properties']['approvers']==['a5310000000000000000000000000065--user']
node['properties']['counterSign']=1
node['properties']['approvers']=['a5310000000000000000000000000064--user','a5310000000000000000000000000065--user']
versions[0]['flowTemplateJson']=json.dumps(tree);d['templateBody']['flowTemplateJson']=json.dumps(versions);d['onlySyntheticFirstNodeChangedToTwoApproverCountersign']=True
raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode();f.write_bytes(raw)
(P/'countersign-scope.json').write_text(json.dumps({'ownedSyntheticDefinitionOnly':True,'beforeSHA256':hashlib.sha256(before).hexdigest(),'afterSHA256':hashlib.sha256(raw).hexdigest(),'firstNodeCounterSignBefore':0,'firstNodeCounterSignAfter':1,'ownNormalApprovers':2,'productOrRealTemplateChanged':False,'realTemplateOrProductChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'onlySyntheticFirstNodeCounterSign':1,'runtimeProductOrOriginalSDKChanged':False}))
