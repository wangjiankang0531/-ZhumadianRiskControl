import test from 'node:test';
import assert from 'node:assert/strict';
import {preparedPreviewCoverageFirst,preparedOriginalFormatTransitions,createPreparedPreviewRootIndex} from '../src/prepared_preview_policy.js';
import {chooseIndexedCoverageCandidate} from '../src/source_allocation.js';
const health=()=>({application:'xnby.landscape.web.v1',lodAccess:'read_only',conversionEnabled:false,descriptorPlanSchema:'xnby.source_bundle_plan.v1',nativeReaderEnabled:false,scope:'existing_verified_bundles_only',sourceCoveragePolicy:'prepared_visible_roots_first_v1'});
test('only the complete prepared-only service capability activates coverage preservation',()=>{
 assert.equal(preparedPreviewCoverageFirst(health()),true);
 for(const key of Object.keys(health())){const h=health();delete h[key];assert.equal(preparedPreviewCoverageFirst(h),false,key);}
 for(const h of [null,{}, {...health(),conversionEnabled:true},{...health(),nativeReaderEnabled:true},{...health(),sourceCoveragePolicy:'unknown'}])assert.equal(preparedPreviewCoverageFirst(h),false);
});
test('visible unseeded root wins before a cheaper central refinement, then normal refinement resumes',()=>{
 const rows=[{key:'family/141/p',kind:'family',id:141,score:100,cost:1},{key:'root/94/3',kind:'root',id:94,score:1,cost:100}];
 assert.equal(chooseIndexedCoverageCandidate(rows,id=>id===141).key,'root/94/3');
 assert.equal(chooseIndexedCoverageCandidate(rows,()=>true).key,'family/141/p');
});

test('prepared camera index retains all visible roots past the historical 16-row limit',()=>{
 const rows=Array.from({length:40},(_,i)=>({tile_id:i+1,bounds_min:[i,0,0],bounds_max:[i+.5,.5,.5]}));
 rows.push({tile_id:41,bounds_min:[100,0,0],bounds_max:[101,.5,.5]});
 const before=JSON.stringify(rows),index=createPreparedPreviewRootIndex({root_records:rows});
 const result=index.query([[1,0,0,1],[-1,0,0,40],[0,1,0,1],[0,-1,0,1],[0,0,1,1],[0,0,-1,1]]);
 assert.equal(result.records.length,40);assert.ok(result.records.some(r=>r.tile===40));assert.ok(!result.records.some(r=>r.tile===41));assert.equal(JSON.stringify(rows),before);
});
test('camera index rejects duplicate roots and inverted bounds rather than hiding missing coverage',()=>{
 const r={tile_id:1,bounds_min:[0,0,0],bounds_max:[1,1,1]};
 assert.throws(()=>createPreparedPreviewRootIndex({root_records:[r,r]}),/Duplicate/);
 assert.throws(()=>createPreparedPreviewRootIndex({root_records:[{...r,bounds_max:[-1,1,1]}]}),/bounds/);
});

