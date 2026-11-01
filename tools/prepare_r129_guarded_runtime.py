from pathlib import Path
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';p=T/'verify_full_controller_material_r129_20261101.py';s=p.read_text(encoding='utf-8')
s=s.replace("choices=['original','candidate']","choices=['original','candidate','guarded']")
s=s.replace("if options.variant=='candidate':prepared_base=prior_base/'candidate-install-r1'","if options.variant=='candidate':prepared_base=prior_base/'candidate-install-r1'\nif options.variant=='guarded':prepared_base=base/'candidate-install-r1'")
s=s.replace("if options.variant=='candidate':","if options.variant in ['candidate','guarded']:")
# The one-line preparation selector must still choose WF7 for baseline; guarded selects WF9 afterward.
s=s.replace("if options.variant in ['candidate','guarded']:prepared_base=prior_base/'candidate-install-r1'","if options.variant=='candidate':prepared_base=prior_base/'candidate-install-r1'")
p.write_text(s,encoding='utf-8')
p=T/'verify_full_controller_material_browser_r129_20261101.mjs';s=p.read_text(encoding='utf-8')
anchor=" cases.push({case:'actual-server-false-result-baseline-recorded',passed:true,originalDefectReproduced:!onEditor});"
replacement=""" if(wire.variant==='guarded'){
  if(!onEditor||await formValue('物资数量')!=='24')throw Error('FALSE_SAVE_DID_NOT_KEEP_ORIGINAL_EDITOR_AND_INPUT');
  if(!await evaluate('document.body.innerText.includes("保存未完成，请保留当前内容")'))throw Error('FALSE_SAVE_NOTICE_MISSING');
  cases.push({case:'actual-server-code-zero-false-keeps-editor-values-and-shows-failure',passed:true});
 }else cases.push({case:'actual-server-false-result-baseline-recorded',passed:true,originalDefectReproduced:!onEditor});"""
assert s.count(anchor)==1;s=s.replace(anchor,replacement)
anchor="await listReady();await filter(editedName);await rowAction('删除');"
replacement="""await listReady();await filter(editedName);
 if(wire.variant==='guarded'){
  const beforeCancel=http.filter(x=>x.path.endsWith('/materials/removeById')).length;await rowAction('删除');await until(()=>evaluate('!!document.querySelector(".el-message-box")'));
  if(!await click('.el-message-box button','取消'))throw Error('OWN_DELETE_CANCEL');await until(()=>evaluate('!document.querySelector(".el-message-box")'));await sleep(200);
  if(http.filter(x=>x.path.endsWith('/materials/removeById')).length!==beforeCancel)throw Error('CANCELLED_DELETE_STILL_CALLED_SERVER');
  if(Number((await ownAPI('/getPage?current=1&size=1&materialName='+encodeURIComponent(editedName))).total)!==1)throw Error('CANCELLED_DELETE_CHANGED_ROW');
  cases.push({case:'native-cancel-delete-keeps-own-row-and-sends-zero-delete',passed:true});
 }
 await rowAction('删除');"""
assert s.count(anchor)==1;s=s.replace(anchor,replacement)
s=s.replace('productFixed:false','productFixed:wire.variant===\'guarded\'')
p.write_text(s,encoding='utf-8');print('R129_GUARDED_RUNTIME_SELECTS_NEW_EXACT_FIXTURE_AND_REAL_FALSE_OR_CANCEL_CASES')
