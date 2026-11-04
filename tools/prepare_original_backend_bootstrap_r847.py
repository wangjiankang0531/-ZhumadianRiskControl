"""Compose full tested frontend over exact R44 original backend; no service or public mutation."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/original_backend_bootstrap_r45_20261104'
O=R/'work/original-backend-bootstrap-r847'
BUILD=R/'work/canonical-bootstrap-compatible-r841'
P44=R/'work/mapper-chart-bundles-r571'
J=lambda p:json.loads(p.read_bytes())
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def main():
 assert not D.exists()and not O.exists()
 assert sha(R/'Document/Deployment/public_test_mapper_chart_r44_20261104/delivery-manifest.json')=='9a9db792a32e46437763c111badecebb6e4a6a1efe047cae98b05c26f370e9bf'
 proof=J(BUILD/'verified-bounded-full-build-r673.json')
 assert proof['passed']and proof['sourceRestored']and proof['terminal']['nodeExitCode']==0 and proof['terminal']['actualJobDescendantsZeroBeforeClose']
 assert J(R/'Document/Deployment/grouped_component_bootstrap_r846_20261104/verified-component-bootstrap-r846.json')['passed']
 files=proof['files'];assert len(files)==344
 for n,pin in files.items():assert (BUILD/'dist'/n).stat().st_size==pin['bytes']and sha(BUILD/'dist'/n)==pin['sha256']
 oldInputs=J(R/'work/user_feedback_20261031/event-research-level-r418/build/actual-compiled-source-files.json')
 inputs=J(BUILD/'actual-compiled-source-files.json')
 delta={n:inputs[n]for n in set(inputs)|set(oldInputs)if inputs.get(n)!=oldInputs.get(n)}
 assert set(delta)=={'src/global-import.ts','src/router/index.ts','src/OriginalAuthenticatedInstallerR817.ts',
  'src/components/workflow/info.vue','src/components/workflow/components/businessForm.vue',
  'src/components/workflow/components/OriginalWorkflowOnlineFormModelR470.ts','src/components/workflow/components/OriginalWorkflowOnlineFormR470.vue'}
 baseSource=A/'tools/original_public_test_update_r44_mapper_chart_r570.py'
 assert sha(baseSource)=='cbca17bbb2e98dfda77aed44719641447ef68b8ef18f85a6426d9d120f7d593e'
 runtime=load('original_backend_base_r847',baseSource)
 rows={'frontend/emergency_pc/'+n:pin for n,pin in files.items()}
 contract=copy.deepcopy(runtime.R38_FRONTEND_CONTRACT)
 contract.update(revision='retained-features-original-online-forms-and-authenticated-bootstrap-v4',
  changedCompiledSourcePaths=30,compiledSourceInventoryComparisonOrigin='retained-emergency-workflow-source-r17',
  actualCompiledSourceInventorySHA256=sha(BUILD/'actual-compiled-source-files.json'))
 contract['frontends']['emergency_pc']=runtime.r32_frontend_manifest(rows,'emergency_pc')
 feature={'revision':'original-sdk-online-forms-and-canonical-authenticated-bootstrap-v1',
  'compiledSourceDeltaFromR44':delta,'staticBase':'/zhumadian/emergency/branding-20261025/',
  'originalApplicationBase':'/zhumadian/emergency/','originalRouterBase':'/zhumadian/emergency',
  'completeGlobalComponentsRetained':True,'onlyCodeLoadPromiseShared':True,'originalSDKAndBackendRetained':True,
  'newSupervisionModuleRequired':False,'onlySupportedOriginalSchemaFieldsRendered':True,
  'allOriginalNangangSchemasAccepted':False,'actualIISOrPublicAcceptance':False}
 source=baseSource.read_text(encoding='utf8');tree=ast.parse(source)
 replacements={'R38_FRONTEND_ROWS':rows,'R38_FRONTEND_CONTRACT':contract,'R38_REVISION':'20261104-R45-original-online-forms-and-authenticated-bootstrap'}
 for name,value in replacements.items():
  nodes=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
  assert len(nodes)==1;old=ast.get_source_segment(baseSource.read_text(encoding='utf8'),nodes[0]);assert source.count(old)==1
  source=source.replace(old,name+' = '+repr(value))
 function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='r38_unified_bundle_contract')
 before=ast.get_source_segment(baseSource.read_text(encoding='utf8'),function)
 after=before.replace("expected[R44_STYLE_FIELD]=R44_STYLE_CONTRACT","expected[R44_STYLE_FIELD]=R44_STYLE_CONTRACT;expected[R45_BOOTSTRAP_FIELD]=R45_BOOTSTRAP_CONTRACT")
 assert after!=before and source.count(before)==1
 source=source.replace(before,'R45_BOOTSTRAP_FIELD = "emergencyOriginalFormBootstrap"\nR45_BOOTSTRAP_CONTRACT = '+repr(feature)+'\n\n'+after)
 candidateTree=ast.parse(source)
 funcs=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 beforeFunctions,afterFunctions=funcs(tree),funcs(candidateTree)
 assert set(beforeFunctions)==set(afterFunctions)
 assert [n for n in beforeFunctions if beforeFunctions[n]!=afterFunctions[n]]==['r38_unified_bundle_contract']
 out=V/'original_public_test_update_r45_bootstrap_r847.py';assert not out.exists();out.write_text(source,encoding='utf8',newline='\n')
 assert shutil.disk_usage(R).free>2*1024**3+256*1024**2
 D.mkdir();O.mkdir();variants={};updater='tools/original_public_test_update.py'
 for label in ['r36','r37']:
  base=P44/label/'bundle';oldRoot=(R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle'if label=='r36'else R/'work/r39-plan-runtime-unified-r1/original-r37-contract')
  previous=J(oldRoot/'payload/payload-manifest.json');plan=copy.deepcopy(J(base/'update-manifest.json'))
  release=copy.deepcopy(J(base/'payload/release-manifest.json'));payload=copy.deepcopy(J(base/'payload/payload-manifest.json'))
  oldEmergency={n:p for n,p in payload['files'].items()if n.startswith('frontend/emergency_pc/')}
  assert oldEmergency==runtime.R38_FRONTEND_ROWS and len(oldEmergency)==341
  assert 'businessSupervisionPdf'not in release
  for n in oldEmergency:del payload['files'][n]
  payload['files'].update(rows)
  updaterPin={'bytes':out.stat().st_size,'sha256':sha(out)}
  if updater in payload['files']:payload['files'][updater]=updaterPin
  release['controllerFiles'][updater]=updaterPin['sha256'];release[runtime.R38_FRONTEND_FIELD]=contract
  release['emergencyOriginalFormBootstrap']=feature;release['publicTestRevision']=replacements['R38_REVISION']
  payloadRaw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payloadRaw).hexdigest();releaseRaw=enc(release)
  oldfront={n:p for n,p in previous['files'].items()if n.startswith('frontend/emergency_pc/')}
  changed={n:p for n,p in rows.items()if oldfront.get(n)!=p}
  writes={n:pin for n,pin in plan['files'].items()if not n.startswith('frontend/emergency_pc/')}
  writes.update({n:{'bytes':pin['bytes'],'SHA256':pin['sha256']}for n,pin in changed.items()})
  writes[updater]={'bytes':updaterPin['bytes'],'SHA256':updaterPin['sha256']}
  raw={'payload-manifest.json':payloadRaw,'release-manifest.json':releaseRaw}
  for n,b in raw.items():writes[n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
  plan.update(updateId='20261104-r45-original-bootstrap-from-'+label,files=writes,
   removedFrontendFiles={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldfront.items()if n not in rows},
   oldPayloadFiles={n:previous['files'][n]for n in writes if n in previous['files']},
   newReleaseSHA256=hashlib.sha256(releaseRaw).hexdigest(),newPayloadManifestSHA256=release['payloadManifestSHA256'])
  assert len(writes)<1000 and sum(p['bytes']for p in writes.values())<32*1024**2
  bundle=O/label/'bundle'
  for n,pin in writes.items():
   assert not n.startswith(('private/','UserData/','Assets/','Reference/','runtime/','seed/'))and'..'not in Path(n).parts
   target=bundle/'payload'/n
   if n in raw:put(target,raw[n]);continue
   origin=out if n==updater else BUILD/'dist'/n.removeprefix('frontend/emergency_pc/')if n.startswith('frontend/emergency_pc/')else base/'payload'/n
   assert origin.stat().st_size==pin['bytes']and sha(origin)==pin['SHA256'];target.parent.mkdir(parents=True,exist_ok=True);os.link(origin,target)
  put(bundle/'update-manifest.json',enc(plan))
  # The entire non-frontend payload equals R44 except its existing updater pin.
  retained={n:p for n,p in J(base/'payload/payload-manifest.json')['files'].items()if not n.startswith('frontend/emergency_pc/')and n!=updater}
  assert retained=={n:p for n,p in payload['files'].items()if not n.startswith('frontend/emergency_pc/')and n!=updater}
  variants[label]={'bundle':str(bundle),'manifestSHA256':sha(bundle/'update-manifest.json'),'newReleaseSHA256':plan['newReleaseSHA256'],
   'writes':len(writes),'removedFrontendPaths':len(plan['removedFrontendFiles']),'payloadLogicalBytes':sum(p['bytes']for p in writes.values()),
   'allR44BackendAuthenticationHistoryIISAndDataPinsRetained':True}
 assert variants['r36']['newReleaseSHA256']==variants['r37']['newReleaseSHA256']
 report={'prepared':True,'variants':variants,'runtimeSHA256':sha(out),'runtimeBytes':out.stat().st_size,
  'changedFunctions':['r38_unified_bundle_contract'],'unchangedFunctions':len(beforeFunctions)-1,
  'frontendFiles':344,'compiledSourceDeltaFromR44':delta,'newBackendOrSupervisionModuleIncluded':False,
  'actualOriginalPublicBackendCompatibilityStillPending':True,'publicChanged':False,'fullCloneReady':False}
 put(D/'prepared-bundles-r847.json',enc(report));print(json.dumps({k:v for k,v in report.items()if k!='compiledSourceDeltaFromR44'}))
if __name__=='__main__':main()
