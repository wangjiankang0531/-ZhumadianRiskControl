from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_six_relations_r372_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()and not(R/'work/event_delivery_consistency_20261030/full-controller-r163/r147').exists()
assert J(R/'Document/Deployment/native_plan_unified_candidate_r39_20261103/verified-lifecycle-stage-r350.json')['bothExactBaselinesPassed']
assert sha(T/'original_public_test_update_r39_plan_runtime_r337.py')=='e935f51aa3c7a5aae3346c632b90423ce99f6a0887b1d44781ea0ed8e8c16d8f'
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
browser=(T/'verify_native_unified_plan_r347.mjs').read_text(encoding='utf-8')
browser=once(browser," const name='OWN_G_PLAN_R222_'+root.split('/').at(-1),exerciseName='OWN_G_EXERCISE_R222_'+root.split('/').at(-1);",r'''
 const name='OWN_G_PLAN_R222_'+root.split('/').at(-1),exerciseName='OWN_G_EXERCISE_R222_'+root.split('/').at(-1);
 const relationPrefix='OWN_REL_'+root.split('/').at(-1).toUpperCase();
 const relationKinds=[
  {entity:'materials',label:'应急物资',button:'新增应急物资',filter:'物资名称',nameKey:'materialName',tag:'MAT',ids:'emergencyGoodsManageIdList',list:'emergencyGoodsManageList',payload:{materialType:'1',materialModel:'OWN_REL_MODEL',materialQuantity:'4',unit:'件',storageLocation:'OWN_REL_STORE',person:'OWN_REL_PERSON',phone:'13800000000'}},
  {entity:'firstAidTeams',label:'应急队伍',button:'新增应急队伍',filter:'队伍名称',nameKey:'teamName',tag:'TEAM',ids:'emergencyTeamIdList',list:'emergencyTeamList',payload:{teamType:'OWN_REL_TEAM_TYPE',teamLocation:'OWN_REL_SITE',leaderName:'OWN_REL_LEADER',leaderPhone:'13800000000'}},
  {entity:'emergencyExperts',label:'应急专家',button:'新增应急专家',filter:'专家姓名',nameKey:'expertName',tag:'EXPERT',ids:'emergencyExpertIdList',list:'emergencyExpertList',payload:{expertPhone:'13800000000',expertField:'1',expertEducation:'OWN_DEGREE',expertMajor:'OWN_MAJOR',workingYears:'3'}}
 ];
 const memberKinds=[{title:'副指挥长',list:'emergencyPlanDeputyHeadList',nameKey:'deputyHeadName',fields:['副指挥长','副指挥长电话']},
  {title:'其他成员',list:'emergencyPlanOthermemberList',nameKey:'otherMemberName',fields:['其他成员','其他成员电话']},
  {title:'参与单位',list:'emergencyPlanCompanyList',nameKey:'planCompanyName',fields:['参与单位','单位负责人','单位负责人电话']}];
 async function resourceRequest(kind,operation,payload){
  if(!relationKinds.includes(kind)||!['save','getPage'].includes(operation))throw Error('ONLY_THIS_OWN_RESOURCE_KIND');
  const ua=await evaluate('navigator.userAgent');let url=wire.base+'/zhumadian/api/serv/'+kind.entity+'/'+operation;
  const options={headers:{Authorization:token,'User-Agent':ua},signal:AbortSignal.timeout(15000)};
  if(operation==='save'){
   if(![kind.ownA,kind.ownB].includes(payload[kind.nameKey])||Object.keys(payload).some(k=>!Object.keys({...kind.payload,[kind.nameKey]:''}).includes(k)))throw Error('ONLY_THIS_OWN_RESOURCE_BODY');
   options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(payload);
  }else url+='?current=1&size=5&'+kind.nameKey+'='+encodeURIComponent(payload);
  const response=await fetch(url,options),reply=await response.json();if(response.status!==200||reply.code!==0)throw Error('OWN_ORIGINAL_RESOURCE_API_'+kind.entity+'_'+response.status+'_'+reply.code);
  return reply.data;
 }
 for(const kind of relationKinds){
  kind.ownA=relationPrefix+'_'+kind.tag+'_A';kind.ownB=relationPrefix+'_'+kind.tag+'_B';kind.rows=[];
  for(const ownName of [kind.ownA,kind.ownB]){
   if(await resourceRequest(kind,'save',{...kind.payload,[kind.nameKey]:ownName})!==true)throw Error('OWN_RESOURCE_SAVE_NOT_TRUE');
   const page=await resourceRequest(kind,'getPage',ownName);
   if(Number(page.total)!==1||page.records[0][kind.nameKey]!==ownName||typeof page.records[0].id!=='string')throw Error('OWN_UNIQUE_RESOURCE_READBACK');
   kind.rows.push(page.records[0]);
  }
 }
 cases.push({case:'three-original-resource-save-APIs-create-six-owned-normal-role-fixtures',passed:true});
 const ownMemberValue=(kind,index,field,edited=false)=>field.includes('电话')?'13800000000':relationPrefix+'_'+kind.nameKey+'_'+index+(edited?'_EDIT':'');
 function memberRoot(title){return `Array.from(document.querySelectorAll('.form-list-item')).find(e=>e.getClientRects().length&&e.querySelector('.item-title')?.textContent.trim()===${JSON.stringify(title)})`;}
 async function memberFill(kind,index,edited=false){
  for(const field of kind.fields){const val=ownMemberValue(kind,index,field,edited);
   if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},row=g?.querySelectorAll('.item-form')[${index}],f=Array.from(row?.querySelectorAll('.el-form-item')||[]).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(field)}),input=f?.querySelector('input');if(!input||input.disabled||input.readOnly)return false;input.value=${JSON.stringify(val)};input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return input.value===${JSON.stringify(val)}})()`))throw Error('OWN_MEMBER_FIELD_'+kind.title+'_'+index+'_'+field);
  }
 }
 async function memberButton(kind,text){if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},b=Array.from(g?.querySelectorAll('.item-header button')||[]).find(e=>e.textContent.trim()===${JSON.stringify(text)});b?.click();return!!b})()`))throw Error('OWN_MEMBER_BUTTON_'+kind.title);}
 const pane=()=>`Array.from(document.querySelectorAll('.el-tab-pane')).find(e=>e.getClientRects().length&&e.querySelector('.el-table'))`;
 const picker=()=>`Array.from(document.querySelectorAll('.el-dialog')).find(e=>e.getClientRects().length&&e.querySelector('.el-dialog__title')?.textContent.trim()==='新增')`;
 async function resourceTab(kind){if(!await click('.el-tabs__item',kind.label))throw Error('OWN_RESOURCE_TAB_'+kind.entity);await until(()=>evaluate(`!!(${pane()})`));}
 async function selectedResourceCount(){return evaluate(`(${pane()})?.querySelectorAll('.el-table__body-wrapper tbody tr').length??-1`);}
 async function chooseResource(kind,which,expectedCount){
  await resourceTab(kind);if(!await click('button',kind.button))throw Error('OWN_RESOURCE_OPEN_'+kind.entity);
  await until(()=>evaluate(`!!(${picker()})?.querySelector('.table-search')`));
  await until(()=>evaluate(`!!(${picker()})?.querySelector('.el-dialog__footer button:last-child')?.disabled`));
  const ownName=which==='A'?kind.ownA:kind.ownB;
  if(!await evaluate(`(()=>{const d=${picker()},f=Array.from(d?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(kind.filter)}),e=f?.querySelector('input');if(!e)return false;e.value=${JSON.stringify(ownName)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));const b=Array.from(d.querySelectorAll('.table-search button')).find(e=>e.textContent.trim()==='搜索');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_FILTER_'+kind.entity);
  await until(()=>evaluate(`Array.from((${picker()})?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(e=>e.getClientRects().length).length===1&&Array.from((${picker()})?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).some(e=>e.textContent.includes(${JSON.stringify(ownName)}))`));
  if(!await evaluate(`(()=>{const d=${picker()},r=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).find(e=>e.textContent.includes(${JSON.stringify(ownName)})),b=r?.querySelector('.el-radio');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_RADIO_'+kind.entity);
  await until(()=>evaluate(`!(${picker()})?.querySelector('.el-dialog__footer button:last-child')?.disabled`));
  if(!await evaluate(`(()=>{const d=${picker()},b=Array.from(d?.querySelectorAll('.el-dialog__footer button')||[]).find(e=>e.textContent.trim()==='确定');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_CONFIRM_'+kind.entity);
  await until(()=>evaluate(`!(${picker()})`));await until(async()=>await selectedResourceCount()===expectedCount);
 }
 async function removeResourceA(kind){
  await resourceTab(kind);
  async function remove(){if(!await evaluate(`(()=>{const p=${pane()},r=Array.from(p?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).find(e=>e.textContent.includes(${JSON.stringify(kind.ownA)})),b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_REMOVE_BUTTON');await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("确认删除"))'));}
  await remove();if(!await click('.el-message-box__btns button','取消'))throw Error('OWN_RESOURCE_REMOVE_CANCEL');await until(async()=>await selectedResourceCount()===2);
  await remove();if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_RESOURCE_REMOVE_CONFIRM');await until(async()=>await selectedResourceCount()===1);
  if(!await evaluate(`(${pane()})?.textContent.includes(${JSON.stringify(kind.ownB)})===true`))throw Error('OWN_RESOURCE_REMOVE_RETAIN_B');
 }
 function checkRelations(record,edited){
  for(const kind of relationKinds){const expected=(edited?[kind.rows[1]]:kind.rows).map(r=>String(r.id)).sort();
   if(JSON.stringify((record[kind.ids]||[]).map(String).sort())!==JSON.stringify(expected)||JSON.stringify((record[kind.list]||[]).map(r=>String(r.id)).sort())!==JSON.stringify(expected))throw Error('OWN_RESOURCE_CANONICAL_IDS_AND_DETAILS_'+kind.entity);
   for(const row of record[kind.list])if(!kind.rows.some(r=>r.id===row.id&&r[kind.nameKey]===row[kind.nameKey]))throw Error('OWN_RESOURCE_DETAIL_METADATA_'+kind.entity);
  }
  for(const kind of memberKinds){const rows=record[kind.list];if(!Array.isArray(rows)||rows.length!==(edited?1:2))throw Error('OWN_MEMBER_COUNT_'+kind.title);
   const expected=Array.from({length:edited?1:2},(_,i)=>ownMemberValue(kind,i,kind.fields[0],edited)).sort();if(JSON.stringify(rows.map(r=>r[kind.nameKey]).sort())!==JSON.stringify(expected))throw Error('OWN_MEMBER_VALUES_'+kind.title);
  }
 }
''')
anchor=" await fill('指挥长电话','13800000000');await fill('处置措施','OWN_PLAN_MEASURES_R222');stage='actual-plan-create';"
browser=once(browser,anchor,r'''
 await fill('指挥长电话','13800000000');await fill('处置措施','OWN_PLAN_MEASURES_R222');
 stage='fill-original-six-plan-relation-groups';
 for(const kind of memberKinds){await memberFill(kind,0);await memberButton(kind,'新增'+kind.title);await until(()=>evaluate(`(${memberRoot(kind.title)})?.querySelectorAll('.item-form').length===2`));await memberFill(kind,1);}
 cases.push({case:'original-three-member-groups-two-real-form-rows-each-filled',passed:true});
 for(const kind of relationKinds){await chooseResource(kind,'A',1);await chooseResource(kind,'B',2);await chooseResource(kind,'A',2);cases.push({case:'original-'+kind.entity+'-picker-empty-guard-select-two-and-deduplicate',passed:true});}
 stage='actual-plan-create';
''')
anchor=" cases.push({case:'plan-native-create-original-controller-and-normal-role-detail-values',passed:true});"
browser=once(browser,anchor,anchor+"\n checkRelations(detail,false);cases.push({case:'all-six-plan-relation-groups-normal-save-and-original-detail-readback',passed:true});")
anchor=" await until(async()=>await value('应急预案名称')===name);await fill('处置措施','OWN_PLAN_REVISED_R222');"
browser=once(browser,anchor,anchor+r'''
 stage='edit-all-six-plan-relation-groups';
 for(const kind of memberKinds){await memberButton(kind,'删除');await until(()=>evaluate(`(${memberRoot(kind.title)})?.querySelectorAll('.item-form').length===1`));await memberFill(kind,0,true);}
 for(const kind of relationKinds)await removeResourceA(kind);
''')
anchor=" await filterOwn();detail=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));if(detail.disposalMeasures!=='OWN_PLAN_REVISED_R222')throw Error('PLAN_EDIT_NOT_PERSISTED');"
browser=once(browser,anchor,anchor+"\n checkRelations(detail,true);cases.push({case:'all-six-plan-relation-groups-edit-replace-and-canonical-ID-readback',passed:true});")
anchor=" cases.push({case:'plan-edit-reopen-detail-readonly-and-original-identity-kept',passed:true});await click('button','返回');await filterOwn();"
browser=once(browser,anchor,r'''
 for(const kind of memberKinds)if(!await evaluate(`(${memberRoot(kind.title)})?.textContent.includes(${JSON.stringify(ownMemberValue(kind,0,kind.fields[0],true))})===true`))throw Error('OWN_READONLY_MEMBER_VALUE_'+kind.title);
 for(const kind of relationKinds){await resourceTab(kind);if(await selectedResourceCount()!==1||!await evaluate(`(${pane()})?.textContent.includes(${JSON.stringify(kind.ownB)})===true&&!Array.from((${pane()})?.querySelectorAll('button')||[]).some(e=>e.getClientRects().length&&/新增|删除/.test(e.textContent))`))throw Error('OWN_READONLY_RESOURCE_'+kind.entity);}
 cases.push({case:'all-six-plan-relation-groups-actual-readonly-detail-renders-current-values',passed:true});
 cases.push({case:'plan-edit-reopen-detail-readonly-and-original-identity-kept',passed:true});await click('button','返回');await filterOwn();
''')
out=V/'verify_native_plan_six_relations_r374.mjs';assert not out.exists();out.write_text(browser,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(out)],capture_output=True);assert p.returncode==0
newd='native_plan_six_relations_r372_20261103/lifecycle';newo='plan-six-relations-r373'
sources=[]
for role,oldname in [('inspect','plan_lifecycle_inspect_r37_r346.py'),('prepare','plan_lifecycle_prepare_r37_r346.py'),('run','plan_lifecycle_run_r37_native_r347.py')]:
    text=(T/oldname).read_text(encoding='utf-8').replace('native_plan_unified_candidate_r39_20261103/lifecycle-r37',newd).replace('r39-actual-lifecycle-r37-r346',newo)
    if role=='run':
        text=text.replace("full-controller-r163/r145'","full-controller-r163/r147'").replace('verify_native_unified_plan_r347.mjs',out.name)
        text=text.replace('ab4f66f812ae3e35bb0e8aab608cbd77217ec8b193b06643f386cd3550519e00',sha(out))
        text=text.replace("len(result['cases'])==21","len(result['cases'])==29").replace("'cases':21","'cases':29")
        text=text.replace('OWN_FINAL_R39_NATIVE_21_CASES_WITH_DELETED_DETAIL_NAVIGATION_RETRY_REFRESH_PASSED','OWN_FINAL_R39_NATIVE_29_CASES_WITH_ALL_SIX_RELATIONS_AND_DELETED_DETAIL_PASSED')
        text=text.replace('candidate-native-ui-r347.json','candidate-native-ui-r374.json').replace('verified-lifecycle-r347.json','verified-lifecycle-r374.json')
        text=text.replace("'actualNormalRolePlanExerciseAndDeletedDetail21CasesPassed':True","'actualNormalRolePlanSixRelationsExerciseAndDeletedDetail29CasesPassed':True")
        text=once(text,"'exactFinalR39CandidateRuntime':True", "'allSixPlanRelationsActuallyCreatedEditedAndRenderedReadonly':True,'exactFinalR39CandidateRuntime':True")
    ast.parse(text);file=V/('plan_six_relations_'+role+'_r373.py');assert not file.exists();file.write_text(text,encoding='utf-8');sources.append({'role':role,'path':file.name,'sha256':sha(file)})
D.mkdir();proof={'preparedOnly':True,'onlyOwnedSyntheticG':True,'candidateUpdaterAndR39PayloadUnchanged':True,
 'browserSource':out.name,'browserSHA256':sha(out),'sources':sources,'expectedNormalRoleBrowserCases':29,
 'threeResourceKindsCreatedViaOriginalNormalRoleSaveAPIs':True,'sixRelationGroupsTwoToOneAndReadonlyToBeVerified':True,
 'actualLiveTestNotStarted':True,'publicFormalSceneOrDesktopTouched':False,'frozenR39AndPublic184ManifestsUnchanged':True}
(D/'prepared-r372.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
