"""Resume exactly the new attachment diagnostic record, never recreate it."""
from pathlib import Path
import ast,copy,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
OLD=V/'hazard_attachment_r1207';H=V/'hazard_transaction_r1212';D=R/'Document/Deployment/hazard_attachment_transaction_r1212_20261106';OD=R/'Document/Deployment/hazard_attachment_original_r1207_20261106'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def pin(p):return{'bytes':p.stat().st_size,'sha256':sha(p)}
def one(s,a,b):assert s.count(a)==1,a[:150];return s.replace(a,b)
assert not D.exists()and not H.exists()and not(R/'work/ht1212').exists()and not(R/'work/hazard-transaction-probe-r1212').exists()
previous=j(R/'work/ha1207/verified-hazard-runtime-r1207.json');assert previous['passed']and previous['codeRestored']and previous['originalCurrentPointerRestored']and j(OD/'parent-terminal-r1208.json')['actualJobDescendantsZero']
assert all(x['attachmentAtomicityDefectObserved']for x in previous['businessChecks'])
flight=j(R/'work/hazard-attachment-probe-r1207/hazard-attachment-flight.private.json');assert flight['phase']=='mainflow-completed'and flight['requests']=={'upload':1,'create':1,'failedEdit':1}and len(flight['ownId'])==32
assert sha(G/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
q="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',q],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0'
D.mkdir();H.mkdir();candidate=D/'candidate';candidate.mkdir()
plan=copy.deepcopy(j(OD/'full-source-and-restore-plan.private.json'));oldSHA=sha(OD/'full-source-and-restore-plan.private.json')
plan['schema']='xnby.hazard-attachment-resume-original-sdk.plan.v1'
plan['newOwnHazardCRUDScope']={'createMax':0,'uploadMax':1,'repairEditMax':1,'failedKeepEditMax':1,'normalRetryMax':1,'failedRemoveEditMax':1,'taskReplayForbidden':True,'exactPreviousOwnIdRequired':True,'originalDDLUnchanged':True}
plan['originalR45BackendControllerAndNonSafetyFrontendBytesUnchanged']=False
plan['originalBusinessJarAndAllControllersUnchanged']=True
classPath='payload/business/legacy-classes/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class'
cls=V/'hazard_transaction_r1210/classes/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class'
proof=j(R/'Document/Deployment/hazard_attachment_transaction_r1210_20261106/candidate-source-compile.json');assert sha(cls)==proof['candidateClassSHA256']and not(G/classPath).exists()
payload=j(Path(plan['sources']['payload-manifest.json']['source']));payload['files'][classPath]=pin(cls);(candidate/'payload-manifest.json').write_bytes(enc(payload))
release=j(Path(plan['sources']['release-manifest.json']['source']));release['payloadManifestSHA256']=sha(candidate/'payload-manifest.json');release['ownedHazardAttachmentAtomicCandidate']={'revision':'r1212-owned-resume','classPath':classPath,'classSHA256':sha(cls),'sourceSHA256':proof['candidateSourceSHA256'],'originalJarUnchanged':True,'schemaChanged':False,'publicAccepted':False};(candidate/'release-manifest.json').write_bytes(enc(release))
for name,src in [('payload-manifest.json',candidate/'payload-manifest.json'),('release-manifest.json',candidate/'release-manifest.json'),(classPath,cls)]:
 plan['sources'][name]={'source':str(src),**pin(src)};plan['mutations'][name]={'source':str(src),'before':plan['mutations'][name]['before']if name in plan['mutations']else None,'after':pin(src)}
plan['candidatePayloadManifestSHA256']=sha(candidate/'payload-manifest.json');plan['candidateReleaseSHA256']=sha(candidate/'release-manifest.json')
(D/'flight.private.json').write_bytes(enc({'schema':'xnby.own-hazard-attachment-resume-scope.v1','nonce':flight['nonce'],'ownId':flight['ownId'],'previousUploadUrl':flight['uploadUrl'],'previousFlightJournalSHA256':sha(R/'work/hazard-attachment-probe-r1207/hazard-attachment-flight.private.json'),'createMax':0}))
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan));newSHA=sha(D/'full-source-and-restore-plan.private.json')
for src in OLD.iterdir():
 if src.name not in ['run_hazard_runtime_r1207.py','hazard_health_r1207.py','hazard_receiver_r1207.py','OwnHazardFormMetadataR1207.java','OwnHazardStatisticsMenuFixtureR1172.java','own-attachment.png']:continue
 name=src.name.replace('r1207','r1212').replace('R1207','R1212')
 if src.suffix=='.png':(H/name).write_bytes(src.read_bytes());continue
 t=src.read_text('utf8').replace('hazard_attachment_original_r1207_20261106','hazard_attachment_transaction_r1212_20261106').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212').replace('ha1207','ht1212').replace('r1207','r1212').replace('R1207','R1212').replace(oldSHA,newSHA)
 if name.startswith('run_hazard'):
  t=t.replace('xnby.hazard-crud-owned-original-sdk.plan.v1',plan['schema']).replace("['createMax']==1","['createMax']==0").replace(" and plan['newOwnHazardCRUDScope']['failedEditMax']==1", " and plan['newOwnHazardCRUDScope']['failedRemoveEditMax']==1")
  t=t.replace('hazard_attachment_probe_r1212.py','hazard_transaction_probe_r1212.py').replace('actualNormalHazardCRUDUIProbe','actualOriginalHazardTransactionUIProbe').replace('normalLoginHazardCRUDUIProbeAccepted','normalLoginHazardTransactionUIProbeAccepted')
  t=t.replace('"""Prepare original models/callbacks using one actual owned full-candidate lifecycle.', '"""Test the original service transaction candidate on one existing owned hazard.')
 if name.startswith('hazard_health'):
  t=t.replace("'originalR45BackendHealthPreserved':True,'hazardSourceBackendReplaced':False", "'originalR45OtherBackendHealthPreserved':True,'hazardSourceBackendReplaced':True")
 if src.suffix=='.py':ast.parse(t)
 (H/name).write_text(t,encoding='utf8')
