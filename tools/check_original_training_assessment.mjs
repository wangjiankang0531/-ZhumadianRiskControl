import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const [original,candidate,project,output]=process.argv.slice(2);
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const pin='72cc138530ffdc0b27390938fcc3faa3fa8105881b70665d786b2677136a2c0d';
function need(ok,code){if(!ok)throw Error(code);}
need(original&&candidate&&project&&output&&!fs.existsSync(output),'EXACT_INPUTS_FRESH_OUTPUT');
need(sha(fs.readFileSync(original))===pin,'PINNED_ORIGINAL_FORM');
const requireProject=createRequire(project+'/package.json'),ts=requireProject('typescript'),cases=[];
function context(file,users){
  const raw=fs.readFileSync(file,'utf8'),matches=[...raw.matchAll(/<script setup lang="tsx">([\s\S]*?)<\/script>/g)];need(matches.length===1,'EXACT_TSX');
  let exposed,lookup;
  const scope={exports:{},JSON,React:{createElement(){throw Error('NO_RENDER_IO');}},defineExpose:x=>{exposed=x;},require(name){
    if(name==='vue')return {ref:value=>({value}),reactive:value=>value};
    if(name==='@/api/work/workUserExtend')return {getPage:params=>{need(JSON.stringify(params)==='{"current":1,"size":999,"type":"否"}','ORIGINAL_PERSONNEL_QUERY');return new Promise(resolve=>{lookup=()=>resolve({data:{records:users}});});}};
    throw Error('UNEXPECTED_IMPORT:'+name);
  }};
  const js=ts.transpileModule(matches[0][1],{compilerOptions:{target:ts.ScriptTarget.ES2020,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React}}).outputText;
  vm.runInNewContext(js+'\nglobalThis.__own={form,formRef,handleSubmit,visible,workUserChange};',scope,{timeout:1000});
  return {own:scope.__own,exposed,resolve:async()=>{need(lookup,'ORIGINAL_LOOKUP_STARTED');lookup();await Promise.resolve();await Promise.resolve();}};
}
const row=()=>({id:'OWN_CHILD',examId:'OWN_EXAM',userId:'OWN_USER',realName:'合成姓名',departName:'原部门',userExamScore:'80.0',userExamResult:'1',userExamBeginTime:'2026-10-28 15:10:00',userExamFinishTime:'2026-10-28 15:50:00'});
const users=[{id:'OWN_USER',userName:'当前选项名称',userCard:'OWN-CARD',thirdUnit:'当前选项部门'},{id:'OTHER_USER',userName:'其他合成人员',userCard:'OTHER-CARD',thirdUnit:'其他部门'}];
for(const [mode,file] of [['original',original],['candidate',candidate]]){
  async function runCase(name,initial,choices,check){const c=context(file,choices);let saved;c.exposed.acceptParams({title:'编辑',row:initial,callback:value=>{need(saved===undefined,'ONE_CALLBACK');saved=value;}});await c.resolve();await check(c,value=>{saved=value;},()=>saved);cases.push({mode,name,passed:true});}
  await runCase('saved-row-time-and-identity-rehydration',row(),users,async c=>{
    const f=c.own.form.field;
    need(f.realName==='合成姓名'&&f.departName==='原部门'&&f.userExamScore==='80.0','NO_STORED_FIELDS_OVERWRITE');
    need((Array.isArray(f.userTime)&&f.userTime[0]===row().userExamBeginTime&&f.userTime[1]===row().userExamFinishTime)===(mode==='candidate'),'TIME_REHYDRATION');
    need((f.idCard==='OWN-CARD')===(mode==='candidate'),'IDENTITY_REHYDRATION');
    const dateColumn=c.own.form.columns.find(x=>x.prop==='userTime'),identityColumn=c.own.form.columns.find(x=>x.prop==='idCard');need(dateColumn.required&&identityColumn.required&&identityColumn.rules.includes('idCard'),'ORIGINAL_REQUIRED_RULES');
  });
  await runCase('score-only-confirm-without-reselecting-user',row(),users,async(c,_set,get)=>{
    c.own.form.field.userExamScore='85';c.own.formRef.value={validate:async()=>Boolean(c.own.form.field.idCard&&c.own.form.field.userTime?.length===2)};
    await c.own.handleSubmit();const saved=get();need(Boolean(saved)===(mode==='candidate'),'CONFIRM_RESULT');
    if(saved)need(saved.userId==='OWN_USER'&&saved.examId==='OWN_EXAM'&&saved.userExamScore==='85'&&saved.userExamBeginTime===row().userExamBeginTime&&saved.userExamFinishTime===row().userExamFinishTime&&!('userTime' in saved),'ORIGINAL_SUBMIT_SHAPE_AND_TIMES');
    else need(c.own.visible.value===true,'INVALID_MODAL_REMAINS');
  });
  await runCase('existing-identity-kept',{...row(),idCard:'EXISTING-CARD'},users,async c=>need(c.own.form.field.idCard==='EXISTING-CARD','NO_IDENTITY_OVERWRITE'));
  await runCase('unknown-user-remains-required',{...row(),userId:'NOT_IN_CURRENT_OPTIONS'},users,async c=>need(!c.own.form.field.idCard,'NO_UNKNOWN_USER_IDENTITY_FABRICATION'));
  await runCase('empty-options-do-not-fabricate',row(),[],async c=>need(!c.own.form.field.idCard,'NO_EMPTY_OPTIONS_IDENTITY'));
  await runCase('new-row-remains-empty',{},users,async c=>need(!c.own.form.field.userId&&!c.own.form.field.idCard,'NO_AUTO_SELECT_PERSON'));
  await runCase('partial-time-stays-empty',{...row(),userExamFinishTime:null},users,async c=>need(mode==='original'?c.own.form.field.userTime===undefined:c.own.form.field.userTime.length===0,'NO_PARTIAL_TIME_FABRICATION'));
  await runCase('original-user-selection-behaviour',row(),users,async c=>{c.own.workUserChange('OTHER_USER');need(c.own.form.field.realName==='其他合成人员'&&c.own.form.field.idCard==='OTHER-CARD'&&c.own.form.field.departName==='其他部门','ORIGINAL_SELECTION_BEHAVIOUR');});
  const c=context(file,users);c.exposed.acceptParams({title:'编辑',row:row(),callback(){}});c.exposed.acceptParams({title:'编辑',row:{...row(),userId:'OTHER_USER',realName:'第二条合成姓名'},callback(){}});await c.resolve();need((c.own.form.field.idCard==='OTHER-CARD')===(mode==='candidate'),'LOOKUP_APPLIES_CURRENT_SELECTION');need(c.own.form.field.realName==='第二条合成姓名','LATE_LOOKUP_NO_NAME_OVERRIDE');cases.push({mode,name:'lookup-current-row-identity',passed:true});
}
need(sha(fs.readFileSync(original))===pin,'REFERENCE_UNCHANGED');
fs.writeFileSync(output,JSON.stringify({caseCount:cases.length,cases,sourceSHA256:pin,candidateSHA256:sha(fs.readFileSync(candidate)),actualOriginalComponentFunctionsExecuted:true,syntheticClosedVMOnly:true,browserBackendOrAuthenticationUsed:false},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({cases:cases.length,originalMissingTimeAndIdentityReproduced:true,candidateScoreOnlyEditPreservesTimes:true}));
