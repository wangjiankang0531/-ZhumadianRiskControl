"""Fresh original-UI attachment failure flight; preserve every previous business row.

One synthetic ordinary-user hazard, one PNG upload, one deliberately overlength
status submitted through the actual original form. No schema/fault trigger/API
substitute. A nonzero business response must preserve the old record AND links;
the diagnostic records whether that invariant actually holds across restart.
"""
from pathlib import Path
import ast,base64,copy,hashlib,json,secrets,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
OLD=V/'hazard_crud_r1202';H=V/'hazard_attachment_r1207';D=R/'Document/Deployment/hazard_attachment_original_r1207_20261106';OD=R/'Document/Deployment/hazard_crud_original_r1202_20261105'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def one(s,a,b):assert s.count(a)==1,a[:120];return s.replace(a,b)
assert not H.exists()and not D.exists()and not(R/'work/ha1207').exists()and not(R/'work/hazard-attachment-probe-r1207').exists()
assert j(OD/'stage-summary-r1205.json')['actualUICasePhasesIncludingRestartRepetition']==14
assert j(OD/'parent-terminal-r1203.json')['actualJobDescendantsZero']
assert sha(G/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
q="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',q],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0'
plan=copy.deepcopy(j(OD/'full-source-and-restore-plan.private.json'));plan.pop('preparedFlightJournalBefore',None)
nonce=secrets.token_hex(16);flight={'schema':'xnby.own-hazard-attachment-diagnostic-scope.v1','nonce':nonce,'sourceCode':'OWN_HA_'+nonce[:20],'sourceName':'Own attachment '+nonce,'actorUserId':f'a531{120002:028x}','createMax':1,'uploadMax':1,'failedEditMax':1,'deleteMax':0,'ordinaryEditRetryMax':0,'expectedOriginalStatus':'1','overlengthStatus':'12345','originalDDLStatusMaxCharacters':4,'existingRecordsNeverMutated':True,'taskReplayForbidden':True}
plan['newOwnHazardCRUDScope']=flight
D.mkdir();H.mkdir();(D/'flight.private.json').write_bytes(enc(flight));(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan));oldSHA=sha(OD/'full-source-and-restore-plan.private.json');newSHA=sha(D/'full-source-and-restore-plan.private.json')
png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jc1kAAAAASUVORK5CYII=')
assert png[:8]==b'\x89PNG\r\n\x1a\n' and len(png)<1024
(H/'own-attachment.png').write_bytes(png)
for src in OLD.iterdir():
 if src.name not in ['run_hazard_runtime_r1202.py','hazard_health_r1202.py','hazard_receiver_r1202.py','OwnHazardFormMetadataR1202.java','OwnHazardStatisticsMenuFixtureR1172.java']:continue
 name=src.name.replace('r1202','r1207').replace('R1202','R1207')
 text=src.read_text('utf8').replace('hazard_crud_original_r1202_20261105','hazard_attachment_original_r1207_20261106').replace('hazard-crud-probe-r1202','hazard-attachment-probe-r1207').replace('hc1202','ha1207').replace('r1202','r1207').replace('R1202','R1207').replace(oldSHA,newSHA)
 if name.startswith('run_hazard'):
  text=one(text,"plan['newOwnHazardCRUDScope']['createMax']==1","plan['newOwnHazardCRUDScope']['createMax']==1 and plan['newOwnHazardCRUDScope']['uploadMax']==1 and plan['newOwnHazardCRUDScope']['failedEditMax']==1")
  text=text.replace('hazard_crud_probe_r1207.py','hazard_attachment_probe_r1207.py')
 if src.suffix=='.py':ast.parse(text)
 (H/name).write_text(text,encoding='utf8')
# Read-only oracle excludes exactly this NEW actor-owned hazard; all old task,
# previous hazard and attachment rows are included in before/after digests.
text=(OLD/'OwnHazardCrudReadR1202.java').read_text('utf8').replace('R1202','R1207').replace('hazard-crud-probe-r1202','hazard-attachment-probe-r1207').replace('OWN_HZ_','OWN_HA_').replace('Own hazard ','Own attachment ')
text=one(text,'c.setReadOnly(true);c.setAutoCommit(false);', '''try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@sql_mode")){need(r.next()&&(r.getString(1).contains("STRICT_TRANS_TABLES")||r.getString(1).contains("STRICT_ALL_TABLES")),"ORIGINAL_STRICT_MODE_REQUIRED_NO_MODE_CHANGE");}
   c.setReadOnly(true);c.setAutoCommit(false);''')
