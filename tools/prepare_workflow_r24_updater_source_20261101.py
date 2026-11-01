from pathlib import Path
import ast, hashlib, json

R=Path('D:/Project/Zhumadian'); T=R/'Application/tools'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
base=(T/'original_public_test_update_r23_graceful_20261101.py').read_bytes()
assert sha(base)=='d500b5b591971532a74dd632d2cff7139474bd61986c01bc75b184017c143d41'
text=base.decode('utf-8')
parameter=(T/'server-runtime-temp-r2/original_server_release_parameters.py').read_bytes()
assert len(parameter)==11055 and sha(parameter)=='caf82f852f3ab80d66378869b09497f21f2965975364394579351a4bfda14bc9'
addition='''R24_WORKFLOW_FIELD = 'nativeTaskGuardAndTemporaryLayout'
R24_TASK_CLASS = 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'
R24_PARAMETER = 'tools/original_server_release_parameters.py'
R24_OLD_PARAMETER_SHA = '8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9'
R24_TASK_PIN = {'bytes': 8543, 'sha256': '9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}
R24_PARAMETER_PIN = {'bytes': 11055, 'sha256': 'caf82f852f3ab80d66378869b09497f21f2965975364394579351a4bfda14bc9'}
R24_WORKFLOW_CONTRACT = {'revision': 'original-task-nonempty-flow-and-short-temporary-v1',
    'taskController': dict(path=R24_TASK_CLASS, **R24_TASK_PIN),
    'parameterAdapter': dict(path=R24_PARAMETER, **R24_PARAMETER_PIN)}


def workflow_declared(release, payload):
    if R24_WORKFLOW_FIELD not in release:
        require(R24_TASK_CLASS not in payload['files']
                and release['controllerFiles'].get(R24_PARAMETER) != R24_PARAMETER_PIN['sha256'],
                'EXPLICIT_WORKFLOW_GUARD_EXTENSION_REQUIRED')
        return False
    require(release[R24_WORKFLOW_FIELD] == R24_WORKFLOW_CONTRACT,
            'EXACT_WORKFLOW_GUARD_DESCRIPTOR_REQUIRED')
    require(release.get(R23_ASYNC_FIELD) == R23_ASYNC_CONTRACT,
            'WORKFLOW_GUARD_REQUIRES_COMPLETE_ASYNC_EXTENSION')
    require(payload['files'].get(R24_TASK_CLASS) == R24_TASK_PIN
            and release['controllerFiles'].get(R24_PARAMETER) == R24_PARAMETER_PIN['sha256'],
            'EXACT_WORKFLOW_GUARD_PAYLOAD_AND_PARAMETER_REQUIRED')
    return True


def workflow_bundle_contract(app, bundle, plan, old, release, payload):
    if not workflow_declared(release, payload):
        require(R24_TASK_CLASS not in plan['files'], 'WORKFLOW_CLASS_WITHOUT_DECLARATION_REFUSED')
        return False
    fresh = R24_WORKFLOW_FIELD not in old
    if fresh:
        require(old['controllerFiles'].get(R24_PARAMETER) == R24_OLD_PARAMETER_SHA,
                'EXACT_ORIGINAL_PARAMETER_ADAPTER_REQUIRED')
        require({R24_TASK_CLASS, R24_PARAMETER}.issubset(plan['files']),
                'COMPLETE_WORKFLOW_GUARD_TRANSPORT_REQUIRED')
    else:
        require(old[R24_WORKFLOW_FIELD] == R24_WORKFLOW_CONTRACT
                and old['controllerFiles'].get(R24_PARAMETER) == R24_PARAMETER_PIN['sha256'],
                'EXACT_RETAINED_WORKFLOW_GUARD_REQUIRED')
    for name, pin in ((R24_TASK_CLASS, R24_TASK_PIN), (R24_PARAMETER, R24_PARAMETER_PIN)):
        if name in plan['files']:
            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},
                    'EXACT_WORKFLOW_GUARD_TRANSPORT_PIN_REQUIRED:' + name)
        check_file(bundle / 'payload' if name in plan['files'] else app,
                   name, pin['sha256'], pin['bytes'])
    return True


def workflow_ready(app, row):
    release = read(regular(app, 'release-manifest.json'))
    payload_path = check_file(app, 'payload-manifest.json', release['payloadManifestSHA256'])
    if not workflow_declared(release, read(payload_path)):
        return None
    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())
    require(run.parent == app / 'UserData/OriginalServer/runs'
            and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None,
            'OWNED_WORKFLOW_GUARD_RUN_REQUIRED')
    business = regular(run, 'b')
    owner = marker(regular(business, 'server-owner.properties'))
    require(owner == {'schema': 'zhumadian.original.server.owner.v1', 'ownerId': row['ownerId']},
            'EXACT_WORKFLOW_GUARD_RUNTIME_OWNER_REQUIRED')
    check_file(app, R24_TASK_CLASS, R24_TASK_PIN['sha256'], R24_TASK_PIN['bytes'])
    check_file(app, R24_PARAMETER, R24_PARAMETER_PIN['sha256'], R24_PARAMETER_PIN['bytes'])
    check_file(business, R24_TASK_CLASS.removeprefix('payload/business/run-template/'),
               R24_TASK_PIN['sha256'], R24_TASK_PIN['bytes'])
    return {'taskControllerPinned': True, 'parameterAdapterPinned': True}


'''
def replace(before,after):
    global text
    assert text.count(before)==1,(before,text.count(before))
    text=text.replace(before,after)
replace('def sha(path):\n',addition+'def sha(path):\n')
replace(') or name in R23_ASYNC_ROWS or name in (',') or name in R23_ASYNC_ROWS or name == R24_TASK_CLASS or name in (')
replace('    if not async_declared(release, payload):\n        require(not set(R23_ASYNC_ROWS).intersection(plan',
        '    workflow = workflow_bundle_contract(app, bundle, plan, old, release, payload)\n    if not async_declared(release, payload):\n        require(not set(R23_ASYNC_ROWS).intersection(plan')
replace("                updater: sha(Path(__file__))}\n    require(all(controls", "                updater: sha(Path(__file__))}\n    if workflow:\n        expected[R24_PARAMETER] = R24_PARAMETER_PIN['sha256']\n    require(all(controls")
replace('    async_ready(app, row)\n\ndef installed_overlay', '    async_ready(app, row)\n    workflow_ready(app, row)\n\ndef installed_overlay')
ast.parse(text)
defs=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(base.decode()),defs(text)
assert {k for k in a if a[k]!=b[k]}=={'load_bundle','async_bundle_contract','health'}
assert set(b)-set(a)=={'workflow_declared','workflow_bundle_contract','workflow_ready'}
out=T/'original_public_test_update_r24_20261101.py'
assert not out.exists();out.write_bytes(text.encode())
print(json.dumps({'source':str(out),'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,
    'existingChangedFunctions':['load_bundle','async_bundle_contract','health'],
    'originalStopBackupReplaceRestoreFunctionsUnchanged':True}))
