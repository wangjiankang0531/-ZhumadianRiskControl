from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';old=T/'original_public_test_update_r24_20261101.py';out=T/'original_public_test_update_r25_20261101.py';assert not out.exists()
assert hashlib.sha256(old.read_bytes()).hexdigest()=='4931c7fbb58880f228423f8324d3b40cb22e500bc299f053a8fe455a742c7878'
classes=json.loads((R/'work/event_delivery_consistency_20261030/full-controller-r128/material-excel-candidate-r1/candidate.json').read_bytes())['classFiles']
rows={'payload/business/run-template/classes/'+n:p for n,p in classes.items()};assert len(rows)==3
block='R25_MATERIAL_FIELD = "materialExcelFileTransaction"\nR25_MATERIAL_ROWS = '+repr(rows)+'\nR25_MATERIAL_CONTRACT = {"revision": "original-whole-file-material-import-v1", "classes": R25_MATERIAL_ROWS}\n\n'
block+='''def material_declared(release, payload):
    present = set(R25_MATERIAL_ROWS).intersection(payload['files'])
    require({n for n in payload['files'] if n.startswith('payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport')}
            <= set(R25_MATERIAL_ROWS), 'UNDECLARED_MATERIAL_HELPER_REFUSED')
    if R25_MATERIAL_FIELD not in release:
        require(not present, 'EXPLICIT_MATERIAL_TRANSACTION_DESCRIPTOR_REQUIRED')
        return False
    require(release[R25_MATERIAL_FIELD] == R25_MATERIAL_CONTRACT,
            'EXACT_MATERIAL_TRANSACTION_DESCRIPTOR_REQUIRED')
    require(all(payload['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),
            'EXACT_MATERIAL_TRANSACTION_CLASS_PINS_REQUIRED')
    require(release.get(R24_WORKFLOW_FIELD) == R24_WORKFLOW_CONTRACT
            and release.get(R23_ASYNC_FIELD) == R23_ASYNC_CONTRACT,
            'MATERIAL_TRANSACTION_REQUIRES_RETAINED_WORKFLOW_AND_ASYNC')
    return True


def material_bundle_contract(app, bundle, plan, old, release, payload):
    if not material_declared(release, payload):
        require(not set(R25_MATERIAL_ROWS).intersection(plan['files']),
                'MATERIAL_CODE_WITHOUT_DECLARATION_REFUSED')
        return False
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R25_MATERIAL_ROWS)
    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))
    require(set(plan['files']) <= legal, 'MATERIAL_UPDATE_TRANSPORT_SCOPE_REFUSED')
    obsolete = {n for n in previous['files'] if n.startswith('frontend/emergency_pc/') and n not in payload['files']}
    require(set(plan.get('removedFrontendFiles', {})) == obsolete,
            'EXACT_OBSOLETE_EMERGENCY_ASSET_REMOVALS_REQUIRED')
    fresh = R25_MATERIAL_FIELD not in old
    if fresh:
        require(not set(R25_MATERIAL_ROWS).intersection(previous['files'])
                and set(R25_MATERIAL_ROWS).issubset(plan['files']),
                'COMPLETE_FRESH_MATERIAL_TRANSACTION_TRANSPORT_REQUIRED')
    else:
        require(old[R25_MATERIAL_FIELD] == R25_MATERIAL_CONTRACT
                and all(previous['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),
                'EXACT_RETAINED_MATERIAL_TRANSACTION_REQUIRED')
    # This fixed extension changes only emergency assets and the three exact material classes.
    retained = lambda files: {n: p for n, p in files.items()
        if not n.startswith('frontend/emergency_pc/') and n not in R25_MATERIAL_ROWS}
    require(retained(previous['files']) == retained(payload['files']),
            'MATERIAL_UPDATE_OTHER_PAYLOAD_BYTES_MUST_BE_RETAINED')
    require(all(n.startswith('frontend/emergency_pc/') for n in plan.get('removedFrontendFiles', {})),
            'MATERIAL_UPDATE_ONLY_OBSOLETE_EMERGENCY_ASSETS_REMOVED')
    for name, pin in R25_MATERIAL_ROWS.items():
        if name in plan['files']:
            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},
                    'EXACT_MATERIAL_TRANSACTION_TRANSPORT_PIN_REQUIRED:' + name)
        check_file(bundle / 'payload' if name in plan['files'] else app,
                   name, pin['sha256'], pin['bytes'])
    return True


def material_ready(app, row):
    release = read(regular(app, 'release-manifest.json'))
    payload = read(check_file(app, 'payload-manifest.json', release['payloadManifestSHA256']))
    if not material_declared(release, payload):
        return None
    require(workflow_ready(app, row) is not None, 'MATERIAL_RUNTIME_OWNED_WORKFLOW_REQUIRED')
    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())
    business = regular(run, 'b')
    for name, pin in R25_MATERIAL_ROWS.items():
        check_file(app, name, pin['sha256'], pin['bytes'])
        check_file(business, name.removeprefix('payload/business/run-template/'),
                   pin['sha256'], pin['bytes'])
    return {'threeMaterialRuntimeClassesBytePinned': True,
            'businessRecordsAccountsSessionsOrCredentialsRead': False}


'''
s=old.read_text(encoding='utf-8');anchor='def workflow_declared(release, payload):';assert s.count(anchor)==1;s=s.replace(anchor,block+anchor)
a="or name == R24_TASK_CLASS or name in (";assert s.count(a)==1;s=s.replace(a,"or name == R24_TASK_CLASS or name in R25_MATERIAL_ROWS or name in (")
a='    async_bundle_contract(app, bundle, plan, old, release, payload)';assert s.count(a)==1;s=s.replace(a,a+'\n    material_bundle_contract(app, bundle, plan, old, release, payload)')
a='    workflow_ready(app, row)\n\ndef installed_overlay';assert s.count(a)==1;s=s.replace(a,'    workflow_ready(app, row)\n    material_ready(app, row)\n\ndef installed_overlay')
def defs(text):return{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=defs(old.read_text(encoding='utf-8'));b=defs(s);assert{k for k in a if a[k]!=b[k]}=={'load_bundle','health'}and set(b)-set(a)=={'material_declared','material_bundle_contract','material_ready'}
out.write_text(s,encoding='utf-8');print(json.dumps({'newUpdater':str(out),'changedOriginalFunctions':['load_bundle','health'],'stopBackupReplaceRestoreASTUnchanged':True,'exactMaterialClasses':3,'publicOrPreviewChanged':False}))
