"""Build the complete emergency frontend retaining team fix and guarding two resource results."""
from pathlib import Path
from contextlib import ExitStack
from original_confirmed_operation_compat import confirmed_operation_override,NOTICE as CONFIRM_NOTICE
from original_event_operations_frontend_compat import event_operation_override,NOTICE as EVENT_NOTICE
import argparse,json,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_original_frontend as base
from original_business_result_compat import business_result_override
from original_emergency_team_frontend_compat import emergency_team_override
from original_emergency_resource_result_compat import resource_result_override,NOTICE
from original_duty_result_compat import duty_result_override,NOTICE as DUTY_NOTICE

def build(project,reference,manifest,node,output,api_prefix,public_base,map_tile_base=None):
    project,reference,manifest,node,output=(Path(p).resolve() for p in (project,reference,manifest,node,output));kind='emergency_pc';base.route(api_prefix,False);base.route(public_base,True)
    if map_tile_base:base.map_tile_path(map_tile_base)
    if output.exists() or output.is_relative_to(project) or project.is_relative_to(output) or output.is_relative_to(reference) or reference.is_relative_to(output):raise ValueError('FRESH_DISTINCT_EMERGENCY_OUTPUT_REQUIRED')
    expected=base.baseline_files(json.loads(manifest.read_text('utf-8-sig')),kind);base.verify_inputs(project,expected);base.verify_inputs(reference,expected);cli=project/'node_modules/vite/bin/vite.js'
    if not node.is_file() or not cli.is_file():raise ValueError('EXISTING_EXPLICIT_EMERGENCY_COMPILER_REQUIRED')
    output.mkdir(parents=True);dist=output/'dist';env=base.deployment_environment(kind,api_prefix,public_base);command=[str(node),str(cli),'build','--mode','replica-deploy','--outDir',str(dist),'--base',public_base];start=time.monotonic()
    with ExitStack() as adapters:
        error=adapters.enter_context(base.request_error_override(kind,project,reference));business=adapters.enter_context(business_result_override(kind,project,reference));tile=adapters.enter_context(base.map_tile_override(project,reference,map_tile_base)) if map_tile_base else None;team=adapters.enter_context(emergency_team_override(project,reference));resources=[adapters.enter_context(resource_result_override(k,project,reference)) for k in ("materials","emergencyExperts")];duties=[adapters.enter_context(duty_result_override(k,project,reference)) for k in ("dutySchedule","dutyPersonnel","dutyLog")]
        confirmation=adapters.enter_context(confirmed_operation_override(kind,project,reference))
        events=adapters.enter_context(event_operation_override(project,reference))
        with (output/'build.log').open('xb') as log:process=subprocess.run(command,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    base.verify_inputs(project,expected);base.verify_inputs(reference,expected)
    if process.returncode!=0 or not (dist/'index.html').is_file():raise RuntimeError('EMERGENCY_COMPILER_FAILED_LOG_RETAINED')
    files=[{'path':p.relative_to(dist).as_posix(),'bytes':p.stat().st_size,'sha256':base.sha(p)} for p in sorted(dist.rglob('*')) if p.is_file()];counts={k:0 for k in ['undefined/serv','undefined/jnpf',api_prefix]};messages=[];dutyMessages=[];dutyNotice=DUTY_NOTICE.encode('utf-8');resourceMessages=[];resourceNotice=NOTICE.encode('utf-8');notice='保存未完成，请保留当前内容，核对队伍状态后重试。'.encode('utf-8')
    for p in dist.rglob('*.js'):
        raw=p.read_bytes()
        for key in counts:counts[key]+=raw.count(key.encode())
        if dutyNotice in raw:dutyMessages.append({'path':p.relative_to(dist).as_posix(),'messageOccurrences':raw.count(dutyNotice),'sha256':base.sha(p)})
        if resourceNotice in raw:resourceMessages.append({'path':p.relative_to(dist).as_posix(),'messageOccurrences':raw.count(resourceNotice),'sha256':base.sha(p)})
        if notice in raw:messages.append({'path':p.relative_to(dist).as_posix(),'messageOccurrences':raw.count(notice),'sha256':base.sha(p)})
    if counts['undefined/serv'] or counts['undefined/jnpf'] or not counts[api_prefix] or sum(x['messageOccurrences'] for x in messages)!=1 or sum(x['messageOccurrences'] for x in resourceMessages)!=2 or not 3<=sum(x['messageOccurrences'] for x in dutyMessages)<=4:raise ValueError('COMPLETE_COMPILED_EMERGENCY_ADAPTER_REQUIRED')
    confirmationChunks=[]
    for p in dist.rglob('*.js'):
     raw=p.read_bytes()
     if CONFIRM_NOTICE.encode('utf8') in raw:confirmationChunks.append({'path':p.relative_to(dist).as_posix(),'occurrences':raw.count(CONFIRM_NOTICE.encode('utf8')),'sha256':base.sha(p)})
    if not confirmationChunks:raise ValueError('COMPILED_CONFIRMATION_RESULT_GUARD_REQUIRED')
    eventChunks=[]
    for p in dist.rglob('*.js'):
     raw=p.read_bytes()
     if EVENT_NOTICE.encode('utf8') in raw:eventChunks.append({'path':p.relative_to(dist).as_posix(),'occurrences':raw.count(EVENT_NOTICE.encode('utf8')),'sha256':base.sha(p)})
    if len(eventChunks)!=3 or not 3<=sum(row['occurrences'] for row in eventChunks)<=4:raise ValueError('FOUR_COMPILED_EVENT_OPERATION_GUARDS_REQUIRED')
    receipt={'kind':kind,'mode':'replica-deploy','command':command,'builderSHA256':base.sha(Path(__file__)),'nodeSHA256':base.sha(node),'sourceManifestSHA256':base.sha(manifest),'sourceInputFilesVerified':len(expected),'sourceFilesUnchanged':True,'originalReferenceUnchanged':True,'requestErrorCompatibility':error,'businessResultCompatibility':business,'mapTileDeploymentAdapter':tile,'emergencyTeamSubmitCompatibility':team,'resourceResultCompatibility':resources,'dutyResultCompatibility':duties,'confirmedOperationCompatibility':confirmation,'eventOperationCompatibility':events,'eventOperationMessageChunks':eventChunks,'confirmationMessageChunks':confirmationChunks,'dutyMessageChunks':dutyMessages,'resourceMessageChunks':resourceMessages,'fileCount':len(files),'bytes':sum(r['bytes'] for r in files),'files':files,'compiledPathOccurrences':counts,'newMessageContainingChunks':messages,'seconds':round(time.monotonic()-start,3),'exitCode':process.returncode,'originalFormTemplatePreserved':True,'backendConnected':False,'publicDeployed':False,'businessParityVerified':False};(output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf-8');return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);args=parser.parse_args();receipt=build(**json.loads(args.config.read_text('utf-8-sig')));print(json.dumps({k:receipt[k] for k in ['kind','fileCount','bytes','sourceInputFilesVerified','sourceFilesUnchanged','seconds','publicDeployed']}))
