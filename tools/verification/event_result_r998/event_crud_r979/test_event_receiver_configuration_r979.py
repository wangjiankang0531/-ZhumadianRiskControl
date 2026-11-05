from pathlib import Path
import copy,hashlib,importlib.util,json,sys
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';sys.path.insert(0,str(A/'tools'))
s=importlib.util.spec_from_file_location('eventcfg_r979',V/'owned_event_receiver_configuration_r979.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
keys=('riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird')
cfg={'schema':'zhumadian.original.server.configuration.v1','configuration':{'business':{k+'Url':'http://127.0.0.1:12345/old'for k in keys}},'businessArguments':[],'unrelated':'keep'}
payload={'schema':'zhumadian.original.server.payload.v1','releaseId':'own-event-test','files':{m.CONFIG:m.raw_pin(m.encode(cfg))}}
release={'schema':'zhumadian.original.server.release.v1','releaseId':'own-event-test','payloadManifestSHA256':m.raw_pin(m.encode(payload))['sha256']}
before={m.CONFIG:m.encode(cfg),m.PAYLOAD:m.encode(payload),m.RELEASE:m.encode(release)}
result=m.event_candidate(before,12346);parsed=json.loads(result[m.CONFIG]);check=copy.deepcopy(parsed)
for k in keys:
 assert parsed['configuration']['business'][k+'Url']=='http://127.0.0.1:12346/own-event-crud-r979/'+k
 check['configuration']['business'][k+'Url']=cfg['configuration']['business'][k+'Url']
assert check==cfg
tests=[{'case':'only-six-loopback-URL-values-change-and-manifests-match','passed':True}]
for port in [True,0,80,8767,18891,65536,'12346']:
 try:m.event_candidate(before,port)
 except ValueError:tests.append({'case':'invalid-port-'+str(port),'passed':True})
 else:raise AssertionError('BAD_PORT_ACCEPTED')
bad=dict(before);bad[m.CONFIG]=before[m.CONFIG]+b' '
try:m.event_candidate(bad,12346)
except ValueError:tests.append({'case':'config-payload-pin-drift-refused','passed':True})
else:raise AssertionError('DRIFT_ACCEPTED')
root=R/'work/ecfg979';assert not root.exists();root.mkdir()
for fault in [0,1,2,3]:
 base=root/('case-'+str(fault));app=base/'Application';app.mkdir(parents=True);(app/'private').mkdir()
 for n,raw in before.items():(app/n).write_bytes(raw)
 tx=m.OwnedEventReceiverConfigurationTransaction(app,base/'transaction',{n:m.raw_pin(raw)for n,raw in before.items()},receiver_port=12346,processes_exited=lambda:True)
 tx.prepare()
 def fail(index,name):
  if fault==index:raise RuntimeError('OWN_INJECTED_WRITE_FAILURE')
 try:tx.apply(after_write=fail)
 except RuntimeError:assert fault>0
 else:assert fault==0
 tx.restore();assert all((app/n).read_bytes()==raw for n,raw in before.items())
 tests.append({'case':'actual-file-normal-or-write-'+str(fault)+'-fault-restores-three-exact-preimages','passed':True,'exitProofCallbackIsSynthetic':True})
out={'passed':True,'checks':tests,'actualOriginalGOrServicesTouched':False,'processExitCallbacksAreExplicitTestDoubles':True}
(V/'configuration-tests-r979.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'checks':len(tests)}))
