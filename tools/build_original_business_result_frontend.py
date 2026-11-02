"""Build the two original PC frontends with an explicit business-result adapter and all prior deployment adapters."""
from pathlib import Path
from contextlib import ExitStack
import sys,argparse,json,subprocess,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_original_frontend as base
from original_business_result_compat import business_result_override

def build(kind,project,reference,manifest,node,output,api_prefix,public_base,local_command=False,home_navigation=False,admin_home_base=None,map_tile_base=None,mobile_qr_url=None,workflow_request=False,approval_retry=False,request_error=True,business_result=False,inspection_filter=False,third_party_credentials=False,training_assessment=False):
 if kind not in ('security_pc','emergency_pc'):raise ValueError('ORIGINAL_PC_KIND_REQUIRED')
 if inspection_filter and kind!='security_pc':raise ValueError('INSPECTION_FILTER_SECURITY_PC_ONLY')
 if third_party_credentials and kind!='security_pc':raise ValueError('THIRD_PARTY_CREDENTIALS_SECURITY_PC_ONLY')
 if training_assessment and kind!='security_pc':raise ValueError('TRAINING_ASSESSMENT_SECURITY_PC_ONLY')
 if business_result and not request_error:raise ValueError('BUSINESS_RESULT_REQUIRES_ERROR_PRESERVATION_BASELINE')
 if not business_result and not inspection_filter and not third_party_credentials and not training_assessment:return base.build(kind,project,manifest,node,output,api_prefix,public_base,reference,local_command,mobile_qr_url,home_navigation,map_tile_base,admin_home_base,False,workflow_request,request_error,approval_retry)
 project,reference,manifest,node,output=(Path(p).resolve() for p in [project,reference,manifest,node,output]);base.route(api_prefix,False);base.route(public_base,True)
 if kind!='security_pc' and (local_command or home_navigation or admin_home_base or mobile_qr_url or workflow_request or approval_retry):raise ValueError('SECURITY_PORTAL_ADAPTER_SCOPE_REQUIRED')
 if admin_home_base and not home_navigation:raise ValueError('HOME_NAVIGATION_REQUIRED')
 if map_tile_base:base.map_tile_path(map_tile_base)
 if mobile_qr_url:base.mobile_entry_url(mobile_qr_url)
 if output.exists() or output.is_relative_to(project) or project.is_relative_to(output) or output.is_relative_to(reference) or reference.is_relative_to(output):raise ValueError('FRESH_INDEPENDENT_PC_OUTPUT_REQUIRED')
 expected=base.baseline_files(json.loads(manifest.read_text(encoding='utf-8-sig')),kind);base.verify_inputs(project,expected);base.verify_inputs(reference,expected);cli=project/'node_modules/vite/bin/vite.js'
 if not node.is_file() or not cli.is_file():raise ValueError('EXISTING_EXPLICIT_PC_COMPILER_REQUIRED')
 output.mkdir(parents=True);dist=output/'dist';env=base.deployment_environment(kind,api_prefix,public_base);command=[str(node),str(cli),'build','--mode','replica-deploy','--outDir',str(dist),'--base',public_base];start=time.monotonic();home=tile=workflow=approval=error=result=inspection=third_party=exam=None
 with ExitStack() as adapters:
  if local_command or home_navigation:home=adapters.enter_context(base.home_deployment_override(project,reference,local_command,public_base.rstrip('/') if home_navigation else None,admin_home_base))
  if map_tile_base:tile=adapters.enter_context(base.map_tile_override(project,reference,map_tile_base))
  if workflow_request:workflow=adapters.enter_context(base.workflow_request_override(project,reference))
  error=adapters.enter_context(base.request_error_override(kind,project,reference))
  if business_result:result=adapters.enter_context(business_result_override(kind,project,reference))
  if inspection_filter:
   from original_inspection_filter_compat import inspection_filter_override
   inspection=adapters.enter_context(inspection_filter_override(project,reference))
  if third_party_credentials:
   from original_third_party_frontend_compat import third_party_credentials_override
   third_party=adapters.enter_context(third_party_credentials_override(project,reference))
  if training_assessment:
   from original_training_assessment_frontend_compat import training_assessment_override
   exam=adapters.enter_context(training_assessment_override(project,reference))
  if approval_retry:approval=adapters.enter_context(base.approval_retry_override(project,reference))
  with (output/'build.log').open('wb') as log:process=subprocess.run(command,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 base.verify_inputs(project,expected);base.verify_inputs(reference,expected)
 if process.returncode!=0 or not (dist/'index.html').is_file():raise RuntimeError('ORIGINAL_PC_COMPILER_FAILED_LOG_RETAINED')
 qr=base.replace_output_mobile_qr(dist,mobile_qr_url) if mobile_qr_url else None
 files=[{'path':p.relative_to(dist).as_posix(),'bytes':p.stat().st_size,'sha256':base.sha(p)} for p in sorted(dist.rglob('*')) if p.is_file()];counts={k:0 for k in ['undefined/serv','undefined/jnpf',api_prefix]}
 for p in dist.rglob('*.js'):
  raw=p.read_bytes()
  for key in counts:counts[key]+=raw.count(key.encode())
 if counts['undefined/serv'] or counts['undefined/jnpf'] or not counts[api_prefix]:raise ValueError('COMPILED_PC_API_PREFIX_INVALID')
 receipt={'kind':kind,'mode':'replica-deploy','command':command,'nodeSHA256':base.sha(node),'sourceManifestSHA256':base.sha(manifest),'sourceInputFilesVerified':len(expected),'sourceFilesUnchanged':True,'originalReferenceUnchanged':True,'sourceLogicPatched':True,'localCommandDeploymentAdapter':home if local_command else None,'homeNavigationDeploymentAdapter':home if home_navigation else None,'mapTileDeploymentAdapter':tile,'mobileQRDeploymentAdapter':qr,'workflowRequestCompatibility':workflow,'requestErrorCompatibility':error,'approvalRetryCompatibility':approval,'businessResultCompatibility':result,'inspectionPointNameCompatibility':inspection,'thirdPartyCredentialsCompatibility':third_party,'trainingAssessmentCompatibility':exam,'deploymentOverrides':{k:v for k,v in env.items() if k.startswith(('VITE_','UNI_'))},'seconds':round(time.monotonic()-start,3),'exitCode':process.returncode,'output':str(dist),'fileCount':len(files),'bytes':sum(p['bytes'] for p in files),'files':files,'compiledPathOccurrences':counts,'backendConnected':False,'publicDeployed':False,'businessParityVerified':False,'builderSHA256':base.sha(Path(__file__))};(output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--business-result',action='store_true');p.add_argument('--inspection-filter',action='store_true');p.add_argument('--third-party-credentials',action='store_true');p.add_argument('--training-assessment',action='store_true');args=p.parse_args();config=json.loads(args.config.read_text(encoding='utf-8-sig'));r=build(**config,business_result=args.business_result,inspection_filter=args.inspection_filter,third_party_credentials=args.third_party_credentials,training_assessment=args.training_assessment);print(json.dumps({k:r[k] for k in ['kind','fileCount','bytes','seconds','sourceInputFilesVerified','sourceFilesUnchanged','publicDeployed']}))
if __name__=='__main__':main()
