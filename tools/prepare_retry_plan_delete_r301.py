from pathlib import Path
import ast,ctypes,hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';V=Path(__file__).resolve().parent
OLD=R/'Document/Deployment/native_plan_delete_roundtrip_r297_20261103';D=R/'Document/Deployment/native_plan_delete_roundtrip_r301_20261103'
assert not D.exists()and not(C/'prepared-r134').exists()and not(C/'r134').exists()
assert json.loads((OLD/'prestart-refusal-and-restore-r300.json').read_bytes())['passed']
assert hashlib.sha256((R/'_g/Application/release-manifest.json').read_bytes()).hexdigest()=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
memory=(ctypes.c_ulonglong*8)();memory[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
assert memory[2]>6*1024**3,'ADMISSION_REQUIRES_SIX_GIB_BEFORE_ANY_FIXTURE_MUTATION'
old=json.loads((OLD/'preparation-r297.json').read_bytes());pins={};D.mkdir()
for name,pin in old['sourcePins'].items():
    src=T/name;assert hashlib.sha256(src.read_bytes()).hexdigest()==pin
    dst=T/name.replace('_r297','_r301');assert not dst.exists()
    text=src.read_text(encoding='utf-8').replace('r134','r135').replace('r133','r134').replace('_r297','_r301')
    if name.endswith('.py'):ast.parse(text,filename=dst.name)
    dst.write_text(text,encoding='utf-8',newline='\n');pins[dst.name]=hashlib.sha256(dst.read_bytes()).hexdigest()
syntax=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(T/'verify_native_plan_delete_r301_20261103.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert syntax.returncode==0
restore=(V/'restore_plan_delete_prestart_r300.py').read_text(encoding='utf-8').replace('r133','r134').replace('_r297','_r301')
ast.parse(restore);r=V/'restore_plan_delete_prestart_r302.py';assert not r.exists();r.write_text(restore,encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r134'],['prepare_production_history_runtime_r301.py'],
 ['mapper_product_patch_r301.py','prepare','--attempt','r134'],['mapper_observation_support_r301.py','prepare','--attempt','r134'],['prepare_personal_workflow_frontend_r301.py']]
results=[]
for args in steps:
    completed=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if completed.returncode:
        (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':completed.returncode},indent=2)+'\n',encoding='utf-8');raise RuntimeError('OWN_RETRY_PREPARATION_REFUSED:'+args[0])
    results.append({'step':args[0],'result':json.loads(completed.stdout)})
proof={'prepared':True,'attempt':'r134','priorR133PreallocationMemoryRefusalRetained':True,
 'admissionAvailableBytes':memory[2],'admissionMinimumGiB':6,'runtimeMinimumGiBStill':4,
 'sourcePins':pins,'steps':results,'expectedBrowserCases':14,'newDeleteCases':3,
 'onlyOwnSyntheticFixture':True,'servicesStarted':False,'publicFormalOrDesktopChanged':False}
(D/'prepared-result-r301.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r134','admissionAvailableGiB':round(memory[2]/1024**3,2),'sources':len(pins),'expectedBrowserCases':14,'servicesStarted':False}))