java=(OLD/'OwnHazardCrudReadR1207.java').read_text('utf8').replace('R1207','R1212').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212')
java=one(java,'a.length==6','a.length==7&&a[6].matches("[0-9a-f]{32}")')
java=one(java,'if(phase.equals("before"))need(matches==0,"DO_NOT_RECREATE_EXISTING_OWN_FLIGHT");','if(phase.equals("before"))need(matches==1&&a[6].equals(ownId)&&"Own material v1".equals(own.get("material_type"))&&"1".equals(own.get("status")),"EXACT_PREVIOUS_OWN_RECORD_ONLY_NO_RECREATE");')
java=one(java,'"Own material v1".equals(own.get("material_type"))&&"1".equals(own.get("status")),"EXPECTED_NORMAL_EDIT_THEN_SOFT_DELETE_STALE_WRITE_DID_NOT_COMMIT"','"Own material v2".equals(own.get("material_type"))&&"2".equals(own.get("status")),"EXPECTED_OWN_REPAIR_RETRY_AND_FAILURE_MAIN_ROW_PRESERVED"')
java=one(java,'"BOUNDED_SINGLE_OWN_ATTACHMENT_COUNT");}', '"BOUNDED_SINGLE_OWN_ATTACHMENT_COUNT");if(phase.equals("before"))need(attachments==0,"EXACT_DIAGNOSED_LOST_LINK_SCOPE");else need(attachments==1,"CANDIDATE_MUST_PRESERVE_OWN_ATTACHMENT_ON_FAILURE");}')
java=one(java,'result.setProperty("originalHazardRowsFingerprint"', '''if(ownId!=null)try(PreparedStatement p=c.prepareStatement("SELECT id FROM base_file WHERE correlation_id=?")){p.setString(1,ownId);try(ResultSet r=p.executeQuery()){if(r.next())result.setProperty("ownAttachmentId",r.getString(1));}}
   result.setProperty("originalHazardRowsFingerprint"''')
