"""Read-only current managed-sync identity, including exact listener ownership."""
from pathlib import Path
import re
from services.layer_sync_bridge import process_creation
from tools.layer_sync_server_owner import plain,read,loads,sha,sample_processes,_options
from tools.layer_sync_supervisor import controller_record,verify_package
from tools.serve_layer_sync import read_server_config


def inspect_sync_instance(control_root,package,config_path,config_sha,manifest_sha,data_root,python_executable,*,sampler=sample_processes):
    control_root,package,config_path,data_root=map(plain,(control_root,package,config_path,data_root))
    python_executable=Path(python_executable).resolve(strict=True)
    verify_package(package,manifest_sha)
    config,_,actual_sha=read_server_config(config_path,config_sha)
    record,pointer_raw=controller_record(control_root)
    if record is None or record['configSHA256']!=config_sha or record['manifestSHA256']!=manifest_sha:
        raise ValueError('EXACT_MANAGED_SYNC_CONTROLLER_REQUIRED')
    if process_creation(record['pid'])!=record['creation']:raise ValueError('MANAGED_SYNC_CONTROLLER_NOT_ALIVE')
    candidates=[]
    for item in plain(record['run']).iterdir():
        if item.is_dir() and re.fullmatch('[0-9a-f]{32}',item.name) and (item/'ready.json').exists():
            path=plain(item/'ready.json');raw=read(path,16384);ready=loads(raw)
            fields={'schema','listen','pid','creation','port','nativePlatformPort','instanceId','configSHA256','manifestSHA256'}
            if (not isinstance(ready,dict) or set(ready)!=fields or ready['schema']!='xnby.layer-sync.ready.v2'
                    or ready['listen']!='127.0.0.1' or ready['instanceId']!=item.name
                    or ready['configSHA256']!=config_sha or ready['manifestSHA256']!=manifest_sha
                    or ready['port']!=config['listenPort'] or ready['nativePlatformPort']!=config['platformPort']):
                raise ValueError('MANAGED_SYNC_READY_CHANGED')
            if process_creation(ready['pid'])==ready['creation']:candidates.append((path,raw,ready))
            if len(candidates)>1:raise ValueError('MULTIPLE_LIVE_MANAGED_SYNC_WORKERS')
    if len(candidates)!=1:raise ValueError('UNIQUE_LIVE_MANAGED_SYNC_WORKER_REQUIRED')
    ready_path,ready_raw,ready=candidates[0]
    observed=sampler([record['pid'],ready['pid']],config['listenPort'])
    rows=observed.get('processes');listeners=observed.get('listeners')
    if not isinstance(rows,list) or len(rows)!=2 or not isinstance(listeners,list) or len(listeners)!=1:
        raise ValueError('EXACT_SYNC_PROCESS_AND_LISTENER_OBSERVATION_REQUIRED')
    by_id={row['pid']:row for row in rows}
    if set(by_id)!={record['pid'],ready['pid']}:raise ValueError('SYNC_PROCESS_SELECTION_CHANGED')
    for pid,birth in [(record['pid'],record['creation']),(ready['pid'],ready['creation'])]:
        row=by_id[pid]
        if row.get('creation')!=birth or plain(row['image'])!=python_executable or Path(row['argv'][0]).resolve(strict=True)!=python_executable:
            raise ValueError('SYNC_PROCESS_IMAGE_OR_CREATION_CHANGED')
    parent=by_id[record['pid']];child=by_id[ready['pid']]
    if child.get('parent')!=record['pid'] or int(child['creation'])<int(parent['creation']):raise ValueError('SYNC_PROCESS_LINEAGE_CHANGED')
    def args(row,script,mode=False):
        values=row['argv'][1:]
        while values and values[0] in ('-I','-B'):values=values[1:]
        if not values or plain(values[0])!=package/'tools'/script:raise ValueError('SYNC_PROCESS_SCRIPT_CHANGED')
        values=values[1:]
        if mode:
            if not values or values[0]!='run':raise ValueError('SYNC_CONTROLLER_MODE_CHANGED')
            values=values[1:]
        return values
    common={'--config','--config-sha256','--manifest-sha256','--data-root'}
    parent_options=_options(args(parent,'manage_layer_sync_server.py',True),common|{'--control-root','--max-restarts','--start-timeout','--stop-timeout'})
    child_options=_options(args(child,'serve_layer_sync.py'),common|{'--run-root','--instance-id'})
    for options in [parent_options,child_options]:
        if (not common<=set(options) or plain(options['--config'])!=config_path or plain(options['--data-root'])!=data_root
                or options['--config-sha256']!=config_sha or options['--manifest-sha256']!=manifest_sha):
            raise ValueError('SYNC_PROCESS_ARGUMENT_BINDING_CHANGED')
    if plain(parent_options.get('--control-root',''))!=control_root or plain(child_options.get('--run-root',''))!=ready_path.parent or child_options.get('--instance-id')!=ready['instanceId']:
        raise ValueError('SYNC_PRIVATE_RUN_BINDING_CHANGED')
    if listeners!=[{'address':'127.0.0.1','port':config['listenPort'],'pid':ready['pid']}]:raise ValueError('SYNC_LISTENER_OWNER_CHANGED')
    if read(control_root/'current.private.json',16384)!=pointer_raw or read(ready_path,16384)!=ready_raw or sha(read(config_path,32768))!=config_sha:
        raise ValueError('SYNC_CHANGED_DURING_OWNER_OBSERVATION')
    verify_package(package,manifest_sha)
    return {'schema':'xnby.layer-sync.deployment-service.v1','controller':{'pid':record['pid'],'creation':record['creation']},
            'worker':{'pid':ready['pid'],'creation':ready['creation']},'port':config['listenPort'],'instanceId':record['instanceId'],
            'configSHA256':config_sha,'manifestSHA256':manifest_sha}
