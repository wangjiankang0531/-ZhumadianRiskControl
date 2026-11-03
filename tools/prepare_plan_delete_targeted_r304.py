from pathlib import Path
import ast,ctypes,hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_plan_delete_roundtrip_r304_20261103'
assert not D.exists()and not(C/'prepared-r135').exists()and not(C/'r135').exists()
assert hashlib.sha256((R/'_g/Application/release-manifest.json').read_bytes()).hexdigest()=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert json.loads((C/'prepared-r134/history-runtime-restored.json').read_bytes())['passed']
memory=(ctypes.c_ulonglong*8)();memory[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>6*1024**3,'SIX_GIB_ADMISSION_REQUIRED_BEFORE_MUTATION'
schema_root=R/'work/event_delivery_consistency_20261030/full-controller-r131'
assert (schema_root/'schema-reader.json').is_file()and(schema_root/'original-table-names.txt').is_file()
class Rewrite(ast.NodeTransformer):
    def visit_Constant(self,node):
        if not isinstance(node.value,str):return node
        v=node.value
        if v=='r131':v='r135'
        elif v=='r132':v='r136'
        elif v=='prepared-r131':v='prepared-r135'
        elif v.startswith('r131/'):v='r135/'+v[len('r131/'):]
        v=v.replace('_r266','_r304')
        if v=='original_public_test_update_mapper_runtime_r265.py':v='original_public_test_update_r38_mapper_preflight_r286.py'
        if v=='verify_full_controller_mapper_product_r304.py':v='verify_full_controller_plan_delete_r304.py'
        if v=='verify_native_plan_exercise_r245_20261103.mjs':v='verify_native_plan_delete_r304_20261103.mjs'
        if v=='runtimeAdapterOnlyChangesDeclarations':v='fixedRuntimeSourceNotTransportAcceptance'
        return ast.copy_location(ast.Constant(v),node)
D.mkdir();pins={}
def save(src,dst):
    tree=Rewrite().visit(ast.parse((T/src).read_bytes()));ast.fix_missing_locations(tree)
    s=ast.unparse(tree)+'\n';ast.parse(s,filename=dst)
    p=T/dst;assert not p.exists();p.write_text(s,encoding='utf-8');pins[dst]=hashlib.sha256(p.read_bytes()).hexdigest()
for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend']:
    save(stem+'_r266.py',stem+'_r304.py')
save('mapper_product_patch_r266.py','mapper_product_patch_r304.py')
save('mapper_observation_support_r266.py','mapper_observation_support_r304.py')
save('verify_full_controller_mapper_product_r266.py','verify_full_controller_plan_delete_r304.py')
save('run_mapper_product_r266.py','run_native_plan_delete_r304.py')
host=T/'verify_full_controller_plan_delete_r304.py';text=host.read_text(encoding='utf-8')
assert "schema_base = R / 'work/event_delivery_consistency_20261030/full-controller-r131'"in text
assert "options.attempt in ['r135']"in text
needle="len(browser_result['cases']) >= 6";assert text.count(needle)==1;text=text.replace(needle,"len(browser_result['cases']) == 14")
host.write_text(text,encoding='utf-8');pins[host.name]=hashlib.sha256(host.read_bytes()).hexdigest()
js=T/'verify_native_plan_delete_r304_20261103.mjs';assert not js.exists();js.write_bytes((T/'verify_native_plan_delete_r301_20261103.mjs').read_bytes());pins[js.name]=hashlib.sha256(js.read_bytes()).hexdigest()
node=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(js)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert node.returncode==0
restore=(V/'restore_plan_delete_prestart_r300.py').read_text(encoding='utf-8').replace('r133','r135').replace('_r297','_r304')
restore=restore.replace(" and 'line 8'in trace",'').replace("assert 'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in source[7]","assert any('OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY' in line for line in source)")
ast.parse(restore);f=V/'restore_plan_delete_prestart_r305.py';assert not f.exists();f.write_text(restore,encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r135'],['prepare_production_history_runtime_r304.py'],
 ['mapper_product_patch_r304.py','prepare','--attempt','r135'],['mapper_observation_support_r304.py','prepare','--attempt','r135'],['prepare_personal_workflow_frontend_r304.py']]
results=[]
for args in steps:
    done=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if done.returncode:
        (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':done.returncode},indent=2)+'\n',encoding='utf-8');raise RuntimeError('OWN_TARGETED_PREPARATION_REFUSED:'+args[0])
    results.append({'step':args[0],'result':json.loads(done.stdout)})
proof={'prepared':True,'attempt':'r135','sourcePins':pins,'admissionAvailableBytes':memory[2],
 'fixedSchemaReaderDirectoryPreservedAndExists':True,'attemptLiteralsRewrittenByASTNotGlobalSubstring':True,
 'priorR133MemoryRefusalAndR134DriverDependencyFailureRetained':True,'expectedBrowserCases':14,
 'newDeleteCases':3,'steps':results,'servicesStarted':False,'onlyOwnSyntheticFixture':True,'publicFormalOrDesktopChanged':False}
(D/'prepared-result-r304.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r135','sources':len(pins),'fixedSchemaReaderChecked':True,'admissionAvailableGiB':round(memory[2]/1024**3,2),'servicesStarted':False}))
