"""Adapt only fixture identity/private manifest pins; preserve all R45 shipped program bytes."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
source=V/'original_public_test_update_r45_bootstrap_r847.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
s=importlib.util.spec_from_file_location('r45_file_fixture_runtime',source);runtime=importlib.util.module_from_spec(s);s.loader.exec_module(runtime)
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def compose(base,old_payload,out,label):
    assert label in ['r36','r37']and not out.exists()
    public=R/f'work/original-backend-bootstrap-r847/{label}/bundle'
    plan=copy.deepcopy(J(public/'update-manifest.json'));payload=copy.deepcopy(J(public/'payload/payload-manifest.json'));release=copy.deepcopy(J(public/'payload/release-manifest.json'))
    baseline=J(base/'update-manifest.json')
    payload['files']['private/server-configuration.json']=old_payload['files']['private/server-configuration.json']
    payloadRaw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payloadRaw).hexdigest();releaseRaw=enc(release)
    plan.update(targetApplication=baseline['targetApplication'],gatewayPort=baseline['gatewayPort'],
        acceptedOldReleases=baseline['acceptedOldReleases'],basePayloadManifestSHA256=baseline['basePayloadManifestSHA256'],
        newReleaseSHA256=hashlib.sha256(releaseRaw).hexdigest(),newPayloadManifestSHA256=release['payloadManifestSHA256'])
    raw={'release-manifest.json':releaseRaw,'payload-manifest.json':payloadRaw}
    for n,b in raw.items():plan['files'][n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
    for n,pin in plan['files'].items():
        target=out/'payload'/n
        if n in raw:put(target,raw[n]);continue
        origin=public/'payload'/n
        assert origin.stat().st_size==pin['bytes']and sha(origin)==pin['SHA256']
        target.parent.mkdir(parents=True,exist_ok=True)
        if origin.stat().st_file_attributes&1:target.write_bytes(origin.read_bytes())
        else:os.link(origin,target)
    put(out/'update-manifest.json',enc(plan))
    return {'bundle':str(out),'manifestSHA256':sha(out/'update-manifest.json'),'newReleaseSHA256':plan['newReleaseSHA256']}
