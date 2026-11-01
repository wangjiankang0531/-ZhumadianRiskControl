"""Verify the recorded installed plan/report stage, with original auth and preserved scene."""
from pathlib import Path
import hashlib,importlib.util,json,sys,urllib.request
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/emergency_plan_report_20261030';sys.path.insert(0,str(T));sys.dont_write_bytecode=True
from run_original_inventory_ownership_probe import state
from verify_confirmed_operation_preservation import protected
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def current():
 spec=read(D/'current-local-candidate.json');bundle=Path(spec['bundle']);life=Path(spec['lifecycle']);assert bundle.resolve().is_relative_to((R/'work/emergency_plan_report_20261030').resolve()) and life.resolve().is_relative_to((R/'work/emergency_plan_report_20261030').resolve());result=read(life/'result.json');prepared=read(life/'prepared.private.json');build=read(bundle/'build-result.json');assert result['runtimeReady'] and result['legacyProjectionUnchanged'] and spec['releaseSHA256']==result['releaseSHA256']==build['newReleaseSHA256']==sha(Q/'release-manifest.json') and sha(bundle/'update-manifest.json')==build['manifestSHA256'];row=state();assert row['controllerPID']==result['controllerPID'] and row['run']==result['run'];release=read(Q/'release-manifest.json')
 for name,pin in release['controllerFiles'].items():assert sha(Q/name)==pin
 path=bundle/'payload/tools/original_public_test_update.py';assert sha(path)==release['controllerFiles']['tools/original_public_test_update.py'];s=importlib.util.spec_from_file_location('own_active_plan_report_updater',path);u=importlib.util.module_from_spec(s);s.loader.exec_module(u);u.health(Q,row,gateway_port=18891);observation=u.plan_report_observer_ready(Q,row);schema=u.event_report_schema_ready(Q,row);assert observation['allPlanReportMethodsAndManagerMatched']
 for name,pin in prepared['dataIdentityPins'].items():assert sha(name)==pin
 assert protected()==prepared['protected'];opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 with opener.open('http://127.0.0.1:8767/api/runtime/status',timeout=5) as response:scene=json.load(response)
 assert scene['pid']==6780 and scene['identity']=='f6a5758586635b70025773c3e40083e0c51c7bc01cc02db74cf491233dd7293a' and scene['readOnly'] and not scene['conversionEnabled']
 return {'currentBS':Path(row['run']).name,'controllerPID':row['controllerPID'],'releaseSHA256':spec['releaseSHA256'],'databaseUUID':row['databaseUUID'],'allRetainedAndPlanReportReadinessMatched':True,'currentScenePID':6780,'legacyDataAndDataIdentityPreservedAtActualStart':True,'actualAuthenticatedBusinessOrRoleAcceptance':False,'fullCloneReady':False}
if __name__=='__main__':
 v=current();print(json.dumps({k:x for k,x in v.items() if k!='databaseUUID'}))
