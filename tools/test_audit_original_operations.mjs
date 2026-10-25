import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {parsers,analyzeVue,apiExports,safeFile,auditProjects} from './audit_original_operations.mjs';
const p=parsers(process.env.XNBY_AST_PARSER_ROOT||(()=>{throw Error('Set XNBY_AST_PARSER_ROOT to an existing locked Vue project');})());
const apiSource=`throw new Error('ORIGINAL_API_MUST_NOT_EXECUTE');import request from '@/utils/request';export const getPage=(params)=>request.get('/serv/items/page',params);export const remove=(params)=>request.delete('/serv/items/'+params.id);export const save=(data)=>request({url:'/serv/items',method:'post',data});`;
const api=apiExports(apiSource,p);

test('Vue AST preserves multiline actions, inherited visibility and disabled conditions',()=>{
  const source=`<template><section v-if="canEdit"><el-button\n :disabled="row.owner !== department" @click="edit(row)">编辑</el-button><el-button v-auth="'delete'" @click="del(row)">删除</el-button></section></template><script setup lang="ts">const edit=(row:any)=>{};const del=(row:any)=>{};</script>`;
  const result=analyzeVue(source,p);
  assert.equal(result.controls.length,2);assert.equal(result.controls[0].label,'编辑');assert.deepEqual(result.controls[0].conditions,[{directive:'if',expression:'canEdit'}]);assert.deepEqual(result.controls[0].disabled,['row.owner !== department']);assert.equal(result.controls[1].conditions[1].directive,'auth');
});
test('action handler follows local callback references to imported APIs and literal navigation candidates',()=>{
  const source=`<template><button @click="del(row)">删除</button><button @click="add">新增</button></template><script setup lang="ts">import {remove as removeById} from '@/api/items';const del=(row:any)=>useHandleData(removeById,row);const add=()=>router.push({path:'/items/add'});</script>`;
  const result=analyzeVue(source,p,{apiLoader:()=>api});const action=result.controls[0].events[0];assert.equal(action.apiReferences[0].export,'remove');assert.deepEqual(action.apiReferences[0].requests[0].url,{kind:'dynamic',path:'/serv/items/${dynamic}',queryOmitted:false});assert.equal(result.controls[1].events[0].routeCandidates[0].path,'/items/add');
});
test('API exports retain verb and dynamic placeholder without exposing external query strings',()=>{
  assert.equal(api.getPage[0].method,'GET');assert.equal(api.save[0].method,'POST');assert.equal(api.save[0].url.path,'/serv/items');
  const external=apiExports(`export const x=()=>request.get('https://invalid.example/a?token=SECRET');`,p).x[0].url;
  assert.equal(external.kind,'external');assert.ok(external.sha256);assert.equal(JSON.stringify(external).includes('SECRET'),false);
});
test('unused API imports are not counted as references or successful actions',()=>{
  const result=analyzeVue(`<template><ProTable :request-api="getPage"/></template><script setup>import {getPage,remove} from '@/api/items';const query=()=>getPage();</script>`,p,{apiLoader:()=>api});assert.equal(result.apiReferences.some(r=>r.binding==='remove'),false);assert.equal(result.functionalParityVerified,false);
});
test('commented controls and script strings are not counted as visible template elements',()=>{
  const result=analyzeVue(`<template><!-- <button @click="bad">FAKE</button> --><button @click="good">真实候选</button></template><script setup>globalThis.__XNBY_ORIGINAL_EXECUTED=true;const text='<button>FAKE</button>';const good=()=>{};</script>`,p);assert.equal(result.controls.length,1);assert.equal(result.controls[0].label,'真实候选');assert.equal(globalThis.__XNBY_ORIGINAL_EXECUTED,undefined);
});
test('missing or unsupported API exports remain explicitly unresolved',()=>{
  const result=analyzeVue(`<template><button @click="missing">操作</button></template><script setup>import {missing} from '@/api/items';</script>`,p,{apiLoader:()=>api});assert.equal(result.unresolvedApiImports.length,1);assert.equal(result.controls[0].events[0].apiReferences[0].resolved,false);
});
test('source path escape is rejected without reading outside the root',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'zmd-operation-path-'));try{fs.writeFileSync(path.join(root,'one.vue'),'synthetic');assert.throws(()=>safeFile(root,'../outside'),/SOURCE_PATH_REJECTED/);assert.throws(()=>safeFile(root,path.resolve(root,'one.vue')),/SOURCE_PATH_REJECTED/);assert.equal(safeFile(root,'one.vue'),fs.realpathSync(path.join(root,'one.vue')));}finally{fs.rmSync(root,{recursive:true});}
});
test('folder index imports resolve and per-page parse failures do not become green coverage',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'zmd-operation-project-'));try{
    fs.mkdirSync(path.join(root,'src/api/items'),{recursive:true});fs.mkdirSync(path.join(root,'src/views'),{recursive:true});
    fs.writeFileSync(path.join(root,'src/api/items/index.ts'),apiSource);
    fs.writeFileSync(path.join(root,'src/views/good.vue'),`<template><button @click="remove({id:'synthetic'})">删除</button></template><script setup>import {remove} from '@/api/items';</script>`);
    fs.writeFileSync(path.join(root,'src/views/bad.vue'),'<script setup>const = broken;</script>');
    const result=auditProjects({projects:{synthetic:root}},p);const project=result.projects[0];assert.equal(project.vueFiles,2);assert.equal(project.parseFailures,1);assert.equal(project.apiModules,1);assert.equal(project.pages.find(r=>r.parsed).controls[0].events[0].apiReferences[0].requests[0].method,'DELETE');assert.equal(result.functionalParityVerified,false);assert.equal(result.originalCodeExecuted,false);
  }finally{fs.rmSync(root,{recursive:true});}
});


test('plain TypeScript angle assertions are parsed without treating them as JSX',()=>{
  const result=analyzeVue(`<template><button @click="save">保存</button></template><script setup lang="ts">const rows=ref(<any>[]);const save=()=>{};</script>`,p);
  assert.equal(result.controls.length,1);assert.equal(result.controls[0].label,'保存');
});
test('mobile service imports and table request bindings are enumerated without counting type-only imports',()=>{
  const result=analyzeVue(`<template><ProTable :request-api="getPage"/><button @tap="save">提交</button></template><script setup lang="ts">import {getPage,save} from '@/service/items';import type {Row} from '@/service/interface';</script>`,p,{apiLoader:specifier=>specifier==='@/service/items'?api:null});
  assert.equal(result.templateApiBindings[0].apiReferences[0].export,'getPage');assert.equal(result.controls[0].events[0].apiReferences[0].export,'save');assert.equal(result.unresolvedApiImports.length,0);
});