test('explicit verified original-data composition preserves visible-root priority with bounded capability',()=>{
 const composed=()=>({...health(),scope:'verified_prepared_and_explicit_python_original_sources',preparedSourceCount:2,pythonOriginalSources:{enabled:true,assetWritesEnabled:false,readerIdentity:'a'.repeat(64),tiles:[73,164]}});
 assert.equal(preparedPreviewCoverageFirst(composed()),true);
 for(const field of ['scope','preparedSourceCount','pythonOriginalSources']){const h=composed();delete h[field];assert.equal(preparedPreviewCoverageFirst(h),false,field);}
 for(const field of Object.keys(composed().pythonOriginalSources)){const h=composed();delete h.pythonOriginalSources[field];assert.equal(preparedPreviewCoverageFirst(h),false,field);}
 for(const tiles of [[],[1,1],[0],[2347],['1'],Array.from({length:257},(_,i)=>i+1)]){const h=composed();h.pythonOriginalSources.tiles=tiles;assert.equal(preparedPreviewCoverageFirst(h),false);}
 for(const change of [{enabled:false},{assetWritesEnabled:true},{readerIdentity:'unverified'}]){const h=composed();Object.assign(h.pythonOriginalSources,change);assert.equal(preparedPreviewCoverageFirst(h),false);}
 for(const change of [{scope:'arbitrary_original_sources'},{preparedSourceCount:0},{preparedSourceCount:5},{nativeReaderEnabled:true},{conversionEnabled:true},{sourceCoveragePolicy:'unknown'}])assert.equal(preparedPreviewCoverageFirst({...composed(),...change}),false);
 const rows=[{key:'family/73/p',kind:'family',id:73,score:100,cost:1},{key:'root/164/3',kind:'root',id:164,score:1,cost:100}];
 assert.equal(chooseIndexedCoverageCandidate(rows,id=>id===73).key,'root/164/3');
 assert.equal(chooseIndexedCoverageCandidate(rows,()=>true).key,'family/73/p');
});

test('sealed complete-index fallback keeps coverage priority without enumerating all roots as a bounded explicit list',()=>{
 const indexed=()=>({...health(),scope:'verified_prepared_and_explicit_python_original_sources',preparedSourceCount:2,pythonOriginalSources:{enabled:true,assetWritesEnabled:false,readerIdentity:'a'.repeat(64),tileSelection:'sealed_index_missing_prepared_v1',tileCount:2346,indexIdentity:'b'.repeat(64),sourceManifestSHA256:'c'.repeat(64),preparedFirst:true}});
 assert.equal(preparedPreviewCoverageFirst(indexed()),true);
 for(const field of Object.keys(indexed().pythonOriginalSources)){const h=indexed();delete h.pythonOriginalSources[field];assert.equal(preparedPreviewCoverageFirst(h),false,field);}
 for(const change of [{tileCount:2345},{tileCount:2347},{preparedFirst:false},{tileSelection:'all_files'},{indexIdentity:'unknown'},{sourceManifestSHA256:'unknown'},{tiles:[]}]){const h=indexed();Object.assign(h.pythonOriginalSources,change);assert.equal(preparedPreviewCoverageFirst(h),false);}
});

test('format transitions bind the complete source capability to the actual loaded index and catalog',()=>{
 const h={...health(),scope:'verified_prepared_and_explicit_python_original_sources',preparedSourceCount:2,pythonOriginalSources:{enabled:true,assetWritesEnabled:false,readerIdentity:'a'.repeat(64),tileSelection:'sealed_index_missing_prepared_v1',tileCount:2346,indexIdentity:'b'.repeat(64),sourceManifestSHA256:'c'.repeat(64),preparedFirst:true}},index={identity:'b'.repeat(64),sourceManifestSHA256:'c'.repeat(64)};
 assert.equal(preparedOriginalFormatTransitions(h,index),true);
 for(const i of [null,{}, {...index,identity:'d'.repeat(64)},{...index,sourceManifestSHA256:'d'.repeat(64)}])assert.equal(preparedOriginalFormatTransitions(h,i),false);
});
test('format transitions stay disabled for generic prepared services, old explicit lists and weakened source capabilities',()=>{
 const index={identity:'b'.repeat(64),sourceManifestSHA256:'c'.repeat(64)};
 for(const h of [null,health(),{...health(),scope:'verified_prepared_and_explicit_python_original_sources',preparedSourceCount:2,pythonOriginalSources:{enabled:true,assetWritesEnabled:false,readerIdentity:'a'.repeat(64),tiles:[1],indexIdentity:index.identity,sourceManifestSHA256:index.sourceManifestSHA256}},{...health(),nativeReaderEnabled:true}])assert.equal(preparedOriginalFormatTransitions(h,index),false);
});
