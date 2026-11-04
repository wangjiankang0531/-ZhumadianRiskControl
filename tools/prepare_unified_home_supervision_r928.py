"""Prepare one exact R45 -> home assets + factory-registered PDF extension.

Retain the byte-identical R46 core and its complete original sparse validator.
The extension changes only declared controller/module/helper/core/updater pins.
No installed application, database, desktop or public host is changed.
"""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
B=R/'work/home-sparse-r914/bundle';D=R/'Document/Deployment/unified_home_supervision_r928_20261104';O=R/'work/unified-home-supervision-r928/bundle'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert not D.exists()and not O.exists()
base_release=J(B/'payload/release-manifest.json');base_payload=J(B/'payload/payload-manifest.json');base_plan=J(B/'update-manifest.json')
assert sha(B/'update-manifest.json')=='387e7f3d425b99b90561332e7a13a9546f1bdb11c8792babdaa60fdcf4c60388'
assert J(R/'Document/Deployment/public_test_home_transfer_r46_20261104/verified-transport-r917.json')['passed']
full=J(R/'Document/Deployment/supervision_current_full_r920_20261104/full-source-and-restore-plan.private.json')
assert full['onlyThreeSupervisionProgramChangesOverHomeR905']and full['privateConfigurationNotChanged']
core=V/'original_public_test_base_r46.py';assert not core.exists();core.write_bytes((V/'original_public_test_update_home_r46_r914.py').read_bytes())
assert sha(core)=='83244ea13218416b062285c44c01e925b95249243b3691543d6475e69b461251'
names=['tools/serve_original_server_release.py','tools/original_supervision_release_support.py','payload/business/run-template/own-supervision-pdf.jar']
sources={n:Path(full['sources'][n]['source'])for n in names};sources['tools/original_public_test_base_r46.py']=core
pins={n:{'bytes':p.stat().st_size,'sha256':sha(p)}for n,p in sources.items()}
for n in names:assert pins[n]=={k:full['sources'][n][k]for k in ['bytes','sha256']}
helper=sources[names[1]];s=importlib.util.spec_from_file_location('factory_descriptor_r928',helper);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
text=(A/'tools/public_supervision_runtime_r552.py.in').read_text('utf8')
for a,b in [('R42','R46'),('r42','r46'),('R43','R47'),('r43','r47')]:text=text.replace(a,b)
oldcore='5e63e0f3e1f7d1064b5ae1276bfee56d51ce58b0e0ea64f59e30238c1c2d8b30';assert text.count(oldcore)==1;text=text.replace(oldcore,sha(core))
metadata={k:v for k,v in base_release.items()if k!='payloadManifestSHA256'}
text=text.replace('__PARENT_META_SHA__',hashlib.sha256(canonical(metadata)).hexdigest()).replace('__SUPERVISION_PINS__',repr(pins)).replace('__SUPERVISION_DESCRIPTOR__',repr(h.CONTRACT))
text=text.replace("'20261104-R47-supervision-over-frozen-R46'","'20261104-R47-home-and-factory-supervision-over-frozen-R46'")
needle="r'20261104-r47-supervision-from-r(?:36|37)'";assert text.count(needle)==1;text=text.replace(needle,"r'20261104-r47-home-supervision-from-r45'")
assert '__SUPERVISION_'not in text and '__PARENT_'not in text;ast.parse(text)
runtime=V/'original_public_test_home_supervision_r47_r928.py';assert not runtime.exists();runtime.write_text(text,encoding='utf8',newline='\n')
s=importlib.util.spec_from_file_location('unified_factory_bundle_r928',runtime);w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
assert w.CORE_SHA==sha(core)and w.PINS==pins and w.DESCRIPTOR==h.CONTRACT
old_payload=J(R/'work/original-backend-bootstrap-r847/r36/bundle/payload/payload-manifest.json')
new_payload=w.expected_payload(base_payload);payloadraw=enc(new_payload);payloadsha=hashlib.sha256(payloadraw).hexdigest()
new_release=w.expected_release(base_release,payloadsha);releaseraw=enc(new_release)
assert new_release['homeTransferAssets']==base_release['homeTransferAssets']and new_release[h.FIELD]==h.CONTRACT
assert {k for k in new_release if new_release[k]!=base_release.get(k)}=={'controllerFiles',h.FIELD,'publicTestRevision','payloadManifestSHA256'}
plan=copy.deepcopy(base_plan);files=copy.deepcopy(plan['files'])
for n,pin in {**pins,w.UPDATER:{'bytes':runtime.stat().st_size,'sha256':sha(runtime)}}.items():files[n]={'bytes':pin['bytes'],'SHA256':pin['sha256']}
raw={'payload-manifest.json':payloadraw,'release-manifest.json':releaseraw}
for n,b in raw.items():files[n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
assert len(files)==11 and sum(p['bytes']for p in files.values())<=32*1024**2
plan.update(updateId='20261104-r47-home-supervision-from-r45',files=files,newReleaseSHA256=hashlib.sha256(releaseraw).hexdigest(),newPayloadManifestSHA256=payloadsha,
 oldPayloadFiles={n:old_payload['files'][n]for n in files if n in old_payload['files']})
plan[w.OUTER_FIELD]={'relativeRoot':'base-r46','manifestSHA256':sha(B/'update-manifest.json'),'coreSHA256':sha(core)}
assert not plan['removedFrontendFiles']and not plan['legacyEntrySHA256']
O.mkdir(parents=True);sources[w.UPDATER]=runtime
for n,pin in base_plan['files'].items():
 dest=O/'base-r46/payload'/n;dest.parent.mkdir(parents=True,exist_ok=True);os.link(B/'payload'/n,dest)
put(O/'base-r46/update-manifest.json',(B/'update-manifest.json').read_bytes())
for n,pin in files.items():
 if n in raw:put(O/'payload'/n,raw[n])
 else:
  src=sources.get(n,B/'payload'/n);assert src.stat().st_size==pin['bytes']and sha(src)==pin['SHA256'];dest=O/'payload'/n;dest.parent.mkdir(parents=True,exist_ok=True);os.link(src,dest)
put(O/'update-manifest.json',enc(plan));D.mkdir()
proof={'prepared':True,'baseR45ReleaseSHA256':next(iter(plan['acceptedOldReleases'])),'baseSparseHomeR46SHA256':sha(B/'update-manifest.json'),
 'coreSHA256':sha(core),'runtimeSHA256':sha(runtime),'bundleManifestSHA256':sha(O/'update-manifest.json'),'newReleaseSHA256':plan['newReleaseSHA256'],
 'writes':len(files),'removals':0,'logicalPayloadBytes':sum(p['bytes']for p in files.values()),'sourceFiles':{n:str(p)for n,p in sources.items()},'extensionPins':pins,
 'originalCoreBytesAndCompleteInnerValidatorRetained':True,'exactOneBaseR45Only':True,'factoryModuleSameAsCurrentFullCandidate':True,
 'originalJarAuthConfigurationDatabaseUploadsAndThreeDimensionalSourcesRetained':True,'fullBundleAndRestoreVerificationPending':True,
 'publicUploadOrDeploymentOrGitPushPerformed':False,'fullCloneReady':False}
(D/'prepared-r928.json').write_bytes(enc(proof));print(json.dumps({k:v for k,v in proof.items()if k not in ['sourceFiles','extensionPins']}))
