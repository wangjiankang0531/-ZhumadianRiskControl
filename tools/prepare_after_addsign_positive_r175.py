from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent
for name in ['verify_full_controller_addsign_r172_20261102.py','run_addsign_r172_20261102.py']:
    p=V/name;s=p.read_text(encoding='utf-8');old="['r72','r73','r74']";assert s.count(old)==1;s=s.replace(old,"['r72','r73','r74','r75']");ast.parse(s);p.write_text(s,encoding='utf-8')
p=V/'verify_native_addsign_browser_r172_20261102.mjs';s=p.read_text(encoding='utf-8')
assert s.count('nativeRecords=[],nativeDownloadStarted=')==1;s=s.replace('nativeRecords=[],nativeDownloadStarted=','nativeRecords=[],nativeNodeProperties={},nativeDownloadStarted=')
needle="nativeRecords=Array.isArray(body.data?.flowTaskOperatorRecordList)?body.data.flowTaskOperatorRecordList:[];";assert s.count(needle)==1;s=s.replace(needle,needle+'nativeNodeProperties=body.data?.approversProperties||{};')
needle="   if(!['1','2'].includes(wire.addsignType))throw Error('EXACT_ORIGINAL_ADDSIGN_TYPE_REQUIRED');";assert s.count(needle)==1
s=s.replace(needle,needle+"\n   if(root.endsWith('/r75')&&nativeNodeProperties.counterSign!==1)throw Error('ACTUAL_PROVIDER_MUST_RETURN_OWN_COUNTERSIGN_NODE');\n   cases.push({case:'actual-provider-node-sign-type-before-addsign',counterSign:nativeNodeProperties.counterSign,passed:true});")
p.write_text(s,encoding='utf-8');r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
print(json.dumps({'afterPositiveAttemptAdded':'r75','actualProviderCounterSignMustBeOne':True,'originalR73RejectedEvidencePreserved':True,'noProductOrConfigurationChanged':True}))
