"""Read-only R4 observation for independent fixtures, with creation-time proof of PID reuse.

The fixed installation package and its strict observer are unchanged. No process is
started, stopped, signalled, or modified here. A live reused PID is accepted only
when its creation is later than the authoritative normal-shutdown receipt.
"""
from pathlib import Path
import ctypes,datetime,hashlib,json
from ctypes import wintypes
from original_r4_apply_baseline import R,Q,RELEASE,validate
from original_task_identity_authority import listener_owner,process_identity

LAST_PID_REUSE_PROOF=[]
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def process_observation(handle):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    query=kernel.GetExitCodeProcess;query.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];query.restype=wintypes.BOOL
    def exit_code():
        value=wintypes.DWORD();assert query(handle,ctypes.byref(value)),'KERNEL_PROCESS_EXIT_QUERY_REQUIRED'
        return int(value.value)
    code=exit_code()
    if code!=259:return {'running':False,'exitCode':code,'kernelConfirmedExited':True}
    try:image,created_ms=process_identity(handle)
    except RuntimeError:
        code=exit_code()
        if code!=259:return {'running':False,'exitCode':code,'kernelConfirmedExited':True}
        raise
    code=exit_code()
    if code!=259:return {'running':False,'exitCode':code,'kernelConfirmedExited':True}
    return {'running':True,'image':str(image),'creationUnixMilliseconds':created_ms}

def observe():
    global LAST_PID_REUSE_PROOF
    strict=R/'Application/tools/original_r4_stopped_observation.py'
    assert sha(strict)=='55ae360e1c4da440b5d043a7ef9eb0ee5184d5b9df929fe5ed5760378ecfd119','FIXED_STRICT_OBSERVER_CHANGED'
    spec_path=R/'Document/Deployment/emergency_plan_report_20261030/current-local-candidate.json'
    spec=read(spec_path);pw=R/'work/emergency_plan_report_20261030'
    life=Path(spec['lifecycle']).resolve(strict=True);bundle=Path(spec['bundle']).resolve(strict=True)
    if not life.is_relative_to(pw) or not bundle.is_relative_to(pw):raise ValueError('ORIGINAL_R4_LOCAL_POINTER_REQUIRED')
    result=read(life/'result.json');build=read(bundle/'build-result.json')
    state_path=Q/'UserData/OriginalServer/current-run.json';state_pin=sha(state_path);state=read(state_path)
    receipt_path=Path(state['run'])/'receipt.json';receipt_pin=sha(receipt_path);receipt=read(receipt_path)
    assert result['runtimeReady'] and result['legacyProjectionUnchanged']
    assert result['controllerPID']==state['controllerPID']==receipt['controllerPID'] and result['run']==state['run']
    assert spec['releaseSHA256']==result['releaseSHA256']==build['newReleaseSHA256']==sha(Q/'release-manifest.json')==RELEASE
    assert sha(bundle/'update-manifest.json')==build['manifestSHA256']
    assert receipt['allOwnedChildrenExited'] and receipt['normalOwnedShutdown'] and not receipt['forcedJobClosureComponents']
    assert receipt['failureType']=='PermissionError' and set(receipt['exitCodesBeforeJobClose'])==set(state['children']) and set(receipt['exitCodesBeforeJobClose'].values())=={0}
    ended=datetime.datetime.fromisoformat(receipt['endedAt']);assert ended.tzinfo is not None
    ended_ms=int(ended.timestamp()*1000)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE;kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    reused=[]
    for pid in [state['controllerPID'],*state['children'].values()]:
        handle=kernel.OpenProcess(0x1000,False,pid)
        if handle:
            try:
                witness=process_observation(handle)
                if not witness['running']:
                    reused.append({'pid':pid,'kernelConfirmedExited':True,'exitCode':witness['exitCode']})
                    continue
                image,created_ms=Path(witness['image']),witness['creationUnixMilliseconds']
                assert isinstance(created_ms,int) and created_ms>ended_ms,'ORIGINAL_PROCESS_IDENTITY_STILL_PRESENT_OR_UNPROVEN'
                reused.append({'pid':pid,'currentImageName':image.name,'currentCreationUnixMilliseconds':created_ms,'originalNormalShutdownUnixMilliseconds':ended_ms,'newCreationAfterOriginalShutdown':True})
            finally:kernel.CloseHandle(handle)
        else:assert ctypes.get_last_error()==87,'STOPPED_PROCESS_IDENTITY_UNPROVEN'
    assert listener_owner(18891)==[],'LOCAL_GATEWAY_PORT_NOT_FREE'
    release=read(Q/'release-manifest.json')
    for name,pin in release['controllerFiles'].items():assert sha(Q/name)==pin
    assert sha(Q/'payload-manifest.json')==release['payloadManifestSHA256']
    approved=read(pw/'lifecycle-emergency-modules-r4/prepared.private.json');pins={p:sha(p) for p in approved['dataIdentityPins']}
    value={'currentBS':Path(state['run']).name,'controllerPID':state['controllerPID'],'releaseSHA256':RELEASE,'databaseUUID':state['databaseUUID'],'runtimeReadyNow':False,'allOwnedChildrenNormallyExited':True}
    assert sha(state_path)==state_pin and sha(receipt_path)==receipt_pin,'ORIGINAL_RUNTIME_METADATA_CHANGED_DURING_OBSERVATION'
    answer=validate(value,approved,pins);LAST_PID_REUSE_PROOF=reused;return answer
