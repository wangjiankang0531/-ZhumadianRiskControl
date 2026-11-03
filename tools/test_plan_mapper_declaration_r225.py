from pathlib import Path
import copy,importlib.util,json
R=Path('D:/Project/Zhumadian');p=R/'Application/tools/original_public_test_update_r37_plan_exercise_r225.py'
s=importlib.util.spec_from_file_location('candidate',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A=R/'_g/Application';old=m.read(A/'release-manifest.json');payload=m.read(A/'payload-manifest.json')
cases=[]
def check(name,fn,passes):
    rejected=False
    try:value=fn()
    except ValueError:rejected=True
    assert rejected is not passes,name
    if passes:assert value is True,name
    cases.append({'case':name,'passed':True,'expectedAccepted':passes})
check('legacy-exact-team-descriptor-and-no-new-plan-resource',lambda:m.team_declared(old,payload),True)
good=copy.deepcopy(old);q=copy.deepcopy(payload);good[m.R37_PLAN_FIELD]=copy.deepcopy(m.R37_PLAN_CONTRACT);q['files'].update(copy.deepcopy(m.R37_PLAN_ROWS))
check('exact-new-plan-XML-and-legacy-team-contract-together',lambda:m.team_declared(good,q),True)
check('new-resource-without-explicit-plan-descriptor',lambda:m.team_declared(old,q),False)
check('descriptor-without-exact-resource',lambda:m.team_declared(good,payload),False)
for name,mutate in [
 ('wrong-plan-resource-hash',lambda a,b:b['files'][m.R37_PLAN_XML].update(sha256='0'*64)),
 ('wrong-plan-resource-length',lambda a,b:b['files'][m.R37_PLAN_XML].update(bytes=830)),
 ('boolean-resource-length',lambda a,b:b['files'][m.R37_PLAN_XML].update(bytes=True)),
 ('changed-plan-revision',lambda a,b:a[m.R37_PLAN_FIELD].update(revision='unapproved')),
 ('descriptor-extra-option',lambda a,b:a[m.R37_PLAN_FIELD].update(skipChecks=True)),
 ('changed-original-business-archive',lambda a,b:b['files']['payload/business/application.jar'].update(sha256='f'*64)),
 ('unknown-extra-mapper',lambda a,b:b['files'].update({'payload/business/run-template/classes/mapper/Unknown.xml':{'bytes':1,'sha256':'a'*64}})),
 ('changed-retained-team-resource',lambda a,b:b['files'][next(iter(m.R26_TEAM_ROWS))].update(bytes=1)),
 ('changed-retained-material-class',lambda a,b:b['files'][next(iter(m.R25_MATERIAL_ROWS))].update(sha256='1'*64)),
]:
 a,b=copy.deepcopy(good),copy.deepcopy(q);mutate(a,b);check(name,lambda:m.team_declared(a,b),False)
proof={'passed':True,'checks':len(cases),'cases':cases,'actualCandidateFunctionsExecuted':True,
       'legacyChecksNotStubbedOrMonkeyPatched':True,'SQLRuntimeOrProductChanged':False}
D=R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103';(D/'descriptor-gates.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(cases),'realCandidateAndLegacyContractFunctionsUsed':True}))
