from pathlib import Path
import ast,hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_delete_roundtrip_r297_20261103'
assert not(C/'r133').exists()and(C/'prepared-r133/frontend-scope.json').exists()
p=D/'preparation-r297.json';proof=json.loads(p.read_bytes())
for name,pin in proof['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
browser=T/'verify_native_plan_delete_r297_20261103.mjs';s=browser.read_text(encoding='utf-8')
old="responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_DELETE_FALSE_INJECTION'}))"
new="responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Cache-Control',value:'no-store'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_DELETE_FALSE_INJECTION'}))"
assert s.count(old)==1;s=s.replace(old,new);browser.write_text(s,encoding='utf-8',newline='\n')
proof['sourcePins'][browser.name]=hashlib.sha256(browser.read_bytes()).hexdigest();proof['syntheticGETFailureResponseNoStore']=True
p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
for name in proof['sourcePins']:
    if name.endswith('.py'):ast.parse((T/name).read_bytes(),filename=name)
syntax=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(browser)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert syntax.returncode==0
assert hashlib.sha256((T/'original_public_test_update_r38_mapper_preflight_r286.py').read_bytes()).hexdigest()=='f4eae55e6c2b35b4bee67d228bfc8904968ce49d86ea8265436e7e08b2e2964d'
print('OWN_NATIVE_NORMAL_ROLE_DELETE_ROUNDTRIP_R133_STARTING',flush=True)
result=subprocess.call([sys.executable,str(T/'run_native_plan_delete_r297.py')],creationflags=subprocess.CREATE_NO_WINDOW)
print(json.dumps({'ownedRunnerExitCode':result,'attempt':'r133','publicOrFormalOrDesktopChanged':False}),flush=True)
assert result==0,'OWN_NATIVE_PLAN_DELETE_FAILED_EVIDENCE_KEPT'
