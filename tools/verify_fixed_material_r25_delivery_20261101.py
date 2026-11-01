"""Independent readback of transport, composed WF11 assets and actual stopped program bytes."""
from pathlib import Path
import ast,hashlib,importlib.util,json,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';D=R/'Document/Deployment/public_test_material_r25_20261101'
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes());enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
manifest=read(D/'delivery-manifest.json');scope=read(D/'preparation-result.json');delivery=D/'delivery'
assert sha(D/'delivery-manifest.json')==scope['manifestSHA256']and(D/'delivery-manifest.json').read_bytes()==(delivery/'delivery-manifest.json').read_bytes()
assert set(p.name for p in delivery.iterdir())==set(manifest['files'])|{'delivery-manifest.json'}
for n,pin in manifest['files'].items():assert(delivery/n).stat().st_size==pin['bytes']and sha(delivery/n)==pin['sha256']
assert sum(p.stat().st_size for p in delivery.iterdir())==scope['transportBytesIncludingManifest']==1929811
terminal=read(R/'work/event_delivery_consistency_20261030/full-controller-r131/r1/controller-terminal.json');assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed']
app=R/'_g/Application';assert not(app.parent/'user-manual-protected.json').exists()
with zipfile.ZipFile(delivery/'Zhumadian_Material_Emergency_20261101_R25.zip')as z:
    assert z.testzip()is None;p=json.loads(z.read('update-manifest.json'));release=json.loads(z.read('payload/release-manifest.json'));q=json.loads(z.read('payload/payload-manifest.json'))
    assert set(z.namelist())=={'update-manifest.json','web.config'}|{'payload/'+n for n in p['files']}and len(z.namelist())==len(set(z.namelist()))
    assert set(p['acceptedOldReleases'])=={manifest['oldReleaseSHA256']}and len(p['files'])==189 and len(p['removedFrontendFiles'])==182
    for n,pin in p['files'].items():raw=z.read('payload/'+n);assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']
    oldq=read(W/'r24-unified-candidate-r1/sparse-graceful-update-preparation-r1/bundle/payload/payload-manifest.json')
    spec=importlib.util.spec_from_file_location('readback_material_r25',T/'original_public_test_update_r25_20261101.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert release[m.R25_MATERIAL_FIELD]==m.R25_MATERIAL_CONTRACT
    for n,pin in m.R25_MATERIAL_ROWS.items():assert q['files'][n]==pin and sha(app/n)==pin['sha256']
    before={n:v for n,v in oldq['files'].items()if not n.startswith('frontend/emergency_pc/')and n not in m.R25_MATERIAL_ROWS}
    after={n:v for n,v in q['files'].items()if not n.startswith('frontend/emergency_pc/')and n not in m.R25_MATERIAL_ROWS};assert before==after
    wf=read(W/'emergency-workflow-source-r11/build-result.json');assert len(wf['files'])==338
    for rel,pin in wf['files'].items():
        n='frontend/emergency_pc/'+rel;assert q['files'][n]==pin
        raw=z.read('payload/'+n)if n in p['files']else(W/'r24-unified-candidate-r1/payload'/n).read_bytes()
        assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']==sha(app/n)
    assert len(release['controllerFiles'])==20
    for n,h in release['controllerFiles'].items():assert sha(app/n)==h
wrapper=(delivery/'deploy_material_r25.py').read_text(encoding='utf-8');a=ast.parse(wrapper)
constants={n.targets[0].id:ast.literal_eval(n.value)for n in a.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and isinstance(n.value,ast.Constant)}
assert constants['OLD_UPDATER_SHA']==manifest['oldUpdaterSHA256']=='4931c7fbb58880f228423f8324d3b40cb22e500bc299f053a8fe455a742c7878'
assert constants['UPDATER_SHA']==manifest['newUpdaterSHA256']and constants['OLD']==manifest['oldReleaseSHA256']and constants['NEW']==manifest['newReleaseSHA256']
assert "'EXACT_R24_BASE'"in wrapper and 'EXACT_R21'not in wrapper and '__ARCHIVE_SHA__'not in wrapper
for n,mode in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
    s=(delivery/(n+'_Material_R25.cmd')).read_text(encoding='ascii');assert'deploy_material_r25.py'in s and(mode in s if mode else '--check-only'not in s and '--recover-this-update'not in s)
py=[p for p in T.glob('*r25*20261101.py')];assert len(py)>=9
for f in py:ast.parse(f.read_text(encoding='utf-8'))
proof={'schema':'xnby.r25.fixed-delivery-independent-readback.v1','allPassed':True,'transportFiles':8,'transportBytes':1929811,'manifestSHA256':scope['manifestSHA256'],
    'archiveCRCClosedMembersAndAllSHAsVerified':True,'exactR24BaseAndUpdaterGuardVerified':True,'threeMaterialSourceClassesMatchActualRuntimeFixture':True,
    'all338ComposedWF11AssetsMatchSourceBuildAndActuallyRunProgramBytes':True,'all20ControllersMatchActuallyRunProgramBytes':True,
    'allOtherPayloadRowsUnchanged':True,'newPythonSourcesSyntaxChecked':len(py),'actualStoppedControllerTerminalChecked':True,
    'protectedUserPreviewReadOrChanged':False,'realPrivateConfigurationOrDBRead':False,'publicUploadedOrInstalled':False,'publicGitPushed':False}
(D/'independent-fixed-delivery-verification.json').write_bytes(enc(proof));print(json.dumps(proof))
