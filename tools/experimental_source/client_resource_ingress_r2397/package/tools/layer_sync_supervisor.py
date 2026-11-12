"""Own the exact interpreted layer worker, its normal stop and bounded recovery.

No gateway edits, process-name kills, credentials or automatic database repair.
The original application controller must retain this controller's Popen handle.
"""
from contextlib import AbstractContextManager
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import subprocess
import sys
import time
import uuid

from services.common import loads
from services.layer_sync_bridge import process_creation
from tools.original_server_windows_job import OwnedWindowsJob


def plain(path):
    path=Path(path).absolute()
    if '..' in path.parts:raise ValueError('CANONICAL_SYNC_CONTROLLER_PATH_REQUIRED')
    for item in (*reversed(path.parents),path):
        if item.exists() and (item.is_symlink() or getattr(item.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('SYNC_CONTROLLER_REDIRECTION_REJECTED')
    return path


def read(path,limit):
    with plain(path).open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('SYNC_CONTROLLER_INPUT_TOO_LARGE')
    return raw


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def hexpin(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('EXACT_SYNC_PIN_REQUIRED')
    return value


def verify_package(package,expected_sha):
    package=plain(package);raw=read(package/'package-manifest.json',131072)
    if digest(raw)!=hexpin(expected_sha):raise ValueError('SYNC_PACKAGE_MANIFEST_PIN_CHANGED')
    manifest=loads(raw)
    if not isinstance(manifest,dict) or manifest.get('schema')!='xnby.layer-sync.package.v1':raise ValueError('INVALID_SYNC_PACKAGE_MANIFEST')
    inputs=manifest.get('inputs')
    if not isinstance(inputs,dict) or not 1<=len(inputs)<=64:raise ValueError('INVALID_SYNC_PACKAGE_INPUTS')
    required={'services/__init__.py','tools/serve_layer_sync.py','tools/layer_sync_supervisor.py','tools/original_server_windows_job.py','tools/manage_layer_sync_server.py'}
    if not required<=set(inputs):raise ValueError('INCOMPLETE_MANAGED_SYNC_PACKAGE')
    models={'scene_model_sync/__init__.py','scene_model_sync/api.py','scene_model_sync/repository.py','scene_model_sync/validation.py'}
    if models&set(inputs) and not models<=set(inputs):raise ValueError('INCOMPLETE_MANAGED_MODEL_PACKAGE')
    for name,pin in inputs.items():
        path=PurePosixPath(name)
        if (not re.fullmatch('[A-Za-z0-9_./-]+',name) or path.is_absolute() or path.as_posix()!=name or '..' in path.parts
                or (path.parts[0] not in ('services','tools','shared') and name not in ('scene_model_sync/__init__.py','scene_model_sync/api.py','scene_model_sync/repository.py','scene_model_sync/validation.py')) or path.suffix not in ('.py','.json','.mjs')):
            raise ValueError('INVALID_SYNC_PACKAGE_PATH')
        if not isinstance(pin,dict) or type(pin.get('bytes')) is not int or not 0<=pin['bytes']<=2*1048576:
            raise ValueError('INVALID_SYNC_SOURCE_PIN')
        actual=read(package/name,pin['bytes'])
        if len(actual)!=pin['bytes'] or digest(actual)!=hexpin(pin.get('sha256')):raise ValueError('SYNC_PACKAGE_SOURCE_CHANGED')
    return manifest


class Lease(AbstractContextManager):
    def __init__(self,path):
        if os.name!='nt':raise RuntimeError('WINDOWS_SYNC_CONTROLLER_REQUIRED')
        import msvcrt
        self.stream=plain(path).open('a+b')
        try:
            if not plain(path).stat().st_size:self.stream.write(b'0');self.stream.flush()
            self.stream.seek(0);msvcrt.locking(self.stream.fileno(),msvcrt.LK_NBLCK,1)
        except BaseException:self.stream.close();raise
    def __exit__(self,*unused):self.stream.close()


def write_new(path,raw):
    path=plain(path)
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def marker(path,value):
    raw=encode(value);path=plain(path)
    if path.exists():
        if read(path,8192)!=raw:raise ValueError('UNKNOWN_SYNC_STOP_MARKER_RETAINED')
    else:write_new(path,raw)


def controller_record(root):
    root=plain(root);pointer=plain(root/'current.private.json')
    if not pointer.exists():return None,None
    raw=read(pointer,16384);record=loads(raw)
    fields={'schema','pid','creation','instanceId','run','configSHA256','manifestSHA256'}
    if (not isinstance(record,dict) or set(record)!=fields or record['schema']!='xnby.layer-sync.controller.v1'
            or type(record['pid']) is not int or not 0<record['pid']<2**32
            or not isinstance(record['creation'],str) or not re.fullmatch('[0-9]{1,20}',record['creation'])
            or not isinstance(record['instanceId'],str) or not re.fullmatch('[0-9a-f]{32}',record['instanceId'])):
        raise ValueError('UNKNOWN_SYNC_CONTROLLER_RECORD_RETAINED')
    hexpin(record['configSHA256']);hexpin(record['manifestSHA256']);run=plain(record['run'])
    if run.parent!=root/'runs' or run.name!=record['instanceId']:raise ValueError('SYNC_CONTROLLER_RUN_BINDING_CHANGED')
    return record,raw


def request_controller_stop(root):
    record,raw=controller_record(root)
    if record is None:return {'stopRequested':False,'state':'not-running'}
    if process_creation(record['pid'])!=record['creation']:return {'stopRequested':False,'state':'stale-record-retained'}
    marker(Path(record['run'])/'stop.json',{'schema':'xnby.layer-sync.controller-stop.v1','instanceId':record['instanceId'],'configSHA256':record['configSHA256']})
    return {'stopRequested':True,'instanceId':record['instanceId']}


def controller_status(root):
    record,_=controller_record(root)
    if record is None:return {'running':False,'state':'not-running'}
    alive=process_creation(record['pid'])==record['creation']
    return {'running':alive,'state':'running' if alive else 'stale-record-retained','instanceId':record['instanceId'],'pid':record['pid']}


def supervise(package,config_path,config_sha,manifest_sha,data_root,control_root,*,max_restarts=1,start_timeout=15,stop_timeout=15):
    if type(max_restarts) is not int or not 0<=max_restarts<=3 or not .5<=start_timeout<=120 or not .5<=stop_timeout<=30:
        raise ValueError('INVALID_SYNC_RECOVERY_BOUND')
    package=plain(package);config_path=plain(config_path);data_root=plain(data_root);control_root=plain(control_root)
    if (data_root==control_root or data_root.is_relative_to(package) or control_root.is_relative_to(package)
            or control_root.is_relative_to(data_root) or data_root.is_relative_to(control_root)):
        raise ValueError('SEPARATE_PRIVATE_SYNC_ROOTS_REQUIRED')
    from tools.serve_layer_sync import read_server_config
    verify_package(package,manifest_sha);config,_,actual_config_sha=read_server_config(config_path,hexpin(config_sha))
    control_root.mkdir(parents=True,exist_ok=True);runs=plain(control_root/'runs');runs.mkdir(exist_ok=True)
    with Lease(control_root/'controller.lock'):
        previous,previous_raw=controller_record(control_root)
        if previous is not None and process_creation(previous['pid'])==previous['creation']:raise ValueError('PRIOR_SYNC_CONTROLLER_STILL_ALIVE')
        if previous is not None:
            prior_exit=plain(Path(previous['run'])/'controller-exit.json')
            if not prior_exit.is_file():raise ValueError('PRIOR_SYNC_WORKER_RETIREMENT_NOT_PROVEN')
            prior_proof=loads(read(prior_exit,8192))
            if not isinstance(prior_proof,dict) or prior_proof.get('originalWorkerHandleRetired') is not True:
                raise ValueError('PRIOR_SYNC_WORKER_RETIREMENT_NOT_PROVEN')
        instance=uuid.uuid4().hex;run=plain(runs/instance);run.mkdir()
        record={'schema':'xnby.layer-sync.controller.v1','pid':os.getpid(),'creation':process_creation(os.getpid()),'instanceId':instance,
                'run':str(run),'configSHA256':config_sha,'manifestSHA256':manifest_sha}
        record_raw=encode(record);pointer=plain(control_root/'current.private.json');pending=control_root/(instance+'.pending')
        write_new(pending,record_raw)
        if (previous_raw is None and pointer.exists()) or (previous_raw is not None and read(pointer,16384)!=previous_raw):raise ValueError('SYNC_CONTROLLER_POINTER_CHANGED')
        os.replace(pending,pointer)
        stop_value={'schema':'xnby.layer-sync.controller-stop.v1','instanceId':instance,'configSHA256':config_sha}
        def stopped():
            stop=plain(run/'stop.json')
            return stop.exists() and loads(read(stop,8192))==stop_value
        def event(kind,**details):
            with plain(run/'events.jsonl').open('ab') as stream:stream.write(encode({'event':kind,'time':time.time(),'instanceId':instance,**details}));stream.flush();os.fsync(stream.fileno())
        proc=job=child_run=None;exit_code=1;restart=0
        def retire():
            nonlocal proc,job,exit_code
            if proc is None:return
            exceeded=False
            if proc.poll() is None:
                try:
                    marker(child_run/'stop.json',{'schema':'xnby.layer-sync.worker-stop.v1','instanceId':child_run.name,'configSHA256':config_sha})
                except (OSError,ValueError) as error:
                    exit_code=1
                    event('worker-stop-marker-refused-live-handle-retained',errorClass=type(error).__name__)
                try:proc.wait(timeout=stop_timeout)
                except subprocess.TimeoutExpired:
                    exceeded=True;exit_code=1
                    event('worker-stop-timeout-live-handle-retained',pid=proc.pid,noTerminationOrReplacement=True)
                    # Observation expiry does not prove termination or authorize a
                    # replacement. Keep the exact Popen and Job until real exit.
                    proc.wait()
            else:proc.wait()
            if job is not None:
                descendants_deadline=time.monotonic()+stop_timeout
                descendants_overdue=False
                while job.active_processes():
                    if not descendants_overdue and time.monotonic()>=descendants_deadline:
                        descendants_overdue=True;exit_code=1
                        event('owned-descendants-stop-timeout-live-handle-retained',noTerminationOrReplacement=True)
                    time.sleep(.05)
            event('worker-retired',pid=proc.pid,exitCode=proc.returncode,forcedJobClose=False,
                  originalHandleWaited=True,normalStopDeadlineExceeded=exceeded)
            if job is not None:job.close()
            proc=job=None
        try:
            event('controller-start',maxRestarts=max_restarts)
            while True:
                if stopped():exit_code=0;break
                verify_package(package,manifest_sha);read_server_config(config_path,config_sha)
                child_run=plain(run/uuid.uuid4().hex);child_run.mkdir()
                with (child_run/'stdout.log').open('xb') as output,(child_run/'stderr.log').open('xb') as error:
                    proc=subprocess.Popen([sys.executable,'-I','-B',str(package/'tools/serve_layer_sync.py'),'--config',str(config_path),
                                           '--data-root',str(data_root),'--run-root',str(child_run),'--instance-id',child_run.name,
                                           '--config-sha256',config_sha,'--manifest-sha256',manifest_sha],stdout=output,stderr=error,
                                          creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
                try:job=OwnedWindowsJob(proc)
                except BaseException:
                    # Assignment failure cannot authorize a new worker or a PID kill.
                    event('worker-job-assignment-refused-live-handle-retained')
                    raise  # The finally block owns the normal stop and exact wait.
                event('worker-start',pid=proc.pid,attempt=restart)
                deadline=time.monotonic()+start_timeout
                while not plain(child_run/'ready.json').exists():
                    if stopped():exit_code=0;break
                    if proc.poll() is not None:raise ValueError('SYNC_WORKER_FAILED_BEFORE_READY')
                    if time.monotonic()>deadline:raise TimeoutError('SYNC_WORKER_READY_TIMEOUT_NO_RESTART')
                    time.sleep(.05)
                else:
                    ready=loads(read(child_run/'ready.json',16384))
                    expected={'schema':'xnby.layer-sync.ready.v2','listen':'127.0.0.1','pid':proc.pid,'creation':process_creation(proc.pid),
                              'port':config['listenPort'],'nativePlatformPort':config['platformPort'],'instanceId':child_run.name,
                              'configSHA256':config_sha,'manifestSHA256':manifest_sha}
                    if proc.poll() is not None or ready!=expected:raise ValueError('SYNC_WORKER_READY_IDENTITY_CHANGED')
                    event('worker-ready',pid=proc.pid,attempt=restart)
                    print(json.dumps({'ready':True,'controllerPID':os.getpid(),'workerPID':proc.pid,'instanceId':instance,'attempt':restart}),flush=True)
                    while proc.poll() is None and not stopped():time.sleep(.1)
                    if stopped():exit_code=0;break
                    code=proc.wait();event('worker-exited',pid=proc.pid,exitCode=code)
                    retire()
                    if code==0 or restart>=max_restarts:raise ValueError('SYNC_WORKER_RECOVERY_EXHAUSTED')
                    restart+=1;event('restart-after-confirmed-exit',attempt=restart)
                    continue
                break
        except KeyboardInterrupt:
            exit_code=0
        except BaseException as error:
            code=str(error) if re.fullmatch('[A-Z0-9_]+',str(error)) else type(error).__name__
            event('controller-error',code=code)
            raise
        finally:
            try:retire()
            finally:
                if job is not None:job.close()
                if pointer.exists() and read(pointer,16384)==record_raw:pointer.unlink()
                write_new(run/'controller-exit.json',encode({'exitCode':exit_code,'restarts':restart,'originalWorkerHandleRetired':proc is None}))
        return exit_code