text=one(text,'"1".equals(own.get("deleted"))&&"Own material v2".equals(own.get("material_type"))','"0".equals(own.get("deleted"))&&"Own material v1".equals(own.get("material_type"))')
text=one(text,'need(attachments==0,"NO_ATTACHMENT_BUSINESS_MUTATIONS_IN_THIS_FLIGHT");','need(attachments>=0&&attachments<=1,"BOUNDED_SINGLE_OWN_ATTACHMENT_COUNT");')
text=one(text,'result.setProperty("ownAttachmentsEmpty",Boolean.toString(attachments==0));','result.setProperty("ownAttachmentsEmpty",Boolean.toString(attachments==0));result.setProperty("ownAttachmentCount",Integer.toString(attachments));result.setProperty("ownAttachmentFingerprint",fingerprintOwnFiles(c,ownId));')
marker=' static void run(String[]a)throws Exception{'
method=''' static String fingerprintOwnFiles(Connection c,String ownId)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");if(ownId!=null)try(PreparedStatement p=c.prepareStatement("SELECT * FROM base_file WHERE correlation_id=? ORDER BY id")){p.setQueryTimeout(15);p.setString(1,ownId);try(ResultSet r=p.executeQuery()){int n=0;while(r.next()){need(++n<=1,"EXACT_SINGLE_OWN_LINK");for(int i=1;i<=r.getMetaData().getColumnCount();i++)part(d,r.getString(i));}}}return HexFormat.of().formatHex(d.digest());}
'''
text=one(text,marker,method+marker);(H/'OwnHazardCrudReadR1207.java').write_text(text,encoding='utf8')
# Preserve the actual CDP/browser helpers; replace the request oracle and flow.
browser=(OLD/'hazard_crud_browser_r1202.mjs').read_text('utf8').replace('hazard-crud-probe-r1202','hazard-attachment-probe-r1207')
a=browser.index("const ownCode=");b=browser.index('async function clickPoint',a)
browser=browser[:a]+(V/'hazard_attachment_observer_r1207.jsfrag').read_text('utf8')+'\n'+browser[b:]
a=browser.index(" await initializeFlight();");b=browser.index('}catch(e){',a)
browser=browser[:a]+(V/'hazard_attachment_main_r1207.jsfrag').read_text('utf8')+'\n'+browser[b:]
browser=browser.replace('businessWriteRequests:mutations.create+mutations.update+mutations.stale+mutations.delete','businessWriteRequests:mutations.create+mutations.failedEdit+mutations.upload')
(H/'hazard_attachment_browser_r1207.mjs').write_text(browser,encoding='utf8')
(H/'hazard_attachment_probe_r1207.py').write_bytes((V/'hazard_attachment_probe_r1207.py').read_bytes())
launch=(V/'launch_hazard_crud_r1203.py').read_text('utf8').replace('hazard_crud_original_r1202_20261105','hazard_attachment_original_r1207_20261106').replace('hazard_crud_r1202','hazard_attachment_r1207').replace('hazard-crud-probe-r1202','hazard-attachment-probe-r1207').replace('hc1202','ha1207').replace('r1202','r1207').replace('R1202','R1207').replace('r1203','r1208').replace('R1203','R1208')
ast.parse(launch);(V/'launch_hazard_attachment_r1208.py').write_text(launch,encoding='utf8')
pins={str(p):sha(p)for p in H.iterdir()if p.is_file()}
for p in [V/'original_public_test_update_r45_bootstrap_r847.py',A/'tools/owned_candidate_code_transaction_r543.py',A/'tools/owned_run_pointer_r717.py',A/'tools/bounded_build_job_r671.py',V/'launch_hazard_attachment_r1208.py',D/'flight.private.json']:pins[str(p)]=sha(p)
(H/'source-pins-r1207.json').write_bytes(enc({'files':pins,'oneNewOwnedHazardOnly':True,'oneTinyPNGUpload':True,'oneOriginalOverlengthStatusEdit':True,'noBusinessSQLWrites':True,'sameProductBytes':True,'existingElevenMetadataVerifyOnly':True,'diagnosisNotProductAcceptance':True}))
print(json.dumps({'preparedOnly':True,'servicesStarted':False,'oneNewOwnHazardAndPNGMax':1,'failedEditMax':1,'existingBusinessMutations':False,'productUnchanged':True}))