(H/'OwnHazardCrudReadR1212.java').write_text(java,encoding='utf8')
browser=(OLD/'hazard_attachment_browser_r1207.mjs').read_text('utf8').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212')
a=browser.index('const ownCode=');b=browser.index('async function clickPoint',a);browser=browser[:a]+(V/'hazard_transaction_observer_r1212.jsfrag').read_text('utf8')+'\n'+browser[b:]
a=browser.index(' await initializeFlight();');b=browser.index('}catch(e){',a);browser=browser[:a]+(V/'hazard_transaction_main_r1212.jsfrag').read_text('utf8')+'\n'+browser[b:]
browser=browser.replace('businessWriteRequests:mutations.create+mutations.failedEdit+mutations.upload','businessWriteRequests:Object.values(mutations).reduce((a,b)=>a+b,0)')
(H/'hazard_transaction_browser_r1212.mjs').write_text(browser,encoding='utf8')
probe=(OLD/'hazard_attachment_probe_r1207.py').read_text('utf8').replace('hazard_attachment_original_r1207_20261106','hazard_attachment_transaction_r1212_20261106').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212').replace('r1207','r1212').replace('R1207','R1212')
probe=one(probe,"str(out),f'a531{120002:028x}']", "str(out),f'a531{120002:028x}',flight['ownId']]")
probe=one(probe,"wire={'base'", "wire={'ownId':flight['ownId'],'base'")
probe=probe.replace('hazard_attachment_browser_r1212.mjs','hazard_transaction_browser_r1212.mjs')
probe=one(probe,"assert len(ui['attachmentBefore'])==1 and ui['failedEditPreservedMainRow'];assert j(P/'ui-mainflow/verified-png.json')['passed'];", "assert ui['attachmentAtomicityPreserved'] and ui['normalRetryAccepted'] and ui['failedEditPreservedMainRow'];assert after['ownAttachmentId']==ui['attachmentAfter'][0]['id'];assert j(P/'ui-mainflow/verified-png.json')['passed'];")
probe=probe.replace("'diagnosisNotProductAcceptance':True", "'scopedCandidateAcceptanceOnly':True").replace("'oneCreateUploadAndFailingEdit':label=='mainflow'", "'sameExistingOwnRecordNoCreate':True,'repairAndFailedKeepAndValidRetryAndFailedRemove':label=='mainflow'")
probe=probe.replace("'verified-attachment-diagnosis.json'","'verified-attachment-transaction.json'")
ast.parse(probe);(H/'hazard_transaction_probe_r1212.py').write_text(probe,encoding='utf8')
launch=(V/'launch_hazard_attachment_r1208.py').read_text('utf8').replace('hazard_attachment_original_r1207_20261106','hazard_attachment_transaction_r1212_20261106').replace('hazard_attachment_r1207','hazard_transaction_r1212').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212').replace('ha1207','ht1212').replace('r1207','r1212').replace('R1207','R1212').replace('r1208','r1213').replace('R1208','R1213')
ast.parse(launch);(V/'launch_hazard_transaction_r1213.py').write_text(launch,encoding='utf8')
pins={str(p):sha(p)for p in H.iterdir()if p.is_file()}
for p in [V/'original_public_test_update_r45_bootstrap_r847.py',A/'tools/owned_candidate_code_transaction_r543.py',A/'tools/owned_run_pointer_r717.py',A/'tools/bounded_build_job_r671.py',V/'launch_hazard_transaction_r1213.py',D/'flight.private.json']:pins[str(p)]=sha(p)
(H/'source-pins-r1212.json').write_bytes(enc({'files':pins,'oneExistingOwnRecordOnly':True,'noNewCreate':True,'oneUpload':True,'originalMetadataVerifyOnly':True,'originalBusinessArchiveUnchanged':True,'candidateServiceClassExplicitlyPinned':True}))
print(json.dumps({'preparedOnly':True,'noBusinessWriteOrServiceStart':True,'candidateClassPinned':True,'createMax':0,'resumesExactDiagnosticRecord':True,'releaseSHA256':plan['candidateReleaseSHA256']}))
