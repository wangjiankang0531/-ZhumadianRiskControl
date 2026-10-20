import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {PerspectiveCamera,Vector3,Box3,Frustum,Matrix4} from 'three';
import {LevelBoundsIndex,loadSourceLevelIndex,validateLevelTile,validateIndexedDescendantCut,initialIndexedCoverageDepth,indexedResidentCapacity} from '../src/source_level_index.js';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex'),sha='a'.repeat(64),rootSHA='b'.repeat(64);
const name=(level,suffix)=>`Tile_1_L${level}_0${suffix}.osgb`;
const names=[name(16,'u'),name(17,'uu'),name(17,'u0'),name(18,'uuu'),name(18,'uu0')];
const nodes=names.map((name,i)=>({name,sourceSHA256:sha,sourceBytes:100,depth:[0,1,1,2,2][i],level:[16,17,17,18,18][i],children:[],boundsMin:[0,0,0],boundsMax:[2,2,2],subtreeMin:[0,0,0],subtreeMax:[2,2,2],edgeP90:1,texelP90:.1}));nodes[0].children=[names[1],names[2]];nodes[1].children=[names[3],names[4]];
const tile=()=>({schema:'zhumadian.level_bounds.tile.v1',tile:1,complete:true,sourceManifestSHA256:sha,catalogSHA256:rootSHA,root:names[0],roots:[names[0]],nodes:structuredClone(nodes)});
const options={tile:1,sourceManifestSHA256:sha,catalogSHA256:rootSHA,sourceNodes:5,rootBounds:{boundsMin:[0,0,0],boundsMax:[2,2,2]}};
function fixture(){
 const raw=new TextEncoder().encode(JSON.stringify(tile())),entries=Array.from({length:2346},(_,i)=>({tile:i+1,path:`tile_${i+1}.json`,bytes:raw.length,sha256:hash(raw),sourceNodes:i?1:5}));
 const roots=Array.from({length:2346},(_,i)=>({id:i+1,tile:i+1,boundsMin:[0,0,0],boundsMax:[2,2,2],catalogSHA256:rootSHA}));
 const rootRaw=JSON.stringify({schema:'zhumadian.level_bounds.roots.v1',sourceManifestSHA256:sha,coordinateSystem:'source_local_metres',boundsSource:'union_of_original_subtree_geometry',roots});
 const manifestRaw=JSON.stringify({schema:'zhumadian.level_bounds.manifest.v1',sourceManifestSHA256:sha,rootIndexSHA256:hash(rootRaw),boundsSource:'exact_original_geometry',sourceWrites:0,tiles:entries,sourceNodes:2350});
 const status={schema:'zhumadian.level_bounds.status.v1',identity:hash(manifestRaw),roots:2346,exactBounds:true,sourceWrites:false};
 const files=new Map([['api/level-index/status',JSON.stringify(status)],['api/level-index/files/index_manifest.json',manifestRaw],['api/level-index/files/root_index.json',rootRaw],['api/level-index/files/tile_1.json',raw]]);
 return {files,fetcher:async url=>{assert.ok(files.has(url),'only derived local paths');return new Response(files.get(url));}};
}
test('BVH agrees with independent Three frustum checks across deterministic camera movement',()=>{
 let seed=123456;const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
 const records=Array.from({length:1200},(_,i)=>{const low=[(rand()-.5)*10000,(rand()-.5)*10000,rand()*100];return{id:i+1,boundsMin:low,boundsMax:low.map(v=>v+20+rand()*200)};});
 const bvh=new LevelBoundsIndex(records);let reduction=false;
 for(let i=0;i<80;i++){const c=new PerspectiveCamera(20+rand()*90,.6+rand()*2,.1,60000);c.up.set(0,0,1);c.position.set((rand()-.5)*15000,(rand()-.5)*15000,100+rand()*5000);c.lookAt(0,0,30);c.updateMatrixWorld();const f=new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(c.projectionMatrix,c.matrixWorldInverse));
  const actual=bvh.query(f.planes.map(p=>[p.normal.x,p.normal.y,p.normal.z,p.constant])),expected=records.filter(r=>f.intersectsBox(new Box3(new Vector3(...r.boundsMin),new Vector3(...r.boundsMax)))).map(r=>r.id).sort((a,b)=>a-b);assert.deepEqual(actual.records.map(r=>r.id).sort((a,b)=>a-b),expected);reduction ||= actual.stats.tested<records.length/2;
 }assert.equal(reduction,true);
});
test('tangent, near-plane crossing and wide off-center roots survive without a ranking cap',()=>{
 const planes=[[1,0,0,1],[-1,0,0,1],[0,1,0,1],[0,-1,0,1],[0,0,1,0],[0,0,-1,100]],records=Array.from({length:40},(_,i)=>({id:i+1,boundsMin:[1,-.5,-1],boundsMax:[2,.5,1]}));assert.equal(new LevelBoundsIndex(records).query(planes).records.length,40);
 assert.throws(()=>new LevelBoundsIndex([...records,{...records[0]}]));assert.throws(()=>new LevelBoundsIndex(records).query([[NaN,0,0,0]]));
});
test('sealed tile validates all original reachable nodes and conservative descendant envelopes',()=>{
 assert.equal(validateLevelTile(tile(),options),true);
 for(const change of [t=>t.nodes.pop(),t=>t.nodes[4].depth=1,t=>t.nodes[2].children=[names[0]],t=>t.nodes[4].sourceSHA256='wrong',t=>t.nodes[0].subtreeMax=[1,1,1],t=>t.nodes.push(structuredClone(t.nodes[0])),t=>t.roots=[names[0],names[1]],t=>t.catalogSHA256=sha]){const t=tile();change(t);assert.throws(()=>validateLevelTile(t,options));}
});
test('mixed descendant antichains must cover every branch, without overlaps or outsiders',()=>{
 const data=tile();assert.equal(validateIndexedDescendantCut(data,names[0],[names[1],names[2]]),true);assert.equal(validateIndexedDescendantCut(data,names[0],[names[2],names[3],names[4]]),true);
 for(const cut of [[names[3],names[4]],[names[1],names[2],names[3]],[names[0]],[names[2],names[2]],[names[2],'outside'],[]])assert.throws(()=>validateIndexedDescendantCut(data,names[0],cut));
});
test('active service SHA pins manifest, root index and lazily loaded exact tile',async()=>{
 const f=fixture(),index=await loadSourceLevelIndex({...f,hash,cacheSize:1});assert.equal(index.index.records.length,2346);assert.equal(index.cachedTiles,0);const [a,b]=await Promise.all([index.tile(1),index.tile(1)]);assert.equal(a,b);assert.equal(index.cachedTiles,1);assert.equal(Object.isFrozen(a.nodes[0].children),true);assert.equal(index.pendingTiles,0);await assert.rejects(index.tile(2347));
});
test('changed manifest, roots, tile and transport lengths fail before index use',async()=>{
 for(const path of ['api/level-index/files/index_manifest.json','api/level-index/files/root_index.json']){const f=fixture();f.files.set(path,f.files.get(path)+' ');await assert.rejects(loadSourceLevelIndex({...f,hash}),/SHA differs/);}
 const f=fixture(),index=await loadSourceLevelIndex({...f,hash});f.files.set('api/level-index/files/tile_1.json','{}');await assert.rejects(index.tile(1),/SHA differs/);assert.equal(index.cachedTiles,0);assert.equal(index.pendingTiles,0);
 const g=fixture();await assert.rejects(loadSourceLevelIndex({fetcher:async()=>new Response('{}',{headers:{'Content-Length':'5000'}}),hash}),/bound/);
});
test('an unavailable, writable or different source service cannot activate indexed roots',async()=>{
 for(const change of [{sourceWrites:true},{exactBounds:false},{roots:2345},{identity:'wrong'}]){const f=fixture(),path='api/level-index/status';f.files.set(path,JSON.stringify({...JSON.parse(f.files.get(path)),...change}));await assert.rejects(loadSourceLevelIndex({...f,hash}),/identity/);}
});

test('first complete coverage tier uses measured texture pixels and no arbitrary sixteen-root gate',()=>{
 const record={coverageTiers:[{depth:1,sourceCount:1,maxTexel:1},{depth:2,sourceCount:1,maxTexel:.5},{depth:3,sourceCount:1,maxTexel:.25}]};
 assert.equal(initialIndexedCoverageDepth(record,3,500,1000),1);assert.equal(initialIndexedCoverageDepth(record,3,500,200),2);assert.equal(initialIndexedCoverageDepth(record,3,500,100),3);assert.equal(initialIndexedCoverageDepth({},3,500,100),3);
 assert.equal(indexedResidentCapacity(2346),2346);assert.throws(()=>indexedResidentCapacity(2347));assert.throws(()=>initialIndexedCoverageDepth({coverageTiers:[{depth:1,sourceCount:0,maxTexel:1}]},3,500,100));
});
