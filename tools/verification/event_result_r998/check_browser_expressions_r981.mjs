import fs from'node:fs/promises';import vm from'node:vm';import{createRequire}from'node:module';
const require=createRequire('D:/Project/Zhumadian/Application/work/tianjin_native_20261023/emergency_pc/package.json'),ts=require('typescript');
const file=process.argv[2],out=process.argv[3];if(!file?.startsWith('D:/CodexData/home/visualizations/')||!out?.startsWith('D:/CodexData/home/visualizations/'))throw Error('OWN_STATIC_SOURCE_PATH_REQUIRED');
const source=await fs.readFile(file,'utf8'),tree=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),rows=[];
function walk(n){if(ts.isCallExpression(n)&&ts.isIdentifier(n.expression)&&n.expression.text==='evaluate'){
 const arg=n.arguments[0];let expression=null;
 if(arg&&ts.isStringLiteralLike(arg))expression=arg.text;
 else if(arg&&ts.isTemplateExpression(arg)){expression=arg.head.text;for(const s of arg.templateSpans){const text=s.expression.getText(tree);expression+=(text.startsWith('JSON.stringify(')?'"OWN_SYNTHETIC_PARSE_VALUE"':'null')+s.literal.text}}
 if(expression!==null){const line=tree.getLineAndCharacterOfPosition(n.getStart(tree)).line+1;try{new vm.Script(expression);rows.push({line,passed:true})}catch(e){rows.push({line,passed:false,type:e.name,message:e.message})}}
 }ts.forEachChild(n,walk)}walk(tree);
if(rows.length<15)throw Error('EXPECTED_EVENT_BROWSER_EXPRESSION_COVERAGE');
const result={passed:rows.every(r=>r.passed),checkedLiteralOrTemplateEvaluationExpressions:rows.length,rows,sourceCodeExecuted:false,templateSpansUseSyntheticParsePlaceholders:true,notRuntimeUIAcceptance:true};
await fs.writeFile(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});process.stdout.write(JSON.stringify({passed:result.passed,expressions:rows.length,failures:rows.filter(r=>!r.passed)}));if(!result.passed)process.exitCode=1;
