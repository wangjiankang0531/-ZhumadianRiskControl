import fs from 'node:fs/promises';import vm from 'node:vm';import{createRequire}from'node:module';import{pathToFileURL}from'node:url';
const R='D:/Project/Zhumadian',P=R+'/Application/work/tianjin_native_20261023/emergency_pc',O=R+'/work/event_delivery_consistency_20261030/full-controller-r130';
const require=createRequire(pathToFileURL(P+'/package.json')),vue=require('vue'),esbuild=require('esbuild');
const raw=await fs.readFile(R+'/work/user_feedback_20261031/emergency-workflow-source-r10/source/src/hooks/useTable.ts','utf8');
const compiled=await esbuild.transform(raw,{loader:'ts',format:'cjs',target:'es2020'}),module={exports:{}};
vm.runInThisContext('(function(require,module,exports){'+compiled.code+'\n})')(require,module,module.exports);const{useTable}=module.exports;
const renderer=vue.createRenderer({insert(){},remove(){},createElement:()=>({}),createText:()=>({}),createComment:()=>({}),setText(){},setElementText(){},parentNode:()=>null,nextSibling:()=>null,patchProp(){}});
function mount(paged=true){let state;const pending=[],callbacks=[],errors=[];const app=renderer.createApp({setup(){state=useTable(params=>new Promise((resolve,reject)=>pending.push({params,resolve,reject})),{},paged,data=>{callbacks.push(data);return data},e=>errors.push(e));return()=>null}});app.mount({});return{state,pending,callbacks,errors,app};}
const need=(v,m)=>{if(!v)throw Error(m)},cases=[];
{
 const h=mount();const a=h.state.getTableList(),b=h.state.getTableList();h.pending[1].resolve({data:{records:[{name:'new'}],total:7}});await b;h.pending[0].resolve({data:{records:[{name:'old'}],total:100}});await a;
 need(h.state.tableData.value[0].name==='new'&&h.state.pageable.value.total===7&&h.callbacks.length===1,'LATE_SUCCESS_OR_CALLBACK_CHANGED_NEW_RESULT');h.app.unmount();cases.push('late-success-does-not-change-latest-rows-total-or-callback');
}
{
 const h=mount();const a=h.state.getTableList(),b=h.state.getTableList();h.pending[0].reject(Error('own old error'));await a;need(h.state.loading.value&&h.errors.length===0,'OLD_ERROR_CHANGED_LATEST_PENDING_STATE');h.pending[1].resolve({data:{records:[],total:0}});await b;need(!h.state.loading.value,'LATEST_COMPLETION_DID_NOT_CLEAR_LOADING');h.app.unmount();cases.push('old-error-does-not-clear-latest-loading-or-call-error-handler');
}
{
 const h=mount(false);const a=h.state.getTableList();h.app.unmount();h.pending[0].resolve({data:['old']});await a;need(h.state.tableData.value.length===0&&h.callbacks.length===0,'UNMOUNTED_INSTANCE_CHANGED');cases.push('unmount-ignores-success-and-callback');
}
{
 const h=mount(false);h.state.searchParam.value={zero:0,no:false,text:'own'};h.state.search();need(h.pending[0].params.zero===0&&h.pending[0].params.no===false,'ORIGINAL_FALSE_ZERO_FILTERS_LOST');h.pending[0].resolve({data:['own']});await new Promise(r=>setTimeout(r,0));need(h.state.tableData.value[0]==='own','NONPAGED_RESULT_CHANGED');h.app.unmount();cases.push('nonpaged-shape-and-original-zero-false-filters-preserved');
}
await fs.writeFile(O+'/table-hook-lifecycle-proof.json',JSON.stringify({allPassed:true,actualVueRendererAndUnmountUsed:true,syntheticDeferredAPIOnly:true,nativeBrowserAcceptanceSeparate:true,cases},null,2));console.log(JSON.stringify({allPassed:true,actualVueLifecycleCases:cases.length}));
