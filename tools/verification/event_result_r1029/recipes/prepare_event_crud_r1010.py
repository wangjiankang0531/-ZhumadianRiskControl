from pathlib import Path
import ast, copy, hashlib, importlib.util, json, socket, subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
H=V/'event_crud_r1010';D=R/'Document/Deployment/event_crud_native_r1010_20261105'
OLD=V/'ledger_native_r960';SOURCE=R/'Document/Deployment/event_result_owned_full_r1003_20261105'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def pin(p):return {'bytes':Path(p).stat().st_size,'sha256':sha(p)} if Path(p).is_file() else None
assert not H.exists() and not D.exists() and not (R/'work/ev1010').exists()
assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
assert not (G.parent/'user-manual-protected.json').exists()
assert sha(SOURCE/'full-source-and-restore-plan.private.json')=='c64406c0ff32e56f8c44e97ff79585d41e044e7617ad73d711df09c3096f71e7'
assert J(R/'work/ledgerfull-r960/verified-ledger-ui-r960.json')['passed']
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0','OWN_G_REFERENCE_CHECK_REQUIRED_NOT_ACCESS_DENIED_ZERO'
with socket.socket() as s:s.bind(('127.0.0.1',0));receiver=s.getsockname()[1]
assert receiver not in [8767,18891,18892]
H.mkdir();D.mkdir();(D/'candidate').mkdir()
plan=copy.deepcopy(J(SOURCE/'full-source-and-restore-plan.private.json'))
assert pin(G/'private/server-configuration.json')==plan['configBefore']
cfg=J(G/'private/server-configuration.json');keys=['riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird']
cfg2=copy.deepcopy(cfg)
for key in keys:
    assert key+'Url' in cfg2['configuration']['business']
    assert not any(key+'Url' in v for v in cfg2.get('businessArguments',[]))
    cfg2['configuration']['business'][key+'Url']='http://127.0.0.1:'+str(receiver)+'/own-event-crud-r1010/'+key
original=copy.deepcopy(cfg2)
for key in keys:original['configuration']['business'][key+'Url']=cfg['configuration']['business'][key+'Url']
assert original==cfg
rawcfg=enc(cfg2);cfg=None;cfg2=None;original=None
(D/'candidate/configuration.private.json').write_bytes(rawcfg)
payload=J(SOURCE/'candidate/payload-manifest.json');payload['files']['private/server-configuration.json']=pin(D/'candidate/configuration.private.json')
(D/'candidate/payload-manifest.json').write_bytes(enc(payload))
release=J(SOURCE/'candidate/release-manifest.json');release['payloadManifestSHA256']=sha(D/'candidate/payload-manifest.json')
(D/'candidate/release-manifest.json').write_bytes(enc(release))
plan['candidateReleaseSHA256']=sha(D/'candidate/release-manifest.json')
plan['candidatePayloadManifestSHA256']=release['payloadManifestSHA256']
plan['configAfter']=pin(D/'candidate/configuration.private.json')
plan['receiverPort']=receiver
plan['onlySixOwnedDockReceiverURLsAndPrivateManifestPinsAdapted']=True
plan['codeCandidateReleaseSHA256']=J(SOURCE/'full-source-and-restore-plan.private.json')['candidateReleaseSHA256']
# Outer code transaction stays the exact existing R47 set. The separate configuration
# transaction adapts/restores its private field and manifests after code apply/before restore.
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))

