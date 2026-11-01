from pathlib import Path
import ast,hashlib,json,stat,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';D=R/'Document/Deployment/public_test_team_r26_20261101';B=W/'r26-team-native-candidate-r1/bundle';G=R/'_g/Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest();manifest=J(D/'delivery-manifest.json');prep=J(D/'preparation-result.json');delivery=D/'delivery'
assert sha(D/'delivery-manifest.json')==prep['manifestSHA256']=='7f41852d18f96a8b812edfafc4f9f018971a00b1ecd098c7807ead2dcfa11c65'and(D/'delivery-manifest.json').read_bytes()==(delivery/'delivery-manifest.json').read_bytes()
assert {p.name for p in delivery.iterdir()}==set(manifest['files'])|{'delivery-manifest.json'}and len(manifest['files'])==7
for name,pin in manifest['files'].items():p=delivery/name;assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400 and p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']
archive=delivery/'Zhumadian_Team_Emergency_20261101_R26.zip';source=T/'original_public_test_update_r26_20261101.py';updater='tools/original_public_test_update.py';target='payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml';prefix='frontend/emergency_pc/'
with zipfile.ZipFile(archive)as z:
    assert z.testzip()is None and len(z.namelist())==len(set(z.namelist()))
    plan=json.loads(z.read('update-manifest.json'));assert digest(z.read('update-manifest.json'))==manifest['updateManifestSHA256']
    assert set(z.namelist())=={'web.config','update-manifest.json'}|{'payload/'+n for n in plan['files']}
    for item in z.infolist():assert not item.filename.startswith(('/','\\'))and '..'not in Path(item.filename).parts and stat.S_IFMT(item.external_attr>>16)not in [stat.S_IFLNK,stat.S_IFDIR]
    for name,pin in plan['files'].items():raw=z.read('payload/'+name);assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']and raw==(B/'payload'/name).read_bytes()
    q=json.loads(z.read('payload/payload-manifest.json'));r=json.loads(z.read('payload/release-manifest.json'))
    assert digest(z.read('payload/payload-manifest.json'))==r['payloadManifestSHA256']==plan['newPayloadManifestSHA256']and digest(z.read('payload/release-manifest.json'))==plan['newReleaseSHA256']==manifest['newReleaseSHA256']
    assert z.read('payload/'+updater)==source.read_bytes()==(delivery/'r26_update_runtime.py').read_bytes()and sha(source)==manifest['newUpdaterSHA256']
    raw=z.read('payload/'+target);assert len(raw)==2568 and digest(raw)=='2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'
    with zipfile.ZipFile(G/'payload/business/application.jar')as original:assert raw==original.read('xml/FirstAidTeamMembersMapper.xml')
old=J(W/'r25-material-unified-candidate-r1/bundle/payload/release-manifest.json');oldq=J(W/'r25-material-unified-candidate-r1/bundle/payload/payload-manifest.json');assert set(plan['acceptedOldReleases'])=={'b849ad0d46c529b036d29baf4089e57867805c8cdc33661248583337b5f10678'}
assert {n:h for n,h in old['controllerFiles'].items()if n!=updater}=={n:h for n,h in r['controllerFiles'].items()if n!=updater}and len(r['controllerFiles'])==20
legal={'release-manifest.json','payload-manifest.json',updater,target}|{n for n in q['files']if n.startswith(prefix)};assert set(plan['files'])<=legal and len(plan['files'])==177
retained=lambda files:{n:pin for n,pin in files.items()if not n.startswith(prefix)and n!=target};assert retained(oldq['files'])==retained(q['files'])
obsolete={n:{'bytes':pin['bytes'],'SHA256':pin['sha256']}for n,pin in oldq['files'].items()if n.startswith(prefix)and n not in q['files']};assert plan['removedFrontendFiles']==obsolete and len(obsolete)==171
build=J(W/'emergency-workflow-source-r12/build-result.json');assert {n.removeprefix(prefix):pin for n,pin in q['files'].items()if n.startswith(prefix)}==build['files']and len(build['files'])==339
defs=lambda p:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};before=defs(T/'original_public_test_update_r25_20261101.py');after=defs(source);assert {n for n in before if before[n]!=after[n]}=={'load_bundle','health','material_bundle_contract'}and set(after)-set(before)=={'team_declared','team_bundle_contract','team_ready'}
for name in ['deploy_team_r26.py','r26_update_runtime.py']:ast.parse((delivery/name).read_text(encoding='utf-8'))
assert 'EXACT_R25' in(delivery/'deploy_team_r26.py').read_text(encoding='utf-8')and manifest['oldUpdaterSHA256']=='44c846481bc7eb58447374ea37653da6b806e4471ce6a2a83d64c9e901010cb3'
whole=J(R/'work/event_delivery_consistency_20261030/full-controller-r134/r1/result.json');ui=J(R/'work/event_delivery_consistency_20261030/full-controller-r134/r1/team-browser/result.json');assert whole['allPassed']and whole['updaterSHA256']==sha(source)and whole['checks']['actualR26TeamMapperRuntimePinsPassed']and ui['passed']and len(ui['cases'])==13
proof={'schema':'xnby.r26.independent-fixed-delivery.v1','passed':True,'transportFiles':8,'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),'exactArchivedProgramPathsAndCRCVerified':177,'exactObsoleteEmergencyFiles':171,'exactWF12FrontendFiles':339,'originalMemberXMLFromRetainedJarByteEqual':True,'other19ControlsAllOriginalJarsAndOtherPayloadRetained':True,'normalStopBackupReplaceRestoreASTUnchanged':True,'actualNewUpdaterAnd13NativeCasesProofMatched':True,'publicUploadedDeployedOrGitPushed':False,'fullCloneReady':False};assert proof['transportBytes']==prep['transportBytesIncludingManifest'];(D/'independent-fixed-delivery-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
