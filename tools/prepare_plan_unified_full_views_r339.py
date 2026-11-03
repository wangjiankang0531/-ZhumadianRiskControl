from pathlib import Path
import ast,hashlib,json,zipfile

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
O=R/'work/r39-plan-runtime-unified-r1';J=lambda p:json.loads(p.read_bytes())
assert not(D/'full-preflight-sources-r339.json').exists()
plan=J(D/'bundle-preparation-r338.json');contract37=O/'original-r37-contract'
assert not contract37.exists()
archive=list((R/'Document/Deployment/public_test_static_performance_r37_20261103/delivery').glob('*.zip'));assert len(archive)==1
with zipfile.ZipFile(archive[0])as z:
    manifest=json.loads(z.read('update-manifest.json'))
    assert len(manifest['files'])==6
    for name,pin in manifest['files'].items():
        assert not name.startswith(('private/','UserData/','Assets/','Reference/','seed/'))
        raw=z.read('payload/'+name);assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256']
        out=contract37/'payload'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
source=(T/'verify_unified_full_program_r288.py').read_text(encoding='utf-8');rows=[]
for label in ['r36','r37']:
    text=source.replace("S=W/'r38-unified-original-mappers-r2'", "S=R/'work/r39-plan-runtime-unified-r1/"+label+"'")
    text=text.replace("O=R/'work/r38-unified-full-preflight-r288'", "O=R/'work/r39-full-preflight-"+label+"-r339'")
    text=text.replace("D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2'", "D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103/"+label+"'")
    text=text.replace('original_public_test_update_r38_mapper_preflight_r286.py','original_public_test_update_r39_plan_runtime_r337.py')
    text=text.replace("'oldDeclaredControls':21", "'oldDeclaredControls':len(old['controllerFiles'])")
    if label=='r37':text=text.replace("OLD=W/'r36-native-history-candidate-r2/bundle'", "OLD=R/'work/r39-plan-runtime-unified-r1/original-r37-contract'")
    anchor="checks=[{'case':'all-R36-programs-and-final-R38-unified-path-load_bundle'"
    assert text.count(anchor)==1
    text=text.replace(anchor,"assert m.native_plan_runtime_declared(new,newq)and len(loaded['acceptedOldReleases'])==1\nchecks=[{'case':'all-"+label.upper()+"-programs-and-final-R39-unified-path-load_bundle'",1)
    text=text.replace("'internalSameSnapshotMapperGatePassed':True", "'internalSameSnapshotMapperGatePassed':True,'candidatePlanClassContractAndTransportPassed':True,'baselineVariant':'"+label.upper()+"'")
    ast.parse(text)
    file=V/('verify_plan_unified_full_'+label+'_r339.py');assert not file.exists();file.write_text(text,encoding='utf-8')
    rows.append({'variant':label.upper(),'source':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(D/'full-preflight-sources-r339.json').write_text(json.dumps({'prepared':True,'sources':rows,
 'r37OriginalContractOnlySixStaticFilesExtracted':True,'privateConfigAssetsDatabaseOrSeedReadOrCopied':False,
 'fullProgramsWillBeReadOnlyHardlinksAndMutableCopiesBounded128MiBPerVariant':True,
 'servicesWillNotStart':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'variantDrivers':len(rows),'r37StaticContractFiles':len(manifest['files']),'servicesStarted':False}))
