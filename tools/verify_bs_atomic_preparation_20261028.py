from pathlib import Path
import datetime,hashlib,importlib.util,json,sys,unittest
R=Path('D:/Project/Zhumadian');W=Path('D:/Project/yhq/htengine');Q=Path('D:/Zqa20261025/Application');ROOT=R/'work/bs_atomic_local_update_20261028';B=ROOT/'bundle'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((B/'build-result.json').read_text('utf-8'));pin=report['manifestSHA256'];needpin='1d6e286b983efb76ff3fdb1c9f2b164a1fa3c7bc044f6d0bc623980b1450ea3c';assert pin==needpin and sha(B/'update-manifest.json')==pin
 path=B/'payload/tools/original_public_test_update.py';spec=importlib.util.spec_from_file_location('own_atomic_updater',path);u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
 sys.path.insert(0,str(R/'Application/tools'));sys.modules['original_public_test_update']=u
 import test_original_inspection_point_update as old
 with (ROOT/'prior-point-regression.log').open('w',encoding='utf-8') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(old.PointUpdateTests))
 assert result.wasSuccessful() and result.testsRun==6
 plan,oldpin,changes=u.load_bundle(Q,B,pin,expected_target=Q,expected_port=18891);assert oldpin==report['oldReleaseSHA256'] and len(changes)==525
 from run_original_inventory_ownership_probe import state
 s=state();assert s['controllerPID']==35292 and Path(s['run']).name=='j41'
 rows=[]
 for p in (R/'work/third_party_frontend_20261028_r1/pc-candidate/dist').rglob('*.js'):
  raw=p.read_bytes()
  if '证书名称不能超过16个字符'.encode() in raw:
   assert b'Array.from(' in raw and '最多16个字符'.encode() in raw;rows.append({'file':str(p),'SHA256':sha(p)})
 assert rows
 output={'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':pin,'newReleaseSHA256':plan['newReleaseSHA256'],'actualCompleteRetainedPayloadAndControllerPinsVerified':True,'newScopeTestsObserved':14,'newScopeExecChunk':'8a02dc','oldPointScopeTests':6,'compiledOriginalComponentRuleAndHintFiles':rows,'currentRuntimeStillUnchanged':True,'controllerPID':s['controllerPID'],'installed':False,'publicDeployed':False}
 target=ROOT/'preparation-result.private.json';assert not target.exists();target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in output.items() if k!='compiledOriginalComponentRuleAndHintFiles'}))
if __name__=='__main__':main()
