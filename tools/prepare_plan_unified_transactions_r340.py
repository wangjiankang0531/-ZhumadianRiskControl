from pathlib import Path
import ast,hashlib,json

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
assert not(D/'transaction-sources-r340.json').exists()
source=(T/'verify_unified_composition_recovery_r288.py').read_text(encoding='utf-8');rows=[]
negative_extra='''
negative('missing-plan-runtime-descriptor',lambda p,o,n,q:n.pop(m.R39_PLAN_FIELD))
for key in ['schema','javaMajor','originalJarPlanClassSHA256','candidateSourceSHA256','schemaOrOriginalJarOrAuthenticationChanged']:
 negative('plan-contract-'+key,lambda p,o,n,q,k=key:n[m.R39_PLAN_FIELD].__setitem__(k,'foreign'))
negative('missing-plan-class-payload',lambda p,o,n,q:q['files'].pop(m.R39_PLAN_CLASS))
negative('wrong-plan-class-payload',lambda p,o,n,q:q['files'][m.R39_PLAN_CLASS].__setitem__('sha256','0'*64))
negative('missing-plan-class-transport',lambda p,o,n,q:p['files'].pop(m.R39_PLAN_CLASS))
negative('wrong-plan-class-transport',lambda p,o,n,q:p['files'][m.R39_PLAN_CLASS].__setitem__('SHA256','0'*64))
negative('foreign-class-install-path',lambda p,o,n,q:p['files'].__setitem__('payload/business/run-template/classes/foreign/Plan.class',{'bytes':1,'SHA256':'0'*64}))
negative('different-single-accepted-base',lambda p,o,n,q:p.__setitem__('acceptedOldReleases',{'0'*64:next(iter(p['acceptedOldReleases'].values()))}))
'''
readiness='''
readyroot=O/'plan-readiness';assert not readyroot.exists()
readyapp=readyroot/'Application';runtime=readyroot/'runtime';readycases=[]
def seed_ready(rel,pay,installed=True,running=True):
 rel=copy.deepcopy(rel);raw=enc(pay);rel['payloadManifestSHA256']=sha(raw)
 put(readyapp/'payload-manifest.json',raw);put(readyapp/'release-manifest.json',enc(rel))
 for path,include in [(readyapp/m.R39_PLAN_CLASS,installed),(runtime/'b'/m.R39_PLAN_CLASS.split('/run-template/',1)[1],running)]:
  if path.exists():path.unlink()
  if include:put(path,bodies[m.R39_PLAN_CLASS])
seed_ready(new,q)
assert m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})['installedAndRuntimeClassCopyMatched']
readycases.append({'case':'declared-installed-and-runtime-copy-exact','passed':True})
for label in ['missing-runtime-copy','foreign-runtime-copy','foreign-installed-copy','missing-descriptor','wrong-class-pin','wrong-jar-pin']:
 rel,pay=copy.deepcopy(new),copy.deepcopy(q)
 if label=='missing-descriptor':rel.pop(m.R39_PLAN_FIELD)
 if label=='wrong-class-pin':pay['files'][m.R39_PLAN_CLASS]['sha256']='0'*64
 if label=='wrong-jar-pin':pay['files']['payload/business/application.jar']['sha256']='0'*64
 seed_ready(rel,pay,running=label!='missing-runtime-copy')
 if label=='foreign-runtime-copy':put(runtime/'b'/m.R39_PLAN_CLASS.split('/run-template/',1)[1],b'own-foreign-runtime-bytecode')
 if label=='foreign-installed-copy':put(readyapp/m.R39_PLAN_CLASS,b'own-foreign-installed-bytecode')
 try:m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})
 except ValueError as e:readycases.append({'case':label,'refused':str(e)})
 else:raise AssertionError('PLAN_READINESS_BOUNDARY_ACCEPTED:'+label)
seed_ready(old,oldq,installed=False,running=False)
assert m.native_plan_runtime_ready(readyapp,{'run':str(runtime)})is None
readycases.append({'case':'unchanged-original-base-requires-no-plan-override','passed':True})
assert len(readycases)==8
put(D/'plan-readiness-boundaries-r340.json',enc({'passed':True,'cases':readycases,'onlyOwnedFileFixtures':True,'notActualJVMOrServerHealthAcceptance':True}))
'''
for label in ['r36','r37']:
    text=source.replace("O=W/'r38-unified-original-mappers-r2'", "O=R/'work/r39-plan-runtime-unified-r1/"+label+"'")
    text=text.replace("D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2'", "D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103/"+label+"'")
    text=text.replace('original_public_test_update_r38_mapper_preflight_r286.py','original_public_test_update_r39_plan_runtime_r337.py')
    if label=='r37':text=text.replace("OLD=W/'r36-native-history-candidate-r2/bundle'", "OLD=R/'work/r39-plan-runtime-unified-r1/original-r37-contract'")
    text=text.replace('len(changes)==363','len(changes)==364').replace("len(plan['files'])==186","len(plan['files'])==187")
    text=text.replace("'writes':186","'writes':187").replace("'changePaths':363","'changePaths':364").replace("'all363OriginalPathStatesRestored'","'all364OriginalPathStatesRestored'")
    anchor="put(D/'composition-negative-cases.json',enc(cases))";assert text.count(anchor)==1
    text=text.replace(anchor,negative_extra+'\n'+anchor,1)
    anchor="('parameter-write',m.R24_PARAMETER),";assert text.count(anchor)==1
    text=text.replace(anchor,"('plan-class-write',m.R39_PLAN_CLASS),"+anchor,1)
    anchor="('foreign-parameter',m.R24_PARAMETER),";assert text.count(anchor)==1
    text=text.replace(anchor,anchor+"('foreign-plan-class',m.R39_PLAN_CLASS),",1)
    anchor="proof={'passed':True,";assert text.count(anchor)==1
    text=text.replace(anchor,readiness+'\n'+anchor,1)
    text=text.replace("'actualFileBackupReplaceRestoreFunctionsExecuted':True", "'actualFileBackupReplaceRestoreFunctionsExecuted':True,'planReadinessByteBoundaryScenarios':len(readycases),'baselineVariant':'"+label.upper()+"'")
    ast.parse(text);target=V/('verify_plan_unified_transactions_'+label+'_r340.py');assert not target.exists();target.write_text(text,encoding='utf-8')
    rows.append({'variant':label.upper(),'source':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(D/'transaction-sources-r340.json').write_text(json.dumps({'prepared':True,'sources':rows,'eachFixtureBoundedBelow512MiB':True,
 'newPlanClassWriteFaultAndForeignDriftIncluded':True,'servicesOrSQLWillNotRun':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'variantDrivers':len(rows),'planReadinessFileBoundaryCasesEach':8,'servicesStarted':False}))
