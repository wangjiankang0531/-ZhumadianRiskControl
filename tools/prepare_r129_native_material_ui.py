from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r129';assert not C.exists();C.mkdir()
host=(T/'verify_full_controller_material_r128_20261101.py').read_text(encoding='utf-8')
host=host.replace("base=R/'work/event_delivery_consistency_20261030/full-controller-r128';base.mkdir(exist_ok=True)","prior_base=R/'work/event_delivery_consistency_20261030/full-controller-r128'\nbase=R/'work/event_delivery_consistency_20261030/full-controller-r129';base.mkdir(exist_ok=True)")
host=host.replace("default='original'","default='candidate'").replace("prepared_base=base/'candidate-install-r1'","prepared_base=prior_base/'candidate-install-r1'").replace("read(base/'material-excel-candidate-r1/candidate.json')","read(prior_base/'material-excel-candidate-r1/candidate.json')")
start=host.index("        if options.attempt=='r1':");end=host.index("        own=read(",start)
host=host[:start]+"        prior=read(prior_base/'r1/material-browser/failure.json')\n        assert any(x.get('ownUserMatched')and x.get('materialMenuReturned')for x in prior['http']),'OWN_MENUS_NOT_PREPARED'\n"+host[end:]
host=host.replace('verify_full_controller_material_browser_r128_20261101.mjs','verify_full_controller_material_browser_r129_20261101.mjs').replace('xnby.r128.full-controller-material.v1','xnby.r129.full-controller-material-ui.v1')
ast.parse(host);(T/'verify_full_controller_material_r129_20261101.py').write_text(host,encoding='utf-8')
js=(T/'verify_full_controller_material_browser_r128_20261101.mjs').read_text(encoding='utf-8').replace('full-controller-r128','full-controller-r129')
js=js.replace("&&!u.pathname.endsWith('/materials/importExcel')","&&!['/materials/importExcel','/materials/updateById'].some(p=>u.pathname.endsWith(p))")
js=js.replace("row.total=b.data?.total;}","row.total=b.data?.total;}\n   if(row.path.endsWith('/materials/updateById'))row.saved=b.data;")
start=js.index(" stage='download-template';");end=js.index(" await Promise.allSettled([...reads]);await fs.writeFile(O+'/result.json'",start)
business=r'''
 const formValue=label=>evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
 const fill=async(label,value)=>{if(!await evaluate(`(()=>{const a=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return true})()`))throw Error('OWN_FORM_FIELD_NOT_EDITABLE_'+label)};
 const filter=async name=>{const n=http.filter(x=>x.path.endsWith('/materials/getPage')).length;await fill('物资名称',name);if(!await click('.table-search button','搜索'))throw Error('OWN_NATIVE_SEARCH_BUTTON');await until(()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length>n);await until(()=>evaluate('!document.querySelector(".el-loading-mask")'));await Promise.allSettled([...reads]);return http.filter(x=>x.path.endsWith('/materials/getPage')).at(-1)};
 const rowAction=async text=>{if(!await evaluate(`(()=>{const row=document.querySelector('.el-table__body-wrapper tbody tr');const b=Array.from(row?.querySelectorAll('button')||[]).find(x=>x.textContent.trim()===${JSON.stringify(text)});if(!b)return false;b.click();return true})()`))throw Error('OWN_NATIVE_ROW_ACTION_'+text)};
 const listReady=()=>until(()=>evaluate('location.pathname.endsWith("/emergencyResources/materials")&&!!document.querySelector(".table-search")'));
 stage='actual-list-filter';const filtered=await filter('OWN_F_MAT_r7_valid_');if(Number(filtered.total)!==6)throw Error('NATIVE_UI_FILTER_NOT_SIX');
 if(!await evaluate('Array.from(document.querySelectorAll(".el-table__body-wrapper tbody tr")).every(e=>e.textContent.includes("OWN_F_MAT_r7_valid_"))'))throw Error('NATIVE_UI_FILTER_ROWS_WRONG');
 cases.push({case:'native-list-name-filter-and-six-original-synthetic-rows',passed:true,rows:6});
 stage='actual-detail-click';await rowAction('详情');await until(async()=>String(await formValue('物资名称')).startsWith('OWN_F_MAT_r7_valid_'));
 if(await formValue('物资数量')!=='12'||await formValue('物资型号')!=='OWN_MODEL')throw Error('NATIVE_DETAIL_FIELDS_WRONG');
 const originalName=await formValue('物资名称');cases.push({case:'native-row-detail-renders-original-imported-fields',passed:true});
 if(!await click('button','返回'))throw Error('OWN_DETAIL_BACK');await listReady();
 stage='actual-filter-reset';let n=http.filter(x=>x.path.endsWith('/materials/getPage')).length;if(!await click('.table-search button','重置'))throw Error('OWN_NATIVE_RESET');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/getPage')).length>n);if(await formValue('物资名称')!=='')throw Error('NATIVE_RESET_DID_NOT_CLEAR');cases.push({case:'native-list-reset-clears-name-filter',passed:true});
 stage='actual-edit-save';await filter(originalName);await rowAction('编辑');await until(async()=>await formValue('物资名称')===originalName);
 const editedName='OWN_F_UI_R129_'+root.split('/').at(-1);await fill('物资名称',editedName);await fill('物资数量','23');
 n=http.filter(x=>x.path.endsWith('/materials/updateById')).length;if(!await click('button','提交'))throw Error('OWN_EDIT_SUBMIT');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/updateById')).length>n);await listReady();
 const response=http.filter(x=>x.path.endsWith('/materials/updateById')).at(-1);if(response.businessCode!==0||response.saved!==true)throw Error('NATIVE_EDIT_NOT_ACTUALLY_SAVED');
 const edited=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(editedName));if(Number(edited.total)!==1||String(edited.records[0].materialQuantity)!=='23')throw Error('NATIVE_EDIT_READBACK');
 cases.push({case:'native-edit-submit-and-original-API-confirmed-values',passed:true,actualRequests:1});
 stage='actual-edit-detail-reopen';await filter(editedName);await rowAction('详情');await until(async()=>await formValue('物资名称')===editedName);
 if(await formValue('物资数量')!=='23')throw Error('NATIVE_REOPEN_DETAIL_STALE');cases.push({case:'native-reopened-detail-shows-saved-edit',passed:true});await click('button','返回');await listReady();
 // Load an editor, then delete that same synthetic record through another real UI tab.
 stage='stale-editor-open';await filter(editedName);await rowAction('编辑');await until(async()=>await formValue('物资名称')===editedName);const editorSession=session;
 const second=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:second.targetId,flatten:true})).sessionId;
 await send('Page.enable',{},session);await send('Runtime.enable',{},session);await send('Network.enable',{},session);await send('DOM.enable',{},session);await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Page.navigate',{url:wire.base+'/zhumadian/emergency/emergencyResources/materials'},session);await listReady();await filter(editedName);await rowAction('删除');
 await until(()=>evaluate('!!document.querySelector(".el-message-box")'));n=http.filter(x=>x.path.endsWith('/materials/removeById')).length;if(!await click('.el-message-box button','确定'))throw Error('OWN_NATIVE_DELETE_CONFIRM');
 await until(()=>http.filter(x=>x.path.endsWith('/materials/removeById')).length>n);const removed=await ownAPI('/getPage?current=1&size=5&materialName='+encodeURIComponent(editedName));if(Number(removed.total)!==0)throw Error('NATIVE_DELETE_NOT_APPLIED');
 cases.push({case:'native-delete-confirm-removes-only-selected-own-synthetic-row',passed:true});
 session=editorSession;stage='actual-code-zero-false-save';await fill('物资数量','24');n=http.filter(x=>x.path.endsWith('/materials/updateById')).length;await click('button','提交');await until(()=>http.filter(x=>x.path.endsWith('/materials/updateById')).length>n);await sleep(500);
 const stale=http.filter(x=>x.path.endsWith('/materials/updateById')).at(-1);if(stale.businessCode!==0||stale.saved!==false)throw Error('NATIVE_FALSE_RESULT_NOT_REPRODUCED');
 const onEditor=await evaluate('location.pathname.endsWith("/materials/edit")');
 await fs.writeFile(O+'/stale-save-baseline.json',JSON.stringify({originalActualCodeZeroFalse:true,editorRetained:onEditor,falseSaveNavigatedAsSuccess:!onEditor,syntheticRowRemainedAbsent:Number((await ownAPI('/getPage?current=1&size=1&materialName='+encodeURIComponent(editedName))).total)===0},null,2));
 cases.push({case:'actual-server-false-result-baseline-recorded',passed:true,originalDefectReproduced:!onEditor});
'''
js=js[:start]+business+js[end:]
js=js.replace("baselineDefectReproduced:wire.variant!=='candidate',productFixed:wire.variant==='candidate'","baselineDefectReproduced:cases.some(x=>x.originalDefectReproduced),productFixed:false")
(T/'verify_full_controller_material_browser_r129_20261101.mjs').write_text(js,encoding='utf-8')
print(json.dumps({'newRoot':str(C),'newTools':2,'r128AndFixedPublicSnapshotUnchanged':True,'productCodeChanged':False}))