source=A/'tools/owned_task_configuration_r637.py'
# Derivative configuration algorithm fixed by the new source manifest.
text=source.read_text('utf8')
start=text.index('def task_candidate(before):');end=text.index('\nclass OwnedTaskConfigurationTransaction:',start)
function='''def event_candidate(before,receiver_port):
    need(type(receiver_port)is int and 1024<receiver_port<65536 and receiver_port not in {8767,18891,18892},'EXACT_OWN_RECEIVER_PORT_REQUIRED')
    need(isinstance(before,dict)and set(before)==set(NAMES)and all(isinstance(v,bytes)for v in before.values()),'EXACT_EVENT_THREE_BYTES_REQUIRED')
    spec,payload,release=(json.loads(before[n])for n in NAMES)
    need(spec.get('schema')=='zhumadian.original.server.configuration.v1'and payload.get('schema')=='zhumadian.original.server.payload.v1'and release.get('schema')=='zhumadian.original.server.release.v1','ORIGINAL_EVENT_SCHEMAS_REQUIRED')
    need(payload['files'].get(CONFIG)==raw_pin(before[CONFIG])and release['payloadManifestSHA256']==raw_pin(before[PAYLOAD])['sha256']and payload['releaseId']==release['releaseId'],'EXACT_EVENT_MANIFEST_IDENTITY_REQUIRED')
    changed=json.loads(before[CONFIG]);keys=('riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird')
    need(isinstance(changed.get('configuration',{}).get('business'),dict),'BUSINESS_CONFIGURATION_REQUIRED')
    for key in keys:
        need(key+'Url'in changed['configuration']['business']and not any(key+'Url'in arg for arg in changed.get('businessArguments',[])),'NO_RECEIVER_OVERRIDE_OR_MISSING_BINDING')
        changed['configuration']['business'][key+'Url']='http://127.0.0.1:'+str(receiver_port)+'/own-event-crud-r1010/'+key
    reversed_spec=json.loads(encode(changed))
    for key in keys:reversed_spec['configuration']['business'][key+'Url']=spec['configuration']['business'][key+'Url']
    need(reversed_spec==spec,'NO_OTHER_CONFIGURATION_CHANGE_ALLOWED')
    result={CONFIG:encode(changed)};p=json.loads(before[PAYLOAD]);r=json.loads(before[RELEASE])
    p['files'][CONFIG]=raw_pin(result[CONFIG]);result[PAYLOAD]=encode(p)
    r['payloadManifestSHA256']=raw_pin(result[PAYLOAD])['sha256'];result[RELEASE]=encode(r)
    p['files'][CONFIG]=payload['files'][CONFIG];r['payloadManifestSHA256']=release['payloadManifestSHA256']
    need(p==payload and r==release,'NO_OTHER_MANIFEST_CHANGE_ALLOWED')
    need(all(raw_pin(result[n])!=raw_pin(before[n])for n in NAMES),'ALL_EVENT_FILES_MUST_CHANGE')
    return result
'''
text=text[:start]+function+text[end:]
text=text.replace('from original_manager_runtime_spec_r633 import original_task_spec\n','')
text=text.replace('OwnedTaskConfigurationTransaction','OwnedEventReceiverConfigurationTransaction').replace('xnby.owned-task-configuration-transaction.v1','xnby.owned-event-receiver-configuration-transaction.v1')
text=text.replace('expected_before,*,processes_exited):','expected_before,*,receiver_port,processes_exited):')
text=text.replace('self.before=json.loads(json.dumps(expected_before))','self.receiver_port=receiver_port\n        self.before=json.loads(json.dumps(expected_before))')
text=text.replace("'before':self.before})).hexdigest()","'before':self.before,'receiverPort':self.receiver_port})).hexdigest()")
text=text.replace('task_candidate(self.backup_bytes())','event_candidate(self.backup_bytes(),self.receiver_port)').replace('task_candidate(raw)','event_candidate(raw,self.receiver_port)')
assert 'task_candidate(' not in text and text.count('event_candidate(')==3
ast.parse(text);(H/'owned_event_receiver_configuration_r1010.py').write_text(text,encoding='utf8')
# Derive the known lifecycle guard/normal stop/receipt path; never modify that original.
runner=(OLD/'run_ledger_lifecycle_r960.py').read_text('utf8')
runner=runner.replace('unified_home_supervision_exact_r930_20261104','event_crud_native_r1010_20261105').replace('work/ledgerfull-r960','work/ev1010')
runner=runner.replace("assert W.is_dir()and P.is_dir()and (P/'own-ledger-ui.marker').read_bytes()==b'own-ledger-ui-r941\\n'and not(P/'resume-r960').exists()and not Z.exists(),'EXACT_EXISTING_METADATA_NEW_RESUME_REQUIRED'", "assert W.is_dir() and not Z.exists(),'NEW_EVENT_CRUD_ATTEMPT_REQUIRED'")
runner=runner.replace("(P/'resume-r960').mkdir()","# No ledger fixture or metadata writes in this attempt.")
runner=runner.replace("fixture_nonce=hashlib.sha256(str(P).encode('utf8')).hexdigest()[:32]","fixture_nonce=secrets.token_hex(16)")
runner=runner.replace('ledger-source-pins-r960.json','event-source-pins-r1010.json').replace('home_transfer_probe_r906.py','event_crud_probe_r1010.py')
runner=runner.replace('a44203be5562ea30a565752e9b4ec2081b2f5b9d577f7455bc7497a348a9fc7d',sha(D/'full-source-and-restore-plan.private.json'))
runner=runner.replace('proof=','proof=',1)
runner=runner.replace("expectedConfig=plan['configBefore'];taskRestored=True", "event_config=load('own_event_config_r1010',V/'owned_event_receiver_configuration_r1010.py')\nconfigBefore={event_config.CONFIG:plan['configBefore'],event_config.PAYLOAD:plan['mutations'][event_config.PAYLOAD]['after'],event_config.RELEASE:plan['mutations'][event_config.RELEASE]['after']}\nconfigTx=event_config.OwnedEventReceiverConfigurationTransaction(G,Z/'event-config',configBefore,receiver_port=plan['receiverPort'],processes_exited=exited)\nexpectedConfig=plan['configBefore'];taskRestored=False")
runner=runner.replace("tx.apply();configuration_invariant()", "tx.apply();configuration_invariant();configTx.prepare();configTx.apply();expectedConfig=plan['configAfter'];configuration_invariant()")
before=" assert code.pin(G/'private/server-configuration.json')==plan['configBefore'];taskRestored=True"
after=" if configTx.journal.exists():\n  configState=configTx.state()\n  if configState['phase'] in {'prepared','applying','applied','restoring'}:configTx.restore();taskRestored=True\n  elif configState['phase']=='restored':taskRestored=True\n  elif configState['phase']=='backup-in-progress':assert configTx.current()==configBefore;taskRestored=True\n else:assert code.pin(G/'private/server-configuration.json')==plan['configBefore'];taskRestored=True"
assert before in runner;runner=runner.replace(before,after)
# Start the owned receiver only after --run, resource/CIM/source guards and path checks.
receiver_code='''from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import threading
receiverEvents=[]
class OwnReceiver(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  size=int(self.headers.get('Content-Length','0'))
  if self.client_address[0]!='127.0.0.1' or not self.path.startswith('/own-event-crud-r1010/') or not 0<size<=65536:self.send_error(400);return
  raw=self.rfile.read(size)
  try:json.loads(raw)
  except ValueError:self.send_error(400);return
  receiverEvents.append({'syntheticJSONReceived':True,'bodyBytes':size});body=b'{"code":0,"data":true}'
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
receiverServer=ThreadingHTTPServer(('127.0.0.1',plan['receiverPort']),OwnReceiver)
receiverThread=threading.Thread(target=receiverServer.serve_forever,daemon=True);receiverThread.start()
'''
runner=runner.replace("try:\n phase='backup-original-code'",receiver_code+"\ntry:\n phase='backup-original-code'")
runner=runner.replace(" invariant();assert exited(),'LIVE_OR_FOREIGN_G_REFERENCE_NO_CODE_RESTORE'", " receiverServer.shutdown();receiverServer.server_close();receiverThread.join(timeout=10);assert not receiverThread.is_alive()\n invariant();assert exited(),'LIVE_OR_FOREIGN_G_REFERENCE_NO_CODE_RESTORE'")
runner=runner.replace('verified-ledger-ui-r960.json','verified-event-crud-r1010.json').replace('ledger-ui-full-result-r960.json','event-crud-full-result-r1010.json')
runner=runner.replace("'actualOriginalLedgerUIAndNormalRestart'","'actualOriginalEventCRUDAndNormalRestart'").replace("'normalOriginalLedgerPreviewDownloadAndRestartAccepted'","'normalOriginalEventCRUDAndRestartAccepted'")
runner=runner.replace("'privateConfigurationUnchanged':taskRestored", "'privateConfigurationRestored':taskRestored,'onlySixOwnReceiverURLsChanged':True,'actualLoopbackDeliveryReceipts':len(receiverEvents),'realExternalDeliveryAccepted':False")
runner=runner.replace("query=\"(Get-CimInstance", "query=\"$ErrorActionPreference='Stop'; (Get-CimInstance")
ast.parse(runner);(H/'run_event_crud_r1010.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('unified_home_supervision_exact_r930_20261104','event_crud_native_r1010_20261105').replace('ledger-source-pins-r960.json','event-source-pins-r1010.json').replace("==plan['configBefore']","==plan['configAfter']").replace("'privateApplicationSettingsChanged':False","'onlySixOwnLoopbackNotificationSettingsChanged':True")
ast.parse(health);(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
(H/'preparation.json').write_bytes(enc({'sourceR930PlanSHA256':sha(SOURCE/'full-source-and-restore-plan.private.json'),'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'receiverPort':receiver,'onlyOwnGPreparedNoServicesStarted':True,'browserAndConfigFaultTestsStillPending':True}))
print(json.dumps({'prepared':True,'noGCodeConfigOrBusinessWritten':True,'noServicesStarted':True,'runtimeRunNotYetAccepted':True}))
