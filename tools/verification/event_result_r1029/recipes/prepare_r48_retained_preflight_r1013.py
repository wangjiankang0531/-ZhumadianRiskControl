"""Workspace-only source preparation; does not run the blocked file verifier."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');OLD=R/'Document/Deployment/event_result_runtime_r1000_20261105';D=V/'r48-retained-preflight-r2-r1013'
J=lambda p:json.loads(Path(p).read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def funcs(text):return {n.name:ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert not D.exists();old=(OLD/'source/original_public_test_update.py').read_text('utf8')
node=next(n for n in ast.walk(ast.parse(old))if isinstance(n,ast.FunctionDef)and n.name=='preflight')
oldcheck="        m.check_file(bundle/'payload',DESCRIPTOR['file'],DESCRIPTOR['sha256'],DESCRIPTOR['bytes'])"
assert old.count(oldcheck)==1 and oldcheck.strip()in ast.get_source_segment(old,node)
jar='payload/business/run-template/own-supervision-pdf.jar'
assert jar in J(OLD/'update-from-r45.json')['files']and jar not in J(OLD/'update-from-r47.json')['files']
new=old.replace(oldcheck,"        module_root=bundle/'payload' if DESCRIPTOR['file'] in plan['files'] else app\n        m.check_file(module_root,DESCRIPTOR['file'],DESCRIPTOR['sha256'],DESCRIPTOR['bytes'])")
end=new.index('"""',3)+3
new='"""R48 with exact event result metadata and retained supervision preflight.\n\nR2 selects the staged module only when transported, otherwise the installed\nmodule. Existing process, mutation, restoration, authentication and health\nfunction bodies are retained from the first prepared R48 candidate.\n"""'+new[end:]
before,after=funcs(old),funcs(new);assert set(before)==set(after)
changed=[n for n in before if before[n]!=after[n]];assert changed==['runtime','preflight']
D.mkdir();(D/'source').mkdir();(D/'candidate').mkdir()
wp=D/'source/original_public_test_update.py';wp.write_text(new,encoding='utf8')
shutil.copyfile(OLD/'source/original_public_test_base_r46.py',D/'source/original_public_test_base_r46.py')
assert sha(D/'source/original_public_test_base_r46.py')==sha(OLD/'source/original_public_test_base_r46.py')
wrapper=load('r48_retained_r2_r1013',wp);m=wrapper.runtime();targets={};variants={}
for label,origin in [('r45',R/'work/original-backend-bootstrap-r847/r36/bundle/payload'),('r47',R/'work/unified-home-supervision-r928/bundle/payload')]:
 oldrelease=J(origin/'release-manifest.json');previous=J(origin/'payload-manifest.json');payload=copy.deepcopy(previous);payload['files']=m.r48_expected_files(previous['files']);raw=enc(payload)
 release=m.r48_expected_release(oldrelease,hashlib.sha256(raw).hexdigest());assert wrapper.declared(release);targets[label]=(payload,release)
assert targets['r45']==targets['r47']
payload,release=targets['r47'];(D/'candidate/payload-manifest.json').write_bytes(enc(payload));(D/'candidate/release-manifest.json').write_bytes(enc(release))
for label,origin in [('r45',R/'work/original-backend-bootstrap-r847/r36/bundle/payload'),('r47',R/'work/unified-home-supervision-r928/bundle/payload')]:
 plan=J(OLD/('update-from-'+label+'.json'));previous=J(origin/'payload-manifest.json')
 changed_files={n:p for n,p in payload['files'].items()if previous['files'].get(n)!=p}
 plan['files']={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in changed_files.items()}
 for n in ['payload-manifest.json','release-manifest.json']:
  p=D/'candidate'/n;plan['files'][n]={'bytes':p.stat().st_size,'SHA256':sha(p)}
 plan.update(newPayloadManifestSHA256=sha(D/'candidate/payload-manifest.json'),newReleaseSHA256=sha(D/'candidate/release-manifest.json'),oldPayloadFiles={n:previous['files'][n]for n in plan['files']if n in previous['files']})
 (D/('update-from-'+label+'.json')).write_bytes(enc(plan));variants[label]={'writes':len(plan['files']),'removed':len(plan['removedFrontendFiles']),'supervisionJarTransported':jar in plan['files']}
report={'preparedInWritableWorkspaceOnly':True,'confirmedR1RetainedJarStagePathDefect':True,'changedNestedFunctionOnly':'preflight','enclosingRuntimeASTAlsoChanges':True,
 'frozenCoreByteIdenticalToR1':True,'sameFrontendAndBusinessProgramsAsNativeVerifiedR1':True,'allOtherWrapperFunctionASTsIdentical':True,
 'bothExactBasesStillProduceOneTarget':True,'variants':variants,'newReleaseSHA256':sha(D/'candidate/release-manifest.json'),'newUpdaterSHA256':sha(wp),
 'newR2FullFileValidationExecuted':False,'newR2ExactControlLifecycleExecuted':False,'publicPackageOrProjectFilesChanged':False,'blockedR1008NotExecutedOrRelocated':True,
 'supersedesForFutureExecution':'R1008 first-draft file verification must not be run as the final R2 verification','fullCloneReady':False}
(D/'prepared-r2-r1013.json').write_bytes(enc(report));print(json.dumps(report))
