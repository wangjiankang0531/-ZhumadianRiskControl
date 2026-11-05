"""Embedded in a new hash-bound core; constants are supplied by the assembler.

This adds one closed R48 contract. Existing contracts and process/file lifecycle
functions remain unchanged. Only the trusted wrapper sets R48_UPDATER_PIN.
"""
def r48_runtime_rows():
    updater=R48_UPDATER_PIN
    require(isinstance(updater,dict)and set(updater)=={'bytes','sha256'}and type(updater['bytes'])is int and updater['bytes']>0 and re.fullmatch('[0-9a-f]{64}',updater['sha256'])is not None,'TRUSTED_R48_WRAPPER_PIN_REQUIRED')
    core={'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__))}
    return {**R48_SUPPORT_ROWS,R48_CORE:core,'tools/original_public_test_update.py':dict(updater)}

def r48_expected_files(previous):
    require(isinstance(previous,dict),'R48_PREVIOUS_PAYLOAD_FILES_REQUIRED')
    result={n:dict(p)for n,p in previous.items()if not n.startswith('frontend/emergency_pc/')}
    result.update(R48_EMERGENCY_ROWS);result.update(R48_HOME_ROWS);result.update(r48_runtime_rows())
    return result

def r48_expected_release(old,payload_sha):
    require(re.fullmatch('[0-9a-f]{64}',payload_sha or '')is not None,'R48_PAYLOAD_HASH_REQUIRED')
    result=json.loads(json.dumps(old))
    result['controllerFiles'].update({n:p['sha256']for n,p in r48_runtime_rows().items()if n.startswith('tools/')})
    result[R38_FRONTEND_FIELD]=R48_FRONTEND_CONTRACT
    result[R45_BOOTSTRAP_FIELD]=R48_BOOTSTRAP_CONTRACT
    result[R46_HOME_FIELD]=R46_HOME_FEATURE
    result['businessSupervisionPdf']=R48_SUPERVISION_DESCRIPTOR
    result[R48_FIELD]=R48_FEATURE
    result.update(payloadManifestSHA256=payload_sha,publicTestRevision=R48_REVISION,publicAccepted=False)
    return result

def r48_bundle_contract(app,bundle,plan,old,release,payload):
    require(release.get(R48_FIELD)==R48_FEATURE,'EXACT_R48_EVENT_RESULT_FEATURE_REQUIRED')
    old_pin=sha(regular(app,'release-manifest.json'))
    require(old_pin in R48_BASES,'EXACT_R45_OR_R47_BASE_REQUIRED')
    accepted=R48_BASES[old_pin]
    require(plan['acceptedOldReleases']=={old_pin:accepted['accepted']}and plan['basePayloadManifestSHA256']==accepted['accepted']['payloadManifestSHA256'],'EXACT_R48_SINGLE_BASE_AND_CONTROLS_REQUIRED')
    require(plan['updateId']=='20261105-r48-event-results-from-'+accepted['label'],'EXACT_R48_VARIANT_ID_REQUIRED')
    mutable={'acceptedOldReleases','basePayloadManifestSHA256','files','newPayloadManifestSHA256','newReleaseSHA256','oldPayloadFiles','removedFrontendFiles','updateId'}
    require(set(plan)==set(R48_PLAN_COMMON)|mutable,'EXACT_R48_PLAN_KEYS_REQUIRED')
    require({n:v for n,v in plan.items()if n not in mutable}==R48_PLAN_COMMON,'ALL_R48_DATA_CALLBACK_IIS_TARGET_AND_PORT_FIELDS_RETAINED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    expected_payload=dict(previous);expected_payload['files']=r48_expected_files(previous['files'])
    require(payload==expected_payload,'ONLY_FULL_EMERGENCY_HOME_AND_SUPERVISION_DELTA_ALLOWED')
    expected_release=r48_expected_release(old,plan['newPayloadManifestSHA256'])
    require(release==expected_release,'ALL_OTHER_R48_RELEASE_IDENTITIES_FEATURES_AND_CONTROLS_RETAINED')
    require(payload['files']['private/server-configuration.json']==previous['files']['private/server-configuration.json'],'R48_PRIVATE_CONFIGURATION_RETAINED')
    changed={n:p for n,p in expected_payload['files'].items()if previous['files'].get(n)!=p}
    expected_writes={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in changed.items()}
    for n in ['payload-manifest.json','release-manifest.json']:
        p=check_file(bundle/'payload',n,plan['newPayloadManifestSHA256']if n=='payload-manifest.json'else plan['newReleaseSHA256'])
        expected_writes[n]={'bytes':p.stat().st_size,'SHA256':sha(p)}
    require(plan['files']==expected_writes,'EXACT_R48_CHANGED_FILES_REQUIRED')
    removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in previous['files'].items()if n.startswith('frontend/emergency_pc/')and n not in expected_payload['files']}
    require(plan['removedFrontendFiles']==removed,'EXACT_RETIRED_EMERGENCY_ONLY_REQUIRED')
    require(plan['oldPayloadFiles']=={n:previous['files'][n]for n in expected_writes if n in previous['files']},'EXACT_R48_CODE_PREIMAGES_REQUIRED')
    # Detect unknown drift before downtime without reading private/data/seed rows.
    for n,p in previous['files'].items():
        if n.startswith(('private/','UserData/','seed/','Assets/')):continue
        check_file(app,n,p['sha256'],p['bytes'])
    for n,p in r48_runtime_rows().items():
        root=bundle/'payload'if n in plan['files']else app
        check_file(root,n,p['sha256'],p['bytes'])
    for n,h in release['controllerFiles'].items():
        root=bundle/'payload'if n in plan['files']else app
        check_file(root,n,h)
    return True
