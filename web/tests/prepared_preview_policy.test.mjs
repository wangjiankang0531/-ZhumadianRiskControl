import test from 'node:test';
import assert from 'node:assert/strict';
import {preparedPreviewCoverageFirst,createPreparedPreviewRootIndex} from '../src/prepared_preview_policy.js';
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
