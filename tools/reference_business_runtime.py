"""Prepare/select the Reference-source build and its exact bundled dependencies; no application launch."""
import argparse,datetime,hashlib,json,pathlib,re
import reference_flat_runtime

REFERENCE_SHA='b48adb8d966fa55656757d182cdd6b64c409d151c3e30ee3cbc5ef0cb86e68d8'
REBUILT_SHA='abbb76588157cf9ad8e53f98033568bb4c58c1e36a2040e149688c8fcd945485'
DEPLOYED_SHA='4c5bcf1bb3f76a3865c0cd6969cfef845934a11343d2987413f33715411dc902'
def sha(path):
 with pathlib.Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bounded(path,limit=2*1024**2):
 p=pathlib.Path(path).resolve(strict=True)
 if not p.is_file() or not 0<p.stat().st_size<=limit:raise ValueError('BOUNDED_RUNTIME_RECEIPT_REQUIRED')
 return json.loads(p.read_bytes())
def checked_workspace(workspace):
 W=pathlib.Path(workspace).resolve(strict=True)
 if W.parents[1].name!='Application':raise ValueError('APPLICATION_WORKSPACE_REQUIRED')
 return W
def source_inputs(workspace):
 W=checked_workspace(workspace);A=W.parents[1];root=W/'original-business-rebuild-d-original-flags';r=bounded(root/'receipt.json');project=bounded(A.parent/'Document/Deployment/tianjin_native_replica_20261023/original_source_copies.json')['projects']['business_java']
 if r['originalRuntimeSHA256']!=REFERENCE_SHA or r['candidateSHA256']!=REBUILT_SHA or r['javaSourceFiles']!=766 or r['resourceFiles']!=97 or r['compiledClasses']!=768 or not r['originalInputsUnchanged']:raise ValueError('FIXED_REFERENCE_SOURCE_REBUILD_REQUIRED')
 if pathlib.Path(r['candidate']).resolve()!=root/'cloud-endanger-original-source.jar' or pathlib.Path(r['source']).resolve()!=pathlib.Path(project['copy']).resolve():raise ValueError('EXACT_EXISTING_SOURCE_REBUILD_PATHS_REQUIRED')
 if sha(r['originalRuntime'])!=REFERENCE_SHA or sha(r['candidate'])!=REBUILT_SHA:raise ValueError('REFERENCE_OR_REBUILT_ARCHIVE_PIN_MISMATCH')
 rows=r['sourceInputs']
 if len(rows)!=863:raise ValueError('ALL_SOURCE_AND_RESOURCE_INPUTS_REQUIRED')
 for row in rows:
  rel=pathlib.PurePosixPath(row['path'])
  if rel.is_absolute() or '..' in rel.parts or ':' in str(rel):raise ValueError('RELATIVE_SOURCE_INPUT_REQUIRED')
  for base in [project['reference'],project['copy']]:
   base=pathlib.Path(base).resolve(strict=True);file=(base/pathlib.Path(*rel.parts)).resolve(strict=True)
   if not file.is_relative_to(base) or sha(file)!=row['sha256']:raise ValueError('REFERENCE_SOURCE_INPUT_CHANGED')
 return r,hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def prepare(workspace,output):
 W=checked_workspace(workspace);output=pathlib.Path(output).resolve()
 if not output.is_relative_to(W) or output.exists():raise ValueError('FRESH_OWN_RUNTIME_OUTPUT_REQUIRED')
 r,inputs_sha=source_inputs(W);libs=W/'original-business-rebuild-d-original-flags/libs'
 # Dependency verification precedes output creation in the existing packager.
 output.mkdir();flat=output/'flat'
 metadata=reference_flat_runtime.build(pathlib.Path(r['candidate']),libs,flat,REBUILT_SHA)
 proof=reference_flat_runtime.verify(flat)
 if metadata['compiledClassCount']!=768 or metadata['dependencyCount']!=220 or not proof['allOriginalApplicationAndDependencyBytesEqual']:raise ValueError('COMPLETE_REFERENCE_REBUILT_RUNTIME_REQUIRED')
 deployed=bounded(W/'original-shared-runtime-r1_20261024/flat/receipt.json');left={d['file']:d['sha256'] for d in metadata['dependencies']};right={d['file']:d['sha256'] for d in deployed['dependencies']}
 result={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'kind':'reference-source-rebuilt','sourceReferenceArchiveSHA256':REFERENCE_SHA,'sourceRebuiltArchiveSHA256':REBUILT_SHA,'sourceInputs':863,'sourceInputsSHA256':inputs_sha,'compiledClasses':768,'dependencyCount':220,'flatApplicationSHA256':metadata['applicationJarSHA256'],'flatReceiptSHA256':sha(flat/'receipt.json'),'originalSourceOrDependenciesModified':False,'dependencyFilesCopied':0,'dependencyDifferenceFromDeployed':{'onlyReference':sorted(set(left)-set(right)),'onlyDeployed':sorted(set(right)-set(left)),'sameNameDifferentBytes':[n for n in sorted(set(left)&set(right)) if left[n]!=right[n]]},'applicationStarted':False,'databaseConnected':False,'publicDeployed':False,'fullCloneReady':False}
 (output/'selection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
def select(workspace,receipt=None,expected_sha256=None):
 W=checked_workspace(workspace)
 if bool(receipt)!=bool(expected_sha256):raise ValueError('RUNTIME_RECEIPT_AND_PIN_PAIR_REQUIRED')
 if receipt is None:
  flat=W/'original-shared-runtime-r1_20261024/flat';r=bounded(flat/'receipt.json')
  if r['sourceArchiveSHA256']!=DEPLOYED_SHA or r['dependencyCount']!=219:raise ValueError('EXISTING_DEPLOYED_RUNTIME_CHANGED')
  return flat,{'mode':'deployed-archive','dependencyCount':219,'sourceArchiveSHA256':DEPLOYED_SHA,'selectionSHA256':None}
 receipt=pathlib.Path(receipt).resolve(strict=True)
 if not receipt.is_relative_to(W) or receipt.name!='selection.json' or not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256) or sha(receipt)!=expected_sha256:raise ValueError('EXPLICIT_OWN_SOURCE_RUNTIME_SELECTION_PIN_REQUIRED')
 r=bounded(receipt,65536)
 if r.get('kind')!='reference-source-rebuilt' or r.get('sourceReferenceArchiveSHA256')!=REFERENCE_SHA or r.get('sourceRebuiltArchiveSHA256')!=REBUILT_SHA or r.get('compiledClasses')!=768 or r.get('dependencyCount')!=220 or r.get('sourceInputs')!=863 or r.get('originalSourceOrDependenciesModified') is not False:raise ValueError('FIXED_REFERENCE_SOURCE_SELECTION_REQUIRED')
 source,inputs_sha=source_inputs(W)
 if inputs_sha!=r['sourceInputsSHA256']:raise ValueError('REFERENCE_SOURCE_SELECTION_INPUTS_CHANGED')
 flat=receipt.parent/'flat';metadata=bounded(flat/'receipt.json')
 if sha(flat/'receipt.json')!=r['flatReceiptSHA256'] or sha(flat/'application.jar')!=r['flatApplicationSHA256'] or metadata['sourceArchiveSHA256']!=REBUILT_SHA or metadata['sourceArchive']!=source['candidate'] or metadata['dependencyCount']!=220:raise ValueError('REFERENCE_SOURCE_RUNTIME_ARTIFACT_CHANGED')
 reference_flat_runtime.verify(flat)
 return flat,{'mode':'reference-source-rebuilt','dependencyCount':220,'sourceArchiveSHA256':REBUILT_SHA,'referenceArchiveSHA256':REFERENCE_SHA,'selectionSHA256':expected_sha256,'sourceInputsSHA256':inputs_sha}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','validate']);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path);p.add_argument('--receipt',type=pathlib.Path);p.add_argument('--receipt-sha256');a=p.parse_args()
 if a.command=='prepare':
  if not a.output or a.receipt or a.receipt_sha256:p.error('prepare requires only --output')
  r=prepare(a.workspace,a.output);print(json.dumps({k:r[k] for k in ['kind','compiledClasses','dependencyCount','sourceInputs','dependencyFilesCopied','applicationStarted','fullCloneReady']}))
 else:
  if a.output or not a.receipt or not a.receipt_sha256:p.error('validate requires a receipt and pin')
  _,r=select(a.workspace,a.receipt,a.receipt_sha256);print(json.dumps(r))
if __name__=='__main__':main()
