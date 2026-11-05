import fs from'node:fs/promises';import{createRequire}from'node:module';import{createHash}from'node:crypto';
const require=createRequire('D:/Project/Zhumadian/Application/work/tianjin_native_20261023/emergency_pc/package.json'),ts=require('typescript'),sfc=require('@vue/compiler-sfc'),dom=require('@vue/compiler-dom');
const root='D:/Project/Zhumadian/Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/敏捷应急管理前台代码/agile-emergency-response-dev/src/views/emergencyResponse';
const rows=[];
for(const [name,expected,disabledHandlers]of [['response',['新增','详情','编辑','研判','删除'],['handleEventReport','handleDown']],['taskSend',['新增','详情','编辑','处置','删除'],['handleDown']],['disposal',['详情','处置','完成'],[]]]){
 const file=root+'/'+name+'/index.vue',raw=await fs.readFile(file),parsed=sfc.parse(raw.toString('utf8'),{filename:file});if(parsed.errors.length)throw Error('SFC_PARSE');const template=parsed.descriptor.template.content,tree=dom.baseParse(template),buttons=[];
 function text(n){return n.type===dom.NodeTypes.TEXT?n.content:(n.children??[]).map(text).join('')}
 function walk(n){if(n.type===dom.NodeTypes.ELEMENT&&n.tag==='el-button')buttons.push(text(n).trim());for(const x of n.children??[])walk(x)}walk(tree);
 for(const label of expected)if(!buttons.includes(label))throw Error('ACTIVE_SOURCE_CONTROL_MISSING:'+name+':'+label);
 for(const label of ['信息报送','导出列表','Excel导入','下载模板'])if(buttons.includes(label))throw Error('PREVIOUSLY_DISABLED_CONTROL_ACTIVATED:'+name+':'+label);
 const compiled=sfc.compileTemplate({source:template,filename:file,id:'original-enable-r973'});if(compiled.errors.length)throw Error('TEMPLATE_COMPILE');const script=ts.createSourceFile(name+'-render.js',compiled.code,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS);if(script.parseDiagnostics.length)throw Error('COMPILED_JS_PARSE');const refs=new Set();function scan(n){if(ts.isIdentifier(n))refs.add(n.text);ts.forEachChild(n,scan)}scan(script);
 for(const handler of disabledHandlers)if(refs.has(handler))throw Error('DISABLED_HANDLER_COMPILED_ACTIVE:'+handler);
 rows.push({page:name,sourceFile:file,sourceSHA256:createHash('sha256').update(raw).digest('hex'),actualSourceElementButtonLabels:buttons,disabledLabelsNotElementNodes:['信息报送','导出列表','Excel导入','下载模板'],disabledHandlersAbsentFromCompiledRenderIdentifiers:disabledHandlers,templateCompiled:true,sourceEnablementOnlyNotRuntimeRoleOrAcceptance:true});
}
const proof={passed:true,originalSourceAndCompiledRenderASTChecked:true,commentTextNotTreatedAsRenderedButtonOrHandler:true,rows,legacyInactiveFeaturesNotDeclaredMissing:true,servicesDatabaseBusinessOrDesktopUsed:false,fullCloneReady:false};const p=new URL('./original-action-enablement-r973.json',import.meta.url);try{await fs.access(p);throw Error('EXISTS')}catch(e){if(e.code!=='ENOENT')throw e}await fs.writeFile(p,JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({passed:true,pages:3,disabledFeaturesRemainOutsideActiveOriginalUI:true}));
