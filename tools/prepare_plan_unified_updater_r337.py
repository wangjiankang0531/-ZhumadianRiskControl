from pathlib import Path
import ast,copy,hashlib,json,zipfile

R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
SOURCE=T/'original_public_test_update_r38_mapper_preflight_r286.py'
OUT=T/'original_public_test_update_r39_plan_runtime_r337.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert not D.exists()and not OUT.exists()
verified=J(R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103/verified-result-r334.json')
assert verified['passed']and verified['normalRoleActualCompiledBrowserCases']==18
module=J(R/'Document/Deployment/native_plan_runtime_candidate_r329_20261103/native-plan-runtime-module-r333.json')
assert module['classSHA256']=='384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'
text=SOURCE.read_text(encoding='utf-8');tree=ast.parse(text)
assert sha(SOURCE.read_bytes())=='f4eae55e6c2b35b4bee67d228bfc8904968ce49d86ea8265436e7e08b2e2964d'
assign={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
base36=ast.literal_eval(assign['R37_STATIC_BASE_METADATA'].value)
delivery=R/'Document/Deployment/public_test_static_performance_r37_20261103/delivery'
archives=list(delivery.glob('*.zip'));assert len(archives)==1
with zipfile.ZipFile(archives[0])as z:raw37=z.read('payload/release-manifest.json')
assert sha(raw37)=='909b64aa1315b8764b169c9874b8f52f903268b59c67adbf7b3799e85e29448c'
release37=json.loads(raw37);base37={k:v for k,v in release37.items()if k!='payloadManifestSHA256'}
assert base36!=base37
rel=module['runtimeRelativePath'];row={'bytes':module['classBytes'],'sha256':module['classSHA256']}
contract={'schema':'xnby.native-plan-atomic.v1','javaMajor':61,
 'originalJarPlanClassSHA256':module['originalJarPlanClassSHA256'],'candidateSourceSHA256':module['sourceSHA256'],
 'files':{rel:row},'schemaOrOriginalJarOrAuthenticationChanged':False}

helpers='''
def native_plan_runtime_declared(release, payload):
    rows=payload.get('files',{})
    if R39_PLAN_FIELD not in release:
        require(R39_PLAN_CLASS not in rows,'UNDECLARED_NATIVE_PLAN_RUNTIME_CLASS')
        return False
    require(release[R39_PLAN_FIELD]==R39_PLAN_CONTRACT,'EXACT_NATIVE_PLAN_RUNTIME_CONTRACT_REQUIRED')
    require(rows.get(R39_PLAN_CLASS)==R39_PLAN_ROW,'EXACT_NATIVE_PLAN_RUNTIME_CLASS_PIN_REQUIRED')
    jar=R38_MAPPER_CONTRACT['originalBusinessJar']
    require(rows.get(jar['path'])=={'bytes':jar['bytes'],'sha256':jar['sha256']},'NATIVE_PLAN_REQUIRES_ORIGINAL_BUSINESS_JAR')
    return True

def native_plan_runtime_ready(app,row):
    release=read(app/'release-manifest.json')
    payload=read(check_file(app,'payload-manifest.json',release['payloadManifestSHA256']))
    if not native_plan_runtime_declared(release,payload):return None
    pin=R39_PLAN_ROW
    check_file(app,R39_PLAN_CLASS,pin['sha256'],pin['bytes'])
    runtime=Path(row['run'])/'b'
    check_file(runtime,R39_PLAN_CLASS.split('/run-template/',1)[1],pin['sha256'],pin['bytes'])
    return {'candidatePlanClassSHA256':pin['sha256'],'installedAndRuntimeClassCopyMatched':True,
            'businessJDK':17,'actualBusinessFlowAcceptedByReadinessAlone':False}

'''
constants='\nR39_R37_BASE_METADATA='+repr(base37)+'\nR39_PLAN_FIELD="nativePlanAtomicCompatibility"\nR39_PLAN_CLASS='+repr(rel)+'\nR39_PLAN_ROW='+repr(row)+'\nR39_PLAN_CONTRACT='+repr(contract)+'\n'
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='r38_unified_bundle_contract')
original=ast.get_source_segment(text,node);replacement=original
def one(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b,1)
replacement=one(replacement,"==R37_STATIC_BASE_METADATA, 'R38_EXACT_R36_BASE_METADATA_REQUIRED'", "in (R37_STATIC_BASE_METADATA,R39_R37_BASE_METADATA), 'R39_EXACT_R36_OR_R37_BASE_METADATA_REQUIRED'")
replacement=one(replacement,"    expected_files={n:p for n,p in previous['files'].items()if n not in oldfront};expected_files.update(R38_FRONTEND_ROWS)",
 "    require(R39_PLAN_CLASS not in previous['files'],'R39_REQUIRES_NO_PREEXISTING_PLAN_OVERRIDE')\n    expected_files={n:p for n,p in previous['files'].items()if n not in oldfront};expected_files.update(R38_FRONTEND_ROWS);expected_files[R39_PLAN_CLASS]=R39_PLAN_ROW")
replacement=one(replacement,"    expected[R38_FRONTEND_FIELD]=R38_FRONTEND_CONTRACT;expected[R37_STATIC_FIELD]=R37_STATIC_CONTRACT",
 "    expected[R38_FRONTEND_FIELD]=R38_FRONTEND_CONTRACT;expected[R37_STATIC_FIELD]=R37_STATIC_CONTRACT;expected[R39_PLAN_FIELD]=R39_PLAN_CONTRACT")
replacement=one(replacement,"    require(workflow_declared(release,payload)and runtime_pool_declared(release),'R38_RETAINED_WORKFLOW_AND_POOL_REQUIRED')",
 "    require(workflow_declared(release,payload)and runtime_pool_declared(release),'R38_RETAINED_WORKFLOW_AND_POOL_REQUIRED')\n    require(native_plan_runtime_declared(release,payload),'R39_EXPLICIT_NATIVE_PLAN_RUNTIME_REQUIRED')")
replacement=one(replacement,"    required=set(changed)|set(source_pins)|{'release-manifest.json','payload-manifest.json'}",
 "    required=set(changed)|set(source_pins)|{'release-manifest.json','payload-manifest.json',R39_PLAN_CLASS}")
replacement=one(replacement,"    for n,pin in {**changed,**source_pins}.items():", "    for n,pin in {**changed,**source_pins,R39_PLAN_CLASS:R39_PLAN_ROW}.items():")
text=one(text,original,constants+helpers+replacement)
revision=ast.get_source_segment(SOURCE.read_text(encoding='utf-8'),assign['R38_REVISION'])
text=one(text,revision,'R38_REVISION="20261103-R39-plan-runtime-mappers-frontend-performance"')
anchor="            'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class',"
text=one(text,anchor,"            "+repr(rel)+",\n\n"+anchor)
current_tree=ast.parse(text)
health=next(n for n in current_tree.body if isinstance(n,ast.FunctionDef)and n.name=='health')
segment=ast.get_source_segment(text,health)
text=one(text,segment,segment+'\n\n    native_plan_runtime_ready(app,row)')
parsed=ast.parse(text)
before={n.name:ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,ast.FunctionDef)}
after={n.name:ast.dump(n,include_attributes=False)for n in parsed.body if isinstance(n,ast.FunctionDef)}
changed=sorted(k for k in before if before[k]!=after[k])
assert changed==['health','load_bundle','r38_unified_bundle_contract']
retained=['normal_stop','launch','backup_code','replace_code','restore_code','apply_update','rollback_latest','candidate_runtime_pool_preflight']
assert all(before[n]==after[n]for n in retained)
OUT.write_text(text,encoding='utf-8');D.mkdir()
report={'prepared':True,'sourceSHA256':sha(OUT.read_bytes()),'sourceBytes':OUT.stat().st_size,
 'sourceParentSHA256':sha(SOURCE.read_bytes()),'changedExistingFunctions':changed,
 'newFunctions':['native_plan_runtime_declared','native_plan_runtime_ready'],
 'normalLifecycleAndBackupReplaceRestoreAndBudgetFunctionsASTRetained':retained,
 'eachBundleStillAcceptsExactlyOneInstalledBase':True,
 'supportedMetadataBases':['exact-R36','exact-R37'],'publicBaseReleaseSHA256':{
  'R36':'daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853',
  'R37':sha(raw37)},'candidatePlanClassSHA256':module['classSHA256'],
 'candidatePlanContract':contract,'programCompositionFaultAndLifecycleValidationPending':True,
 'publicOrFormalOrDesktopChanged':False,'fullCloneReady':False}
(D/'updater-preparation-r337.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items()if k not in ['candidatePlanContract','normalLifecycleAndBackupReplaceRestoreAndBudgetFunctionsASTRetained']}))
