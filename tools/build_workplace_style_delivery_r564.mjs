import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
const R='D:/Project/Zhumadian', A=R+'/Application', S=A+'/work/tianjin_native_20261023/security_pc';
const D=R+'/Document/Deployment/workplace_style_delivery_r564_20261104', O=R+'/work/workplace-style-delivery-r564';
const req=createRequire(S+'/package.json'), sfc=req('@vue/compiler-sfc'), sass=req('sass'), postcss=req('postcss');
const J=async p=>JSON.parse(await fs.readFile(p,'utf8')), sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=(await J(R+'/work/r42-mapper-equivalence-r457/r37/bundle/payload/payload-manifest.json')).files;
const resolution=(await J(R+'/work/r39-full-preflight-r37-r341/resolution.json')).programs;
const sourcePins=await J(R+'/Document/Deployment/tester_feedback_refresh_r486_20261104/chart-header-candidate-r489.json');
await assert.rejects(()=>fs.stat(D));await assert.rejects(()=>fs.stat(O));
async function frozen(n){
 const p=manifest[n];assert(p);
 const candidates=[R+'/_g/Application/'+n,A+'/'+n,resolution[n]?.source].filter(Boolean);
 for(const source of candidates){let bytes;try{bytes=await fs.readFile(source)}catch{continue}if(bytes.length===p.bytes&&sha(bytes)===p.sha256)return{source,bytes,relative:n,pin:p}}
 throw Error('MISSING_EXACT_BASE_FILE:'+n);
}
const charts=[];let styles='/* XNBY workplace period layout: original chart scripts retained. */\n';
const rules=css=>{const out=[];postcss.parse(css).walkRules(r=>out.push({selector:r.selector.replaceAll(/\s+/g,' '),declarations:r.nodes.filter(n=>n.type==='decl').map(d=>[d.prop,d.value])}));return out};
for(const [name,id,cssName,jsName] of [
 ['Chart1.vue','data-v-0c8e02ef','Chart1-BMhJYYw6.css','Chart1-DJS7F0a2.js'],
 ['Chart2.vue','data-v-7ffd414d','Chart2-l8K2NNB4.css','Chart2-C5rbxczf.js']]){
 const originalPath=S+'/src/views/workplace/components/Analysis/'+name;
 const candidatePath=A+'/source-review/workplace-period-headers-r489/src/views/workplace/components/Analysis/'+name;
 const original=await fs.readFile(originalPath),candidate=await fs.readFile(candidatePath);
 assert.equal(sha(original),sourcePins.files[name].parentSHA256);assert.equal(sha(candidate),sourcePins.files[name].candidateSHA256);
 const parent=sfc.parse(original.toString(),{filename:originalPath}).descriptor;
 const next=sfc.parse(candidate.toString(),{filename:candidatePath}).descriptor;
 assert.equal(parent.template.content,next.template.content);assert.equal(parent.scriptSetup.content,next.scriptSetup.content);
 const compile=d=>{assert.equal(d.styles.length,1);assert.equal(d.styles[0].scoped,true);const scss=sass.compileString(d.styles[0].content).css;const x=sfc.compileStyle({source:scss,id,scoped:true,filename:originalPath});assert.equal(x.errors.length,0);return x.code};
 const oldCSS=await frozen('frontend/security_pc/assets/css/'+cssName),oldJS=await frozen('frontend/security_pc/assets/js/'+jsName);
 assert(oldJS.bytes.toString().includes('"__scopeId","'+id+'"'));
 assert.deepEqual(rules(compile(parent)),rules(oldCSS.bytes.toString()));
 const output=compile(next);assert(output.includes('container-type: inline-size'));assert(output.includes('@container'));assert(!output.includes(':deep'));
 // Late original chunk styles must not override a changed declaration. Original
 // declarations absent from the overlay (justify-content) remain unchanged.
 const oldRules=rules(oldCSS.bytes.toString()),newRules=rules(output);
 for(const rule of oldRules){const newer=newRules.find(r=>r.selector===rule.selector);assert(newer);for(const [prop,value]of rule.declarations){const replacement=newer.declarations.find(d=>d[0]===prop);if(replacement)assert.equal(replacement[1],value)}}
 postcss.parse(output).walkRules(r=>assert(r.selector.includes(id),'UNSCOPED_CHART_SELECTOR'));
 styles+=output+'\n';charts.push({name,id,originalSourceSHA256:sha(original),candidateSourceSHA256:sha(candidate),templateAndScriptUnchanged:true,baselineCSS:{source:oldCSS.source,relative:oldCSS.relative,...oldCSS.pin},baselineJS:{source:oldJS.source,relative:oldJS.relative,...oldJS.pin},originalSourceCSSMatchesCompiledBaseline:true,lateOriginalCSSCannotOverrideChangedDeclarations:true});
}
const css=Buffer.from(styles),cssName='xnby-workplace-period-'+sha(css).slice(0,12)+'.css';
const baselineHTML=await frozen('frontend/security_pc/index.html');let html=baselineHTML.bytes.toString();
assert.equal((html.match(/<\/head>/g)||[]).length,1);assert(!html.includes('data-xnby-workplace-period'));
const link='  <link rel="stylesheet" data-xnby-workplace-period="20261104-r564" href="/zhumadian/assets/css/'+cssName+'">\n';
html=html.replace('</head>',link+'</head>');assert.equal(html.replace(link,''),baselineHTML.bytes.toString());
const output={'frontend/security_pc/index.html':Buffer.from(html),['frontend/security_pc/assets/css/'+cssName]:css};
assert(Object.values(output).reduce((n,b)=>n+b.length,0)<32768);
await fs.mkdir(D);await fs.mkdir(O);
for(const [n,bytes]of Object.entries(output)){const dest=O+'/payload/'+n;await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,bytes,{flag:'wx'})}
const report={prepared:true,charts,baselineHTML:{source:baselineHTML.source,relative:baselineHTML.relative,...baselineHTML.pin},files:Object.fromEntries(Object.entries(output).map(([n,b])=>[n,{bytes:b.length,sha256:sha(b)}])),cssName,cssSHA256:sha(css),onlyNewScopedCSSAndOneHTMLLink:true,originalAllJavaScriptUnchanged:true,hashNamedOriginalCSSAssetsUnchanged:true,existingHomeViewportStyleRetained:html.includes('data-xnby-home-viewport'),noFullViteBuildRequiredForThisCSSDelta:true,browserDeliveryNotYetVerified:true,publicViewportReproductionPending:true,publicUploadedOrDeployed:false,fullCloneReady:false};
await fs.writeFile(D+'/prepared-css-delivery-r564.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({prepared:true,files:2,totalBytes:Object.values(output).reduce((n,b)=>n+b.length,0),originalScriptsAndHashedAssetsUnchanged:true,publicDeployed:false}));
