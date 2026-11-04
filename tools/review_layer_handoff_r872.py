"""Receiver review: pin the handed-off source and run its HTTP tests locally only."""
from pathlib import Path
import ast, hashlib, importlib.util, io, json, sys, types, unittest
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent
A=Path('D:/Project/Zhumadian/Application')
O=V/'layer-handoff-receiver-r872'
PROFILE=A/'deploy/source_profiles/layer_sync_native_rpc_20261104.json'
TEST=A/'tools/tests/layer_sync'
def digest(raw): return hashlib.sha256(raw).hexdigest()
def main():
    assert not O.exists()
    handoff=A.parent/'Document/Deployment/layer_sync_handoff_20261104/handoff.json'
    raw=handoff.read_bytes(); h=json.loads(raw)
    assert h['publicUpdateOwner']=='驻马店3' and h['developmentOwner']=='驻马店三维'
    assert not h['publicRoundTripReady'] and not h['nativeCandidateBuiltOrRun']
    source=A/'tools/build_layer_sync_package.py'
    spec=importlib.util.spec_from_file_location('receiver_build_r872',source)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    profile=PROFILE.read_bytes(); pins=[]
    for row in json.loads(profile)['inputs']:
        b=(A/row['source']).read_bytes()
        assert len(b)==row['bytes'] and digest(b)==row['sha256']
        if row['target'].endswith('.py'): ast.parse(b)
        pins.append({'source':row['source'],'target':row['target'],'bytes':len(b),'sha256':digest(b)})
    tests={name:(TEST/name).read_bytes() for name in ['test_layer_sync_state_20261104.py','test_layer_sync_service_20261104.py']}
    O.mkdir(); package=O/'package'; manifest=m.build(A,PROFILE,package)
    assert manifest['sourceFiles']==len(pins)
    testdir=O/'tests'; testdir.mkdir()
    for name,data in tests.items(): (testdir/name).write_bytes(data)
    # Explicit namespace prevents importing another checkout's tools package.
    namespace=types.ModuleType('tools'); namespace.__path__=[str(package/'tools')]
    sys.modules['tools']=namespace
    sys.path[:0]=[str(package),str(testdir)]
    testmodule=importlib.import_module('test_layer_sync_service_20261104')
    assert Path(testmodule.__file__).resolve()==(testdir/'test_layer_sync_service_20261104.py').resolve()
    log=io.StringIO(); runner=unittest.TextTestRunner(stream=log,verbosity=2)
    result=runner.run(unittest.defaultTestLoader.loadTestsFromModule(testmodule))
    origins={}
    for name in ['services.layer_sync_server','services.layer_sync_transport','services.layer_sync_state','services.layers','services.data','tools.landscape_layer_validation']:
        origin=Path(sys.modules[name].__file__).resolve()
        assert origin.is_relative_to(package.resolve())
        rel=origin.relative_to(package.resolve()).as_posix()
        assert digest(origin.read_bytes())==manifest['inputs'][rel]['sha256']
        origins[name]=rel
    assert handoff.read_bytes()==raw and PROFILE.read_bytes()==profile
    for row in pins: assert digest((A/row['source']).read_bytes())==row['sha256']
    (O/'test-log.txt').write_text(log.getvalue(),encoding='utf8')
    proof={'schema':'xnby.layer-sync.receiver-review.v1','passed':result.wasSuccessful(),
      'handoffSHA256':digest(raw),'profileSHA256':digest(profile),'sourceFiles':len(pins),
      'sourceBytes':sum(r['bytes'] for r in pins),'inputs':pins,'runtimeOrigins':origins,
      'testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'scope':'Pinned original candidate HTTP handler/storage/client; synthetic local platform auth and local HTTP TLS factory substitute',
      'sourceAndProfileUnchanged':True,'desktopUsed':False,'publicReadOrWrite':False,'nativeBuiltOrRun':False,
      'realOriginalAuthenticationVerified':False,'realHTTPSVerified':False,'twoRealMachinesVerified':False,
      'readyForPublicDeployment':False,'recipient':'驻马店3'}
    (O/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in proof.items() if k not in ['inputs','runtimeOrigins']},ensure_ascii=False),flush=True)
    if not result.wasSuccessful(): raise SystemExit(1)
if __name__=='__main__': main()
