import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [original,candidate,project,output]=process.argv.slice(2);
if(!original||!candidate||!project||!output||fs.existsSync(output))throw Error('EXACT_INPUTS_AND_FRESH_OUTPUT_REQUIRED');
const requireProject=createRequire(project+'/package.json');
const ts=requireProject('typescript');
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const pin='1cf19ad6707ee25fbcafe57365ec8ab8a55bef2fb06d1521dba0a988b3057681';
const raw=fs.readFileSync(original);if(sha(raw)!==pin)throw Error('PINNED_ORIGINAL_FORM_REQUIRED');
const cases=[];
function need(ok,message){if(!ok)throw Error(message);}
function context(file){
  const source=fs.readFileSync(file,'utf8');const matches=[...source.matchAll(/<script setup lang="tsx">([\s\S]*?)<\/script>/g)];need(matches.length===1,'EXACT_ORIGINAL_TSX_SCRIPT');
  let exposed;const scope={exports:{},Array,Error,JSON,React:{createElement(){throw Error('NO_UPLOAD_RENDER_OR_IO_ALLOWED');}},defineExpose:value=>{exposed=value;},require(name){
    if(name==='vue')return {ref:value=>({value}),reactive:value=>value};
    if(name==='element-plus')return {ElMessage:{success(){throw Error('NO_NOTIFICATION_OR_BUSINESS_API_ALLOWED');}}};
    if(name==='@/hooks/useDict')return {useDict:(group,keys)=>{need(group==='safetycode'&&JSON.stringify(keys)==='["qualificationCertificateType"]','ORIGINAL_DICTIONARY');return {qualificationCertificateType:{value:['原字典占位']}};}};
    if(name==='@/components/Upload/Img.vue')return {default:{}};
    throw Error('UNEXPECTED_IMPORT:'+name);
  }};
  const js=ts.transpileModule(matches[0][1],{compilerOptions:{target:ts.ScriptTarget.ES2020,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React}}).outputText;
  vm.runInNewContext(js+'\nglobalThis.__own={form,formRef,handleSubmit,dialogProps,visible};',scope,{timeout:1000,filename:'owned-original-component.js'});
  need(exposed&&typeof exposed.acceptParams==='function','ORIGINAL_EXPOSED_ENTRY');return {scope,exposed,own:scope.__own};
}
async function one(file,mode,name,expected){
  const {own,exposed}=context(file);let saved;
  exposed.acceptParams({title:'编辑',row:{id:'OWN_CERT',licenceCode:'OWN-CERT',licenceName:name,licenceType:'其他相关业务资质证书',startDate:'2026-10-28',endDate:'2026-10-29',url:''},callback:value=>{need(saved===undefined,'ONE_CALLBACK');saved=value;}});
  const col=own.form.columns.find(c=>c.prop==='licenceName');need(col.required===true&&own.form.columns.length===5,'ORIGINAL_REQUIRED_AND_COLUMN_COUNT');
  if(mode==='candidate')need(col.attrs.placeholder==='最多16个字符'&&Array.isArray(col.rules)&&col.rules[0].trigger.includes('blur')&&col.rules[0].trigger.includes('change'),'VISIBLE_HINT_AND_IMMEDIATE_RULE');
  own.formRef.value={async validate(){let valid=true;for(const c of own.form.columns)for(const rule of c.rules??[]){if(typeof rule.validator==='function')rule.validator({},own.form.field[c.prop],error=>{if(error){need(error.message==='证书名称不能超过16个字符','EXACT_VALIDATION_MESSAGE');valid=false;}});}return valid;}};
  await own.handleSubmit();need((saved!==undefined)===expected,'EXPECTED_ORIGINAL_COMPONENT_CONFIRM_RESULT');
  need(own.form.field.licenceName===name,'NO_SILENT_TRUNCATION');
  if(saved)need(saved.id==='OWN_CERT'&&saved.licenceName===name&&saved.startDate==='2026-10-28'&&saved.endDate==='2026-10-29'&&!('timeList' in saved)&&saved.url==='','ORIGINAL_CALLBACK_FIELDS_AND_DATE_PACKING');
  else need(own.visible.value===true,'INVALID_FORM_REMAINS_OPEN_FOR_CORRECTION');
  cases.push({mode,codePoints:Array.from(name).length,codeUnits:name.length,confirmed:expected,noSilentTruncation:true});
}
for(const [mode,file] of [['original',original],['candidate',candidate]]){
  for(const [name,valid] of [['A'.repeat(16),true],['A'.repeat(17),false],['安'.repeat(16),true],['安'.repeat(17),false],['😀'.repeat(16),true],['😀'.repeat(17),false],['',true]])await one(file,mode,name,mode==='original'||valid);
  const {own,exposed}=context(file);exposed.acceptParams({title:'新增',row:{},callback(){throw Error('DATE_FAILURE_MUST_NOT_CONFIRM');}});own.form.field.timeList=['2026-10-29','2026-10-28'];let error;
  own.form.columns.find(c=>c.prop==='timeList').rules[0].validator({},own.form.field.timeList,value=>{error=value;});need(error&&error.message==='结束时间不能早于或等于开始时间','ORIGINAL_DATE_RULE_UNCHANGED');cases.push({mode,case:'original-date-rule-preserved',passed:true});
}
need(sha(fs.readFileSync(original))===pin,'REFERENCE_UNCHANGED');
const result={cases,caseCount:cases.length,originalSourceSHA256:pin,candidateSourceSHA256:sha(fs.readFileSync(candidate)),actualOriginalComponentControlFunctionsExecuted:true,VueElementFormValidationHarness:true,realBrowserOrBackendVerified:false,networkOrUploadsOrAuthenticationUsed:false};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({caseCount:cases.length,originalMissingLengthRuleReproduced:true,candidateCodePointBoundaryAndCallbackPreserved:true}));
