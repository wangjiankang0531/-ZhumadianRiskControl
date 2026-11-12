// Discover only. The unchanged canonical builder must later verify fixed outputs.
import fs from'node:fs';import path from'node:path';import crypto from'node:crypto';import {createRequire}from'node:module';import {pathToFileURL}from'node:url';
const W=process.argv[2],O=process.argv[3];if(!W||!O||fs.existsSync(O))throw Error('FRESH_DISCOVERY_ONLY_RECEIPT_REQUIRED');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),m=JSON.parse(fs.readFileSync(path.join(W,'scene_delivery_sources.json'))),{build,version}=createRequire(path.join(W,'package.json'))('esbuild');
if(version!==m.esbuildVersion)throw Error('PINNED_ESBUILD_REQUIRED');
for(const[n,h]of Object.entries(m.sourcePins))if(sha(fs.readFileSync(path.resolve(W,n)))!==h)throw Error('SOURCE_PIN_CHANGED');
const{prepareSceneVendor}=await import(pathToFileURL(path.join(W,'apply_scene_vendor_patch.mjs')));const vendorPatch=prepareSceneVendor();
for(const[n,h]of Object.entries(m.vendorPins))if(sha(fs.readFileSync(path.resolve(W,n)))!==h)throw Error('VENDOR_PIN_CHANGED');
const outputs={};let mainInputs;
for(const[entry,name]of [['src/viewer.js','viewer.js'],['src/source_gain_worker.js','source-gain-worker.js']]){
 const r=await build({absWorkingDir:W,entryPoints:[entry],bundle:true,minify:true,format:'esm',outfile:path.join(W,'unwritten-discovery',name),write:false,metafile:true});
 const raw=Buffer.from(r.outputFiles.find(f=>f.path.endsWith(name)).contents),pins={};for(const n of Object.keys(r.metafile.inputs))pins[n.replaceAll('\\','/')]=sha(fs.readFileSync(path.resolve(W,n)));
 if(name==='viewer.js'){if(JSON.stringify(Object.keys(pins).sort())!==JSON.stringify(Object.keys(m.mainInputs).sort()))throw Error('ACTUAL_MAIN_CLOSURE_DIFFERS');for(const[n,h]of Object.entries(pins))if(m.mainInputs[n]!==h)throw Error('ACTUAL_MAIN_SOURCE_CHANGED');mainInputs=pins;}
 outputs[name]={bytes:raw.length,sha256:sha(raw)};
}
for(const[source,name]of [['src/index.html','index.html'],['source-config.html','source-config.html'],['scene-help.html','scene-help.html']]){const raw=fs.readFileSync(path.join(W,source));outputs[name]={bytes:raw.length,sha256:sha(raw)};}
const receipt={schema:'xnby.scene.output.discovery-only.v1',discoveredOnly:true,qualifiedBuild:false,esbuildVersion:version,vendorPatch,mainInputs,outputs};fs.writeFileSync(O,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({discoveredOnly:true,qualifiedBuild:false,mainInputs:Object.keys(mainInputs).length,outputs:5}));
