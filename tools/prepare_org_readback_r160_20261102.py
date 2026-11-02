from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r159'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(R/'_g/own-fixture.json')['ownedSyntheticFixtureOnly'] and not(R/'_g/user-manual-protected.json').exists()
assert J(C/'r1/controller-terminal.json')['exitCode']==0 and J(C/'r1-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert not(C/'r2').exists() and not(C/'prepared-r2').exists()
ready=J(C/'prepared-r1/controller-fixture-ready.json');assert sha(R/'_g/Application/release-manifest.json')==ready['releaseSHA256']
P=C/'prepared-r2';P.mkdir();(P/'controller-fixture-ready.json').write_bytes((C/'prepared-r1/controller-fixture-ready.json').read_bytes());(P/'own-serial-definition.json').write_bytes((C/'prepared-r1/own-serial-definition.json').read_bytes())
p=V/'verify_org_native_diagnostic_r159_20261102.mjs';s=p.read_text(encoding='utf-8');before=sha(p)
s=s.replace("row.nativeRootMatchesKnownOwnCompany=nativeRoot==='a5310000000000000000000000000001';", "row.nativeRootMatchesKnownOwnCompany=nativeRoot==='a5310000000000000000000000000001';row.nativeRootRepresentation=Array.isArray(nativeRoot)?'array':typeof nativeRoot;row.nativeRootArrayContainsKnownOwnCompany=Array.isArray(nativeRoot)&&nativeRoot.includes('a5310000000000000000000000000001');")
anchor='const row={path:u.pathname,method:r.method};'
assert s.count(anchor)==1
s=s.replace(anchor,"const row={path:u.pathname,method:r.method};if(u.pathname.endsWith('/serv/riskLevel/getPage')){const dept=u.searchParams.get('department')||'';row.departmentQuery=dept===''?'none':dept==='Own risk department A'?'ownA':dept==='Own risk department B'?'ownB':'unexpected';}")
old="const result={httpStatus:row.httpStatus,code:b.code,arrayRows:Array.isArray(rows),rows:Array.isArray(rows)?rows.length:null,allRowsOwnDepartmentA:Array.isArray(rows)&&rows.length>0&&rows.every(x=>x.department==='Own risk department A')};"
new="const result={httpStatus:row.httpStatus,code:b.code,departmentQuery:row.departmentQuery,arrayRows:Array.isArray(rows),rows:Array.isArray(rows)?rows.length:null,total:Number.isFinite(b.data?.total)?b.data.total:null,allRowsOwnDepartmentA:Array.isArray(rows)&&rows.length>0&&rows.every(x=>x.department==='Own risk department A'),allRowsOwnDepartmentB:Array.isArray(rows)&&rows.length>0&&rows.every(x=>x.department==='Own risk department B'),mixedOwnDepartments:Array.isArray(rows)&&rows.some(x=>x.department==='Own risk department A')&&rows.some(x=>x.department==='Own risk department B')};"
assert s.count(old)==1;s=s.replace(old,new)
a=s.index(" stage='native-current-organization-root-readback';")
b=s.index(" await fs.writeFile(O+'/original-selector-owned.png'",a)
body=r'''
 stage='persist-original-observation-before-root-hypotheses';
 const baseline=riskReads.at(-1);
 await fs.writeFile(O+'/baseline-organization-diagnostic.json',JSON.stringify({selector:box,options,originalTreeRequests:treeReads,baselineRiskRead:baseline,normalOwnUserMetadata:http.filter(x=>x.path.endsWith('/oauth/CurrentUser')),noProductChange:true},null,2));
 check(!box.disabled,'unrestricted-own-fixture-user-selector-enabled');
 check(options.ownDepartmentA&&options.ownDepartmentB,'original-configured-root-contains-both-expected-own-departments');
 check(baseline.httpStatus===200&&baseline.code===0&&baseline.rows>0&&baseline.mixedOwnDepartments,'baseline-unfiltered-own-risk-rows-contain-both-departments');
 stage='compare-known-own-company-without-claiming-native-root-shape';
 const agent=await evaluate('navigator.userAgent');
 const response=await fetch(wire.base+'/zhumadian/api/jnpf/permission/Organize/getTree/a5310000000000000000000000000001',{headers:{Authorization:normalToken,'User-Agent':agent}});
 const current=await response.json();const rootRead={httpStatus:response.status,...summarizeTree(current),queriedKnownSyntheticCompanyNotAssumedNativeRoot:true};
 async function fieldState(){return evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim().startsWith("责任部门"));return{inputValue:f?.querySelector("input")?.value||"",selectedText:f?.textContent||""}})()');}
 async function selectDepartment(label){
  const isVisible=await evaluate('Array.from(document.querySelectorAll(".el-select__popper .el-tree-node__label")).some(e=>e.getClientRects().length&&e.textContent.trim()==='+JSON.stringify(label)+')');
  if(!isVisible){check(await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim().startsWith("责任部门"));const e=f?.querySelector("input");if(!e)return false;e.click();return true})()'),'open-original-selector-for-'+label);await until(()=>evaluate('Array.from(document.querySelectorAll(".el-select__popper .el-tree-node__label")).some(e=>e.getClientRects().length&&e.textContent.trim()==='+JSON.stringify(label)+')'));}
  check(await evaluate('(()=>{const n=Array.from(document.querySelectorAll(".el-select__popper .el-tree-node__label")).filter(e=>e.getClientRects().length&&e.textContent.trim()==='+JSON.stringify(label)+');if(n.length!==1)return false;n[0].click();return true})()'),'click-native-tree-option-'+label);
  await until(async()=>{const f=await fieldState();return f.inputValue===label||f.selectedText.includes(label);});
 }
 async function clickSearchButton(label){check(await evaluate('(()=>{const b=Array.from(document.querySelectorAll("button")).filter(e=>e.getClientRects().length&&e.textContent.trim()==='+JSON.stringify(label)+');if(b.length!==1)return false;b[0].click();return true})()'),'click-original-'+label);}
 async function departmentDOM(label){return evaluate('(()=>{const rows=Array.from(document.querySelectorAll(".el-table__body-wrapper tr.el-table__row")).filter(e=>e.getClientRects().length);const labels=rows.map(r=>r.querySelectorAll("td")[1]?.textContent.trim());return{visibleRows:rows.length,allExpected:rows.length>0&&labels.every(v=>v==='+JSON.stringify(label)+'),mixedOwnDepartments:labels.includes("Own risk department A")&&labels.includes("Own risk department B")}})()');}
 const functionalReads=[];
 for(const[label,queryKey,allKey]of[['Own risk department A','ownA','allRowsOwnDepartmentA'],['Own risk department B','ownB','allRowsOwnDepartmentB']]){
  stage='original-ui-select-and-filter-'+queryKey;
  await selectDepartment(label);const before=riskReads.length;await clickSearchButton('搜索');await until(()=>riskReads.length>before);const result=riskReads.at(-1);
  check(result.httpStatus===200&&result.code===0&&result.departmentQuery===queryKey&&result[allKey]&&result.rows>0,'native-http-filter-'+queryKey,result);
  await until(async()=>(await departmentDOM(label)).allExpected);const dom=await departmentDOM(label);check(dom.allExpected,'actual-original-table-filter-'+queryKey,dom);functionalReads.push({department:queryKey,result,dom});
 }
 stage='original-ui-reset-restores-unfiltered-list';const before=riskReads.length;await clickSearchButton('重置');await until(()=>riskReads.length>before);const reset=riskReads.at(-1);
 check(reset.httpStatus===200&&reset.code===0&&reset.departmentQuery==='none'&&reset.mixedOwnDepartments&&reset.total===baseline.total,'native-reset-restores-original-unfiltered-total',reset);
 await until(async()=>(await departmentDOM('')).mixedOwnDepartments);const resetDOM=await departmentDOM('');check(resetDOM.mixedOwnDepartments,'actual-original-table-reset-restores-both-departments',resetDOM);
 check(!http.some(x=>x.path.startsWith('/zhumadian/api/serv/riskLevel/')&&['save','updateById','removeById','importExcel'].includes(x.path.split('/').at(-1))),'no-risk-business-write-request');
 check(exceptions.length===0,'no-unhandled-original-risk-page-runtime-exception');
 const functional={originalConfiguredRootOptionsCorrect:true,actualDepartmentAAndBSelectionAndSearchPassed:true,actualResetRestoresOriginalMixedListAndTotal:true,wrongDeploymentOrgRootReproduced:false};
 await fs.writeFile(O+'/organization-diagnostic.json',JSON.stringify({diagnosticCompleted:true,sourceOriginalUnchanged:true,selector:box,options,originalTreeRequests:treeReads,knownOwnCompanyComparison:rootRead,functional,functionalReads,baselineRiskRead:baseline,resetRiskRead:reset,resetDOM,riskReads,normalOwnUserOnly:true,nativeRootStringAssumptionRemoved:true,businessRowsCreatedEditedOrImported:false,publicG9ReproducedOrResolved:false},null,2));
'''
s=s[:a]+body+s[b:];p.write_text(s,encoding='utf-8')
ast.parse((V/'verify_org_controller_r159_20261102.py').read_text(encoding='utf-8'))
(P/'diagnostic-source-pins.json').write_text(json.dumps({'beforeObserverSHA256':before,'browserSHA256':sha(p),'hostSHA256':sha(V/'verify_org_controller_r159_20261102.py'),'noProductConfigurationOrDatabaseBusinessRowsChanged':True,'preparedOnly':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'attempt':'r2','originalR1EvidenceKept':True,'nativeRootStringAssumptionRemoved':True,'actualDepartmentAAndBSearchAndResetPrepared':True,'noProductChange':True}))
