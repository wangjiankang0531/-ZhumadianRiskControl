"""Prepare, but never install, the exact R48 static-control bridge repair."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import shutil
import zipfile

V=Path(__file__).resolve().parent
D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_event_write_results_r48_20261105/delivery')
OUT=V/'static-control-bridge-r1046'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    original=D/'r48_update_runtime.py'
    assert digest(original)=='43d3096f73f766e6500da330868d63ba13a869b9e075cfa0092e27ee511ecfa7'
    module=load('original_r48_bridge_failure_r1046',original)
    original_runtime=module.runtime()
    with zipfile.ZipFile(D/'Zhumadian_Event_Write_Results_20261105_R48.zip')as archive:
        release=json.loads(archive.read('payload/release-manifest.json'))
    try:original_runtime.static_performance_declared(copy.deepcopy(release))
    except ValueError as exc:
        assert str(exc)=='R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED'
    else:raise AssertionError('ORIGINAL_PRODUCTION_FAILURE_NOT_REPRODUCED')
    text=original.read_text(encoding='utf-8-sig')
    capture='original_preflight=m.candidate_runtime_pool_preflight'
    assert text.count(capture)==1
    text=text.replace(capture,capture+';original_static=m.static_performance_declared')
    marker='    def staged_helper(app,bundle,plan,release):'
    addition='''    def static(release):
        if R48_EVENT_FIELD not in release:return original_static(release)
        need(declared(release),'EXACT_R48_SUPERVISION_REQUIRED_FOR_STATIC_CONTROLS')
        need(release.get(m.R37_STATIC_FIELD)==m.R37_STATIC_CONTRACT,'EXACT_RETAINED_STATIC_DESCRIPTOR_REQUIRED')
        expected=dict(m.R37_STATIC_BASE_METADATA['controllerFiles'])
        expected.update({n:p['sha256']for n,p in m.R37_STATIC_CONTRACT['files'].items()})
        expected[UPDATER]=digest(HERE)
        if m.original_mapper_defaults_declared(release):expected[m.R24_PARAMETER]=m.R38_PARAMETER_PIN['sha256']
        expected.update({n:p['sha256']for n,p in PINS.items()if n.startswith('tools/')})
        need(release.get('controllerFiles')==expected,'EXACT_COMPOSED_R48_STATIC_AND_ALL_CONTROL_PINS_REQUIRED')
        return True
'''
    assert text.count(marker)==1
    text=text.replace(marker,addition+marker)
    needle="        need(result is not None,'RETAINED_BOUNDED_POOL_PREFLIGHT_REQUIRED')"
    assert text.count(needle)==1
    text=text.replace(needle,needle+"\n        static(release) # Validate the same post-replacement control contract before downtime.")
    needle='    m.load_bundle=outer_load;m.candidate_runtime_pool_preflight=preflight;m.health=health'
    assert text.count(needle)==1
    text=text.replace(needle,needle+';m.static_performance_declared=static')
    ast.parse(text)
    OUT.mkdir(exist_ok=False)
    target=OUT/'r48_update_runtime.py'
    target.write_text(text,encoding='utf-8',newline='\n')
    shutil.copyfile(D/'original_public_test_base_r46.py',OUT/'original_public_test_base_r46.py')
    assert digest(OUT/'original_public_test_base_r46.py')==module.CORE_SHA
    patched=load('repaired_r48_bridge_r1046',target)
    runtime=patched.runtime()
    candidate=copy.deepcopy(release)
    candidate['controllerFiles'][patched.UPDATER]=digest(target)
    assert runtime.static_performance_declared(candidate)is True
    checks=[{'case':'exact-original-public-failure-reproduced','passed':True},
        {'case':'complete-24-control-map-accepted-with-candidate-self-pin','passed':True}]
    def reject(label,alter):
        value=copy.deepcopy(candidate)
        alter(value)
        try:runtime.static_performance_declared(value)
        except ValueError:checks.append({'case':label,'passed':True})
        else:raise AssertionError('UNEXPECTED_ACCEPT:'+label)
    for name in candidate['controllerFiles']:
        reject('control-byte-drift:'+name,lambda value,n=name:value['controllerFiles'].__setitem__(n,'0'*64))
        reject('control-removed:'+name,lambda value,n=name:value['controllerFiles'].pop(n))
    reject('extra-unapproved-control',lambda value:value['controllerFiles'].__setitem__('tools/unknown.py','0'*64))
    reject('static-descriptor-missing',lambda value:value.pop(runtime.R37_STATIC_FIELD))
    reject('static-descriptor-drift',lambda value:value[runtime.R37_STATIC_FIELD].__setitem__('revision','changed'))
    reject('supervision-descriptor-drift',lambda value:value[patched.FIELD].__setitem__('sha256','0'*64))
    reject('release-event-feature-drift',lambda value:value[patched.R48_EVENT_FIELD].__setitem__('normalSaveRequiresCode0AndTrue',False))
    # The frozen lifecycle is deliberately retained byte-for-byte. It will now
    # call the same bridge that candidate preflight exercises before shutdown.
    assert runtime.apply_update.__code__.co_code==original_runtime.apply_update.__code__.co_code
    assert runtime.recover_pending.__code__.co_code==original_runtime.recover_pending.__code__.co_code
    assert runtime.normal_stop.__code__.co_code==original_runtime.normal_stop.__code__.co_code
    report={'passed':True,'focusedChecks':len(checks),'checks':checks,
        'candidateRuntimeSHA256':digest(target),'originalRuntimeSHA256':digest(original),
        'frozenCoreUnchanged':True,'all24ControlPinsExactNotSubset':True,
        'staticBridgeUsedBothBeforeShutdownAndAfterReplacement':True,
        'normalStopApplyAndRecoveryFunctionBodiesRetained':True,
        'actualApplyUpdateSixComponentLifecycleTestPerformed':False,
        'serverFilesChanged':False,'publicDeploymentPerformed':False,
        'fixedR48PackageChanged':False,'fullCloneReady':False}
    (OUT/'focused-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items()if k!='checks'},ensure_ascii=False))

if __name__=='__main__':main()
