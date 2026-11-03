"""Fixed static-only R37 contract on the final deployed R36 updater."""
from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
OLD=R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle';D=R/'Document/Deployment/public_test_static_performance_r37_20261103'
if D.exists():assert D.is_dir() and not any(D.iterdir())
else:D.mkdir(parents=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
prior=T/'original_public_test_update_r36_20261103_r2.py';raw=prior.read_bytes();assert sha(raw)=='67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca'
old=json.loads((OLD/'payload/release-manifest.json').read_bytes());assert sha((OLD/'payload/release-manifest.json').read_bytes())=='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'
files={'tools/original_project_branding.py':T/'original_project_branding_r229.py','deploy/iis_original/App_Code/XnbyReferenceProxy.cs':T/'frontend/static_performance_r229/XnbyReferenceProxy.cs','iis/App_Code/XnbyReferenceProxy.cs':T/'frontend/static_performance_r229/XnbyReferenceProxy.cs'}
pins={n:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for n,p in files.items()}
contract={'revision':'gzip-hash-assets-no-store-html-api-v1','files':pins,'onlyPublicStaticGETHEADNegotiatesGzip':True,'encodedResponseBytesPreserved':True,'contentEncodingAndVaryForwarded':True,'successfulHashedAssetsImmutable':True,'htmlBusinessErrorsAndNonHashedResourcesNotLongCached':True,'businessPayloadAuthDatabaseAndPrivateConfigurationUnchanged':True}
base={k:v for k,v in old.items()if k!='payloadManifestSHA256'}
block='\nR37_STATIC_FIELD = "staticInitialLoadPerformance"\nR37_STATIC_CONTRACT = '+repr(contract)+'\nR37_STATIC_BASE_METADATA = '+repr(base)+'\n'
block+='''
def static_performance_declared(release):
    if R37_STATIC_FIELD not in release:return False
    require(release[R37_STATIC_FIELD] == R37_STATIC_CONTRACT, 'R37_EXACT_STATIC_DESCRIPTOR_REQUIRED')
    controls=release['controllerFiles']; updater='tools/original_public_test_update.py'
    expected=dict(R37_STATIC_BASE_METADATA['controllerFiles'])
    expected.update({n:p['sha256'] for n,p in R37_STATIC_CONTRACT['files'].items()})
    expected[updater]=sha(Path(__file__))
    require(controls==expected,'R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED')
    return True

def static_performance_bundle_contract(app,bundle,plan,old,release,payload):
    require(static_performance_declared(release),'R37_EXPLICIT_STATIC_DESCRIPTOR_REQUIRED')
    # The fixed public wrapper additionally pins the exact deployed R36 release SHA.
    # Keeping only the payload manifest pointer variable permits the existing synthetic
    # private-configuration fixture without reading a real credential file.
    require({n:p for n,p in old.items() if n!='payloadManifestSHA256'}==R37_STATIC_BASE_METADATA,'R37_EXACT_R36_RELEASE_METADATA_AND_CONTROLS_REQUIRED')
    require(set(plan['acceptedOldReleases'])=={sha(regular(app,'release-manifest.json'))},'R37_ONLY_ONE_INSTALLED_RELEASE_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    require(payload==previous and release['payloadManifestSHA256']==old['payloadManifestSHA256'],'R37_EVERY_PAYLOAD_ROW_AND_MANIFEST_BYTE_RETAINED')
    mutable={'controllerFiles','publicTestRevision','publicAccepted',R37_STATIC_FIELD}
    require({n:p for n,p in old.items()if n not in mutable}=={n:p for n,p in release.items()if n not in mutable},'R37_ALL_BUSINESS_FRONTEND_AUTH_AND_HISTORY_RELEASE_FIELDS_RETAINED')
    require(release.get('publicAccepted') is False and release.get('publicTestRevision')=='20261103-R37-static-initial-load-performance','R37_EXACT_STATIC_REVISION_REQUIRED')
    proxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs'; actual='iis/App_Code/XnbyReferenceProxy.cs'; updater='tools/original_public_test_update.py'
    require(plan.get('iisProxySHA256')==old['controllerFiles'][proxy],'R37_OLD_IIS_PROXY_PIN_REQUIRED_BEFORE_MUTATION')
    require(plan.get('legacyEntrySHA256')=={actual:[old['controllerFiles'][proxy]]},'R37_ONLY_EXACT_EXISTING_IIS_PROXY_LEGACY_PIN_REQUIRED')
    require(plan.get('oldPayloadFiles')=={} and plan.get('removedFrontendFiles')=={},'R37_NO_BUSINESS_OR_FRONTEND_CHANGE_OR_REMOVAL')
    required=set(R37_STATIC_CONTRACT['files'])|{updater,'release-manifest.json','payload-manifest.json'}
    require(set(plan['files'])==required,'R37_EXACT_SIX_STATIC_INSTALL_PATHS_REQUIRED')
    for n,pin in R37_STATIC_CONTRACT['files'].items():
        require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'R37_EXACT_STATIC_TRANSPORT_PIN_REQUIRED:'+n)
        check_file(bundle/'payload',n,pin['sha256'],pin['bytes'])
    require(plan['files'][updater]=={'bytes':Path(__file__).stat().st_size,'SHA256':sha(Path(__file__))},'R37_EXACT_SELF_UPDATER_REQUIRED')
    return True

'''
s=raw.decode('utf-8');at=s.index('def load_bundle(');s=s[:at]+block+s[at:]
names=['r32_avatar_bundle_contract','risk_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','material_bundle_contract']
f=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='load_bundle')
calls=[n for n in f.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id in names]
assert [n.value.func.id for n in calls]==names
lines=s.splitlines(keepends=True);oldcalls=''.join(lines[calls[0].lineno-1:calls[-1].end_lineno]);assert s.count(oldcalls)==1
newcalls="    if R37_STATIC_FIELD in release:\n        static_performance_bundle_contract(app,bundle,plan,old,release,payload)\n    else:\n"+'\n\n'.join('        '+x+'(app, bundle, plan, old, release, payload)' for x in ['r32_avatar_bundle_contract','risk_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','material_bundle_contract'])
s=s.replace(oldcalls,newcalls+'\n')
# Set the receipt from actual successful file replacement; IIS mapping is unchanged.
needle="        report['codeApplied'] = True";assert s.count(needle)==1
s=s.replace(needle,needle+"\n\n        report['iisChanged'] = static_performance_declared(read(app / 'release-manifest.json'))")
func=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(t).body if isinstance(n,ast.FunctionDef)}
a,b=func(raw.decode()),func(s);changed={n for n in a if a[n]!=b[n]};assert changed=={'load_bundle','apply_update'}
# The only lifecycle-function difference is accurate reporting after replacement.
q=func(s.replace("\n\n        report['iisChanged'] = static_performance_declared(read(app / 'release-manifest.json'))",''));assert q['apply_update']==a['apply_update']
target=T/'original_public_test_update_r37_static_20261103.py';assert not target.exists();target.write_bytes(s.encode())
result={'prepared':True,'priorUpdaterSHA256':sha(raw),'newUpdaterSHA256':sha(target.read_bytes()),'onlyExistingFunctionsChanged':sorted(changed),'applyUpdateOnlyAdditionalAccurateIISReceiptAssignment':True,'allNormalStopLaunchAndBackupReplaceRestoreRecoveryASTIdentical':True,'staticContract':contract,'finalPackageOrFullPreflightOrActualLifecyclePassed':False,'publicDeployed':False}
(D/'updater-preparation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k!='staticContract'}))
