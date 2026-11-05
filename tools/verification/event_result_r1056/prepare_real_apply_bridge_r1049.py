"""Prepare exact real-file local upgrade scenarios; does not mutate/start G."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import socket

V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian')
G=R/'_g/Application'
W=R/'work/ua1049'
D=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'
PUBLIC=R/'Document/Deployment/public_test_event_write_results_r48_20261105/delivery'

def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def read(p):return json.loads(p.read_bytes())
def encode(d):return(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def plain(p):
    for item in [p,*p.parents]:
        assert not item.is_symlink()
        if item.exists():assert not item.lstat().st_file_attributes&0x400
    return p

def main():
    assert not W.exists()and not D.exists()
    assert read(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
    assert not(G.parent/'user-manual-protected.json').exists()
    assert sha(G/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
    assert read(V/'static-control-bridge-r1046/focused-verification.json')['passed']
    assert shutil.disk_usage(R).free>4*1024**3
    resolution=read(V/'r48-file-source-resolution-r1007.private.json')
    assert not resolution['unresolved']
    base=resolution['bases']['r45']
    meta=Path(base['metadataRoot'])
    old=read(meta/'release-manifest.json')
    assert sha(meta/'release-manifest.json')=='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
    assert old['releaseId']==read(G/'UserData/OriginalServer/installation.json')['releaseId']
    old_payload=read(meta/'payload-manifest.json')
    config_before=pin(G/'private/server-configuration.json')
    old_payload['files']['private/server-configuration.json']=config_before
    sources={};mutations={}
    for index,(name,row)in enumerate(base['programs'].items(),1):
        assert not name.startswith(('UserData/','private/','seed/','Assets/'))
        source=plain(Path(row['source']))
        expected={'bytes':row['bytes'],'sha256':row['sha256']}
        assert pin(source)==expected,'OLD_SOURCE_DRIFT:'+name
        current=pin(G/name)
        if current!=expected:mutations[name]={'before':current,'after':expected,'source':str(source)}
        sources[name]={'source':str(source),**expected}
        if index%4000==0:print(json.dumps({'stage':'old-real-source-pins','checked':index}),flush=True)
    with socket.socket()as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    assert port not in {8767,18891,18892,8792,8796}
    W.mkdir();D.mkdir();(W/'old').mkdir()
    (W/'old/payload-manifest.json').write_bytes(encode(old_payload))
    old['payloadManifestSHA256']=sha(W/'old/payload-manifest.json')
    (W/'old/release-manifest.json').write_bytes(encode(old))
    for name in ['payload-manifest.json','release-manifest.json']:
        p=W/'old'/name;mutations[name]={'before':pin(G/name),'after':pin(p),'source':str(p)}
    protected={name:pin(G/name)for name in ['private/server-configuration.json','UserData/OriginalServer/installation.json','UserData/OriginalServer/store-credentials.private.json']}
    assert all(protected.values())
    scenarios=[]
    for label,runtime_source in [('original-failure',PUBLIC/'r48_update_runtime.py'),('repaired',V/'static-control-bridge-r1046/r48_update_runtime.py')]:
        bundle=W/label;payload=bundle/'payload';payload.mkdir(parents=True)
        wrapper=load('real_apply_prepare_'+label.replace('-','_'),runtime_source)
        runtime=wrapper.runtime()
        public_base=copy.deepcopy(runtime.R48_BASES['3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'])
        public_base['accepted']['payloadManifestSHA256']=old['payloadManifestSHA256']
        runtime.R48_BASES={sha(W/'old/release-manifest.json'):public_base}
        runtime.R48_PLAN_COMMON={**runtime.R48_PLAN_COMMON,'targetApplication':G.as_posix(),'gatewayPort':port}
        target_payload=copy.deepcopy(old_payload)
        target_payload['files']=runtime.r48_expected_files(old_payload['files'])
        (payload/'payload-manifest.json').write_bytes(encode(target_payload))
        target_release=runtime.r48_expected_release(old,sha(payload/'payload-manifest.json'))
        (payload/'release-manifest.json').write_bytes(encode(target_release))
        assert wrapper.declared(target_release)
        target_sources=copy.deepcopy(resolution['newSources'])
        target_sources['tools/original_public_test_update.py']={'source':str(runtime_source),**pin(runtime_source)}
        core=runtime_source.with_name('original_public_test_base_r46.py')
        target_sources['tools/original_public_test_base_r46.py']={'source':str(core),**pin(core)}
        changed={name:row for name,row in target_payload['files'].items()if old_payload['files'].get(name)!=row}
        files={}
        for name,row in changed.items():
            assert not name.startswith(('UserData/','private/','seed/','Assets/'))
            source=Path(target_sources[name]['source'])
            assert pin(source)==row,'NEW_SOURCE_DRIFT:'+name
            target=payload/name;plain(target);target.parent.mkdir(parents=True,exist_ok=True)
            try:os.link(source,target)
            except OSError as exc:
                assert exc.winerror==1142 and row['bytes']<=4096 and '/frontend/tiles/'in target.as_posix()
                target.write_bytes(source.read_bytes())
            assert pin(target)==row
            files[name]={'bytes':row['bytes'],'SHA256':row['sha256']}
        for name in ['payload-manifest.json','release-manifest.json']:
            row=pin(payload/name);files[name]={'bytes':row['bytes'],'SHA256':row['sha256']}
        removed={name:{'bytes':row['bytes'],'SHA256':row['sha256']}for name,row in old_payload['files'].items()if name.startswith('frontend/emergency_pc/')and name not in target_payload['files']}
        plan={**runtime.R48_PLAN_COMMON,'acceptedOldReleases':{sha(W/'old/release-manifest.json'):public_base['accepted']},
            'basePayloadManifestSHA256':old['payloadManifestSHA256'],'files':files,
            'newPayloadManifestSHA256':sha(payload/'payload-manifest.json'),'newReleaseSHA256':sha(payload/'release-manifest.json'),
            'oldPayloadFiles':{name:old_payload['files'][name]for name in files if name in old_payload['files']},
            'removedFrontendFiles':removed,'updateId':'20261105-r48-event-results-from-r45'}
        (bundle/'update-manifest.json').write_bytes(encode(plan))
        scenarios.append({'label':label,'runtimeSource':str(runtime_source),'runtimeSHA256':sha(runtime_source),
            'bundle':str(bundle),'planSHA256':sha(bundle/'update-manifest.json'),
            'newReleaseSHA256':plan['newReleaseSHA256'],'expectedOriginalStaticFailure':label=='original-failure'})
    assert max(len(str((W/'base-before/before'/name).with_name('.'+Path(name).name+'.own-'+'0'*32+'.tmp')))for name in mutations)<260
    initial_metadata={name:pin(G/name)for name in ['UserData/OriginalPublicUpdates/latest.json','UserData/OriginalPublicUpdates/pending.json','UserData/OriginalDeployment/active-deployment.private.json']}
    assert all(row is None for row in initial_metadata.values()),'UNEXPECTED_EXISTING_UPDATE_METADATA_KEEP'
    plan={'schema':'xnby.owned-real-apply-bridge-test.v1','target':str(G),'onlyExistingOwnedSyntheticFixture':True,
        'originalGReleaseSHA256':sha(G/'release-manifest.json'),'oldReleaseSHA256':sha(W/'old/release-manifest.json'),
        'mutations':mutations,'sources':sources,'protectedPins':protected,'initialMetadata':initial_metadata,
        'pointerBefore':pin(G/'UserData/OriginalServer/current-run.json'),'gatewayPort':port,
        'binding':public_base,'scenarios':scenarios,'minimumFreePhysicalAndCommitBytes':7*1024**3,
        'outerHarnessAndChildrenMemoryLimitBytes':4*1024**3,
        'IISAndPublicTLSNotEmulatedAsAcceptance':True,'noNewBusinessRowsOrBrowserAuthentication':True,
        'scopeBindings':['owned target','owned gateway port','same G private-config payload pin'],
        'ingressTestBinding':'actual local HTTP gateway responses; not real IIS or TLS'}
    (W/'prepared-plan.private.json').write_bytes(encode(plan))
    proof={'prepared':True,'oldSourcesActuallyHashRead':len(sources),'baseCodeMutations':len(mutations),
        'preparedPlanSHA256':sha(W/'prepared-plan.private.json'),'scenarioCount':len(scenarios),
        'GCodeOrDataChanged':False,'servicesStarted':False,'publicChanged':False,
        'realApplyUpdateAccepted':False,'fullCloneReady':False}
    (D/'prepared-r1049.json').write_bytes(encode(proof))
    print(json.dumps(proof),flush=True)

if __name__=='__main__':main()
