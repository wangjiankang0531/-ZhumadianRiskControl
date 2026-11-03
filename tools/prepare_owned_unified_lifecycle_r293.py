from pathlib import Path
import copy,hashlib,json,os,shutil,socket
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools'
D=R/'Document/Deployment/unified_update_owned_lifecycle_r292_20261103'
O=R/'work/unified-update-lifecycle-r293';W=R/'work/user_feedback_20261031'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert not O.exists();inspection=J(D/'inspection.json')
assert inspection['ownedSyntheticFixtureConfirmed']and inspection['ownedProcessesReferencingFixture']==0
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert sha(A/'release-manifest.json')==inspection['currentOwnReleaseSHA256']=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert inspection['releaseIdAlreadyMatchesR36']and inspection['installationReleaseIdAlreadyMatchesR36']
assert shutil.disk_usage(R).free>2*1024**3+64*1024**2
O.mkdir()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
oldroot=W/'r36-native-history-candidate-r2/bundle';public=W/'r38-unified-original-mappers-r2/bundle'
old=J(oldroot/'payload/release-manifest.json');oldq=J(oldroot/'payload/payload-manifest.json')
new=J(public/'payload/release-manifest.json');newq=J(public/'payload/payload-manifest.json');plan=copy.deepcopy(J(public/'update-manifest.json'))
cfg=A/'private/server-configuration.json';cfgpin={'bytes':cfg.stat().st_size,'sha256':sha(cfg)}
oldq['files']['private/server-configuration.json']=dict(cfgpin);newq['files']['private/server-configuration.json']=dict(cfgpin)
oldqraw=enc(oldq);newqraw=enc(newq);old['payloadManifestSHA256']=hashlib.sha256(oldqraw).hexdigest();new['payloadManifestSHA256']=hashlib.sha256(newqraw).hexdigest()
oldraw=enc(old);newraw=enc(new);oldpin=hashlib.sha256(oldraw).hexdigest();newpin=hashlib.sha256(newraw).hexdigest()
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
assert port not in [18891,18892,8767]
plan.update(targetApplication=A.as_posix(),gatewayPort=port,
 acceptedOldReleases={oldpin:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
 basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=new['payloadManifestSHA256'],newReleaseSHA256=newpin)
for n,raw in [('release-manifest.json',newraw),('payload-manifest.json',newqraw)]:plan['files'][n]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
bundle=O/'bundle'
for n,pin in plan['files'].items():
    out=bundle/'payload'/n;out.parent.mkdir(parents=True,exist_ok=True)
    if n in ['release-manifest.json','payload-manifest.json']:out.write_bytes(newraw if n=='release-manifest.json'else newqraw)
    else:
        src=public/'payload'/n;assert src.stat().st_size==pin['bytes']and sha(src)==pin['SHA256'];os.link(src,out)
put(bundle/'update-manifest.json',enc(plan))
desired={}
for row in inspection['exactPathsForOwnCodePreparationOnly']:
    n=row['path'];src=Path(row['source']);assert n.startswith(('runtime/','frontend/','payload/','tools/','deploy/','iis/'))
    assert not n.startswith(('private/','UserData/','Assets/','seed/'))
    assert src.is_file()and src.stat().st_size==row['sourceBytes']and sha(src)==row['sourceSHA256']
    desired[n]={'bytes':row['sourceBytes'],'sha256':row['sourceSHA256'],'source':str(src)}
for n,raw in [('release-manifest.json',oldraw),('payload-manifest.json',oldqraw)]:
    staged=O/'baseline'/n;put(staged,raw);desired[n]={'bytes':len(raw),'sha256':sha(staged),'source':str(staged)}
known=set(oldq['files'])|set(old['controllerFiles'])|{'iis/App_Code/XnbyReferenceProxy.cs','release-manifest.json','payload-manifest.json'}
for n in plan['files']:
    if n not in known and(A/n).exists():
        assert n.startswith('frontend/emergency_pc/');desired[n]=None
active='UserData/OriginalDeployment/active-deployment.private.json';active_raw=enc({'releaseId':old['releaseId'],'ownedSyntheticLifecycleFixture':True})
put(O/'baseline/active-deployment.private.json',active_raw);desired[active]={'bytes':len(active_raw),'sha256':hashlib.sha256(active_raw).hexdigest(),'source':str(O/'baseline/active-deployment.private.json')}
for n in ['UserData/OriginalPublicUpdates/latest.json','UserData/OriginalPublicUpdates/pending.json']:desired[n]=None
allnames=set(desired)|set(plan['files'])|set(plan['removedFrontendFiles'])|{'UserData/OriginalServer/current-run.json'}
before={}
for n in sorted(allnames):
    p=A/n
    if p.exists():
        assert p.is_file()and not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400
        raw=p.read_bytes();dest=O/'original-before'/n;put(dest,raw)
        before[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    else:before[n]=None
scope={'schema':'xnby.r293.owned-update-lifecycle-scope.v1','onlyOwnedSyntheticG':True,
 'baseOriginalGReleaseSHA256':inspection['currentOwnReleaseSHA256'],'baselineAdaptedR36SHA256':oldpin,
 'candidateAdaptedR38SHA256':newpin,'bundleManifestSHA256':sha(bundle/'update-manifest.json'),
 'candidateUpdaterSourceSHA256':sha(T/'original_public_test_update_r38_mapper_preflight_r286.py'),
 'gatewayPort':port,'desiredBaseline':desired,'originalBefore':before,
 'privateConfigurationPin':cfgpin,'installationSHA256':sha(A/'UserData/OriginalServer/installation.json'),
 'targetCodeOnlyPaths':len(allnames),'baselineMutations':len(desired),
 'databaseCopiedOrReplaced':False,'servicesStartedByPreparation':False,
 'normalSixComponentLifecycleMustFinishBeforeRestore':True,
 'loadBundleTargetAndGatewayAdaptersRequired':True,
 'ingressAdapterWillUseOwnedLoopbackHTTPNotIISTLS':True,
 'publicOrFormal18891OrScene8767Touched':False}
put(O/'scope.json',enc(scope))
proof={k:v for k,v in scope.items()if k not in ['desiredBaseline','originalBefore','privateConfigurationPin']}
proof.update(prepared=True,ownCodePreimagesSaved=True,baselineApplied=False,estimatedPhysicalPeakBytes=64*1024**2)
put(D/'prepared-scope-r293.json',enc(proof))
print(json.dumps({'prepared':True,'baselineMutations':len(desired),'allCodeAndPointerPreimages':len(before),
 'onlySyntheticFixture':True,'baselineApplied':False,'databaseOrServicesTouched':False,'gatewayPort':port}))
