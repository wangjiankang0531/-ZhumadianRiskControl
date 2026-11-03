from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/addsign-history-r180/production-module-r199-r2';D=R/'Document/Deployment/public_test_native_history_r36_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r99/result.json')['allPassed']and J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r102/result.json')['allPassed']
source=W/'original_public_test_update.py';s=source.read_text(encoding='utf-8');before=s
def once(text,a,b):
 assert text.count(a)==1,(a,text.count(a));return text.replace(a,b)
contract='''def history_bundle_contract(app,bundle,plan,old,release,payload):
    require(history_declared(release),'EXACT_NATIVE_HISTORY_EXTENSION_REQUIRED')
    require(R36_HISTORY_FIELD not in old and old.get(R35_PERSONAL_FIELD)==R35_PERSONAL_CONTRACT,'HISTORY_REQUIRES_EXACT_R35_BASE')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    require(native_default_declared(old,previous) and old.get(R23_ASYNC_FIELD)==R23_ASYNC_CONTRACT,'HISTORY_RETAINS_ORIGINAL_NATIVE_AUTH_AND_ASYNC')
    for role,expected in R35_PERSONAL_CONTRACT['frontends'].items():
        require(r32_frontend_manifest(previous['files'],role)==expected and r32_frontend_manifest(payload['files'],role)==expected,'HISTORY_KEEPS_BOTH_R35_FRONTENDS')
    control='tools/original_public_test_update.py';newrows=R36_HISTORY_CONTRACT['files']
    require(old['controllerFiles'].get(control)==R36_OLD_UPDATER_SHA and old['controllerFiles'].get(R23_CONTROLLER)==R27_POOL_PINS[R23_CONTROLLER]['sha256'] and R36_HISTORY_HELPER not in old['controllerFiles'],'HISTORY_EXACT_OLD_CONTROLLER_SOURCES_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))} and plan.get('legacyEntrySHA256')=={} and plan.get('removedFrontendFiles')=={},'HISTORY_ONE_INSTALLED_BASE_NO_LEGACY_OR_ASSET_REMOVALS')
    require(not set(newrows).intersection(previous['files']),'HISTORY_NEW_PATHS_MUST_BE_ABSENT')
    require({n:p for n,p in payload['files'].items()if n not in newrows}==previous['files'],'HISTORY_ALL_PRIOR_PAYLOAD_BYTES_KEPT')
    require(all(payload['files'].get(n)==p for n,p in newrows.items()),'EXACT_HISTORY_PAYLOAD_PINS_REQUIRED')
    changed_controls={R23_CONTROLLER,R36_HISTORY_HELPER,control}
    require(set(release['controllerFiles'])==set(old['controllerFiles'])|{R36_HISTORY_HELPER} and {n:p for n,p in old['controllerFiles'].items()if n not in changed_controls}=={n:p for n,p in release['controllerFiles'].items()if n not in changed_controls},'HISTORY_RETAINS_OTHER_18_CONTROLS')
    require(release['controllerFiles'][control]==sha(Path(__file__)),'EXACT_HISTORY_UPDATER_REQUIRED')
    mutable={'payloadManifestSHA256','controllerFiles','publicTestRevision','publicAccepted',R36_HISTORY_FIELD}
    require({n:p for n,p in old.items()if n not in mutable}=={n:p for n,p in release.items()if n not in mutable} and release.get('publicAccepted')is False,'HISTORY_ALL_PRIOR_RELEASE_CONTRACTS_KEPT')
    required={**newrows,R23_CONTROLLER:R36_HISTORY_CONTROLLER_PIN,R36_HISTORY_HELPER:{'sha256':R36_HISTORY_HELPER_SHA},control:{'sha256':sha(Path(__file__))}}
    require(set(plan['files'])==set(required)|{'payload-manifest.json','release-manifest.json'} and plan['oldPayloadFiles']=={},'EXACT_SEVEN_HISTORY_TRANSPORT_PATHS_REQUIRED')
    for name,pin in required.items():
        actual=plan['files'][name];require(actual['SHA256']==pin['sha256']and('bytes'not in pin or actual['bytes']==pin['bytes']),'EXACT_HISTORY_TRANSPORT_PIN:'+name)
        check_file(bundle/'payload',name,pin['sha256'],pin.get('bytes'))
    return True

'''
old=T/'original_public_test_update_r35_20261103.py';assert sha(old)=='e8f0d69d4db3494139b293631ddf3c58ba07d98557772d0e6de17c35995c2d23'
s=once(s,'def history_declared(release):','R36_OLD_UPDATER_SHA = '+repr(sha(old))+'\n\n'+contract+'def history_declared(release):')
segments={n.name:ast.get_source_segment(s,n)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
for name in ['r32_avatar_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','team_bundle_contract','material_bundle_contract']:
 segment=segments[name];changed=segment
 if name=='r32_avatar_bundle_contract':changed=once(changed,segment.splitlines()[0]+'\n',segment.splitlines()[0]+'\n    if R36_HISTORY_FIELD in release or R36_HISTORY_FIELD in old:\n        return history_bundle_contract(app,bundle,plan,old,release,payload)\n')
 if name=='runtime_pool_bundle_contract':
  changed=once(changed,"allowed=set(R27_POOL_PINS)|{'tools/original_public_test_update.py'}","allowed=set(R27_POOL_PINS)|{'tools/original_public_test_update.py'}|({R36_HISTORY_HELPER}if history_declared(release)else set())")
  changed=once(changed,"and n not in allowed_native}","and n not in allowed_native and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files'])}")
  changed=once(changed,"for n,pin in R27_POOL_PINS.items():","for n,pin in pool_control_pins(release).items():")
 if name in ['team_bundle_contract','material_bundle_contract']:
  if name=='team_bundle_contract':changed=once(changed,"and n not in R26_TEAM_ROWS and not (native_default_declared", "and n not in R26_TEAM_ROWS and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files']) and not (native_default_declared")
  else:changed=once(changed,"and n not in R25_MATERIAL_ROWS and not (team", "and n not in R25_MATERIAL_ROWS and not(history_declared(release)and n in R36_HISTORY_CONTRACT['files']) and not (team")
  anchor="    legal.update(n for n in payload['files'] if r32_frontend_scope(n, release, payload))"
  changed=once(changed,anchor,anchor+"\n    if history_declared(release):legal.update(R36_HISTORY_CONTRACT['files']);legal.add(R36_HISTORY_HELPER)")
 if name=='async_bundle_contract':
  anchor="    if workflow:\n";changed=once(changed,anchor,"    if history_declared(release):expected[R36_HISTORY_HELPER]=R36_HISTORY_HELPER_SHA\n\n"+anchor)
  changed=once(changed,"old[R23_ASYNC_FIELD] == R23_ASYNC_CONTRACT and set(controls) == set(prior)","old[R23_ASYNC_FIELD] == R23_ASYNC_CONTRACT and set(controls) == set(prior)|({R36_HISTORY_HELPER}if history_declared(release)else set())")
 assert changed!=segment;s=once(s,segment,changed)
ast.parse(s);functions=lambda text:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
a,b=functions(before),functions(s);assert {n for n in a if a[n]!=b[n]}=={'r32_avatar_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','team_bundle_contract','material_bundle_contract'}
for n in ['health','history_ready','normal_stop','launch','backup_code','replace_code','restore_code','apply_update','recover_pending','rollback_latest']:assert a[n]==b[n]
target=T/'original_public_test_update_r36_20261103.py';assert not target.exists()and not D.exists();target.write_text(s,encoding='utf-8');D.mkdir()
proof={'sourceSHA256':sha(target),'baseTestedRuntimeUpdaterSHA256':sha(source),'onlyFiveCompositionFunctionsChangedRelativeToActualNativeR199AndR204':True,'newCompositionFunction':'history_bundle_contract','allHealthHistoryReadyNormalStopLaunchBackupRestoreRecoveryASTIdenticalToActualTestedRuntime':True,'oldR35UpdaterSHA256':sha(old),'publicUploadedOrInstalled':False}
(D/'updater-source-comparison.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
