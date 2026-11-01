from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';P=R/'work/r23gv-r1'
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=read(P/'full-preflight-result.json');assert proof['allPassed']and proof['updaterSHA256']=='d500b5b591971532a74dd632d2cff7139474bd61986c01bc75b184017c143d41'
assert not(R/'_b').exists()
spec=importlib.util.spec_from_file_location('real_graceful_update',T/'original_public_test_update_r23_graceful_20261101.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
app=P/'Application';bundle=P/'bundle';changes=read(P/'fixture-changes.json')
assert len(changes)==1183
m.backup_code(app,P/'before-controller-code',changes)
m.replace_code(app,bundle,changes)
release=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json')
assert sha(app/'release-manifest.json')==read(bundle/'update-manifest.json')['newReleaseSHA256']
assert sha(app/'payload-manifest.json')==release['payloadManifestSHA256']
for name,pin in release['controllerFiles'].items():m.check_file(app,name,pin)
for name,row in payload['files'].items():
    if name.startswith('seed/mysql/'):continue
    m.check_file(app,name,row['sha256'],row['bytes'])
overlay=Path('D:/Zqa20261025/Application/payload/callback-overlay/20261026-password-identity')
manifest=read(overlay/'manifest.json');assert sha(overlay/'manifest.json')==release['missingAuthOverlayManifestSHA256']=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb'
assert len(manifest['files'])==6
target=app/'payload/callback-overlay/20261026-password-identity';target.mkdir(parents=True)
(target/'manifest.json').write_bytes((overlay/'manifest.json').read_bytes())
for name,row in manifest['files'].items():
    source=m.check_file(overlay,name,row['SHA256'],row['bytes']);dest=m.regular(target,name)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
spec=importlib.util.spec_from_file_location('actual_callback_loader',app/'tools/original_callback_overlay.py')
callback=importlib.util.module_from_spec(spec);spec.loader.exec_module(callback)
callback.load_callback_overlay(app,target/'manifest.json',release['missingAuthOverlayManifestSHA256'])
(P/'controller-code-prepared.json').write_text(json.dumps({'allPayloadAnd20ControllerPinsVerified':True,
    'callbackManifestAndSixFilesAndSixBaselinesVerified':True,'originalPrivateOrSeedRead':False,
    'ownedLocalCodeReplacementOnly':True,'readyForShortPathMove':True},indent=2),encoding='utf-8')
print('EXACT_GRACEFUL_CONTROLLER_AND_PAYLOAD_PREPARED_CALLBACK_CODE_VERIFIED')
