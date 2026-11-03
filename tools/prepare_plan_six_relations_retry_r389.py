from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(D/'retry-prepared-r389.json').exists()
controller=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/firstAidTeams/controller/FirstAidTeamsController.java'
service=controller.parent.parent/'service/impl/FirstAidTeamsServiceImpl.java'
assert 'save(@RequestBody FirstAidTeamsVo vo)'in controller.read_text(encoding='utf-8')
assert 'getBaseMapper().insert(vo.getTeams())'in service.read_text(encoding='utf-8')
browser=(V/'verify_native_plan_six_relations_cancel_r386.mjs').read_text(encoding='utf-8')
anchor='options.body=JSON.stringify(payload);'
assert browser.count(anchor)==1
browser=browser.replace(anchor,"options.body=JSON.stringify(kind.entity==='firstAidTeams'?{teams:payload,members:[]}:payload);",1)
anchor=' for(const kind of relationKinds){\n  kind.ownA='
assert browser.count(anchor)==1;browser=browser.replace(anchor," stage='create-original-typed-owned-resource-fixtures';\n for(const kind of relationKinds){\n  kind.ownA=",1)
bf=V/'verify_native_plan_six_relations_typed_r390.mjs';assert not bf.exists();bf.write_text(browser,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
resume=(V/'plan_cancel_resume_r388.py').read_text(encoding='utf-8')
fixed_static=next(ast.get_source_segment(resume,n)for n in ast.parse(resume).body if isinstance(n,ast.FunctionDef)and n.name=='verify_candidate_static')
sources=[]
for role in ['inspect','prepare','run']:
 s=(V/('plan_cancel_'+role+'_r386.py')).read_text(encoding='utf-8')
 s=s.replace('native_plan_resource_cancel_r385_20261103/lifecycle','native_plan_resource_cancel_r385_20261103/lifecycle-r390')
 s=s.replace('plan-six-relations-cancel-r386','plan-six-relations-typed-r390')
 if role=='run':
  old_static=next(ast.get_source_segment(s,n)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name=='verify_candidate_static')
  assert s.count(old_static)==1;s=s.replace(old_static,fixed_static,1)
  s=s.replace("full-controller-r163/r149'","full-controller-r163/r151'")
  s=s.replace('verify_native_plan_six_relations_cancel_r386.mjs',bf.name).replace('663764a0641170dcd8ec969cccf47ff9ca02d98c3fc1facb82866d06deb569a0',sha(bf))
  assert sha(bf) in s
 ast.parse(s);out=V/('plan_typed_'+role+'_r390.py');assert not out.exists();out.write_text(s,encoding='utf-8')
 sources.append({'role':role,'name':out.name,'sha256':sha(out)})
report={'preparedOnly':True,'originalTeamControllerSHA256':sha(controller),'originalTeamServiceSHA256':sha(service),
 'normalTeamBodyShape':'teams-object-and-members-array','resourceValidationStillOwnNamesAndAllowedFieldsOnly':True,
 'staticChecksUseCurrentCompiledEntryNamesAndExactDecodedPins':True,'browserSHA256':sha(bf),'drivers':sources,
 'productCandidateChanged':False,'frozenR39Changed':False,'newActual29CaseAcceptancePending':True}
(D/'retry-prepared-r389.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
