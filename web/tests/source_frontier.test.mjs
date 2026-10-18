import {withSourceRestorations,sourceBundleIdentity} from '../src/source_residency.js';
import {stageSourceParts,SourceLoadCancelled} from '../src/lod_transaction.js';
import test from 'node:test';
import assert from 'node:assert/strict';
import {Group,BufferGeometry,Float32BufferAttribute,Mesh,MeshBasicMaterial,DataTexture,Ray,Vector3,PerspectiveCamera,ClampToEdgeWrapping,RepeatWrapping} from 'three';
import {SourceFrontier,pickVisibleSource,validateSourceBundle,visibleSourceCandidates,sourceRefinementScore,sourceViewPriority,rankSourceCandidates,planSourceBudget} from '../src/source_frontier.js';
const hash='a'.repeat(64),side=1024,mipBytes=5592404;
function mesh(points){const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(points,3));g.setIndex(points.length===18?[0,1,2,3,4,5]:[0,1,2]);return new Mesh(g,new MeshBasicMaterial({map:new DataTexture(new Uint8Array(4),side,side)}));}
function node(name,children,depth,part,m,first=0){const p=m.geometry.attributes.position.array,i=m.geometry.index.array,low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];for(let n=first;n<first+3;n++)for(let a=0;a<3;a++){low[a]=Math.min(low[a],p[i[n]*3+a]);high[a]=Math.max(high[a],p[i[n]*3+a]);}return{name,children,depth,triangles:1,source_sha256:hash,longest_edge_p90_m:1,texel_world_p90_m:.1,bounds_min:low,bounds_max:high,spans:[{part,first,count:3}]};}
function part(directory,m){return {directory,vertices:m.geometry.attributes.position.count,indices:m.geometry.index.count,atlas_size:side,gpu_payload_bytes:m.geometry.attributes.position.count*64+m.geometry.index.count*4+mipBytes};}
function bundle(parent,depth,children,names=children){const meshes=new Map([['part_000',mesh([-.9,-.8,.1,-.6,-.8,.1,-.75,-.2,.1])],['part_001',mesh([.6,-.8,.1,.9,-.8,.1,.75,-.2,.1])]]),parts=[...meshes].map(([k,m])=>part(k,m));return {meshes,marker:{schema:'xnby.osgb_native_family.v1',tile_id:1,replacement_parent:parent,parent_source_sha256:hash,complete_sibling_family:true,texture_policy:'original_pixels_v1',parts,source_nodes:names.map((name,i)=>node(name,[],depth,parts[i].directory,meshes.get(parts[i].directory))),indices:6,gpu_payload_bytes:parts.reduce((s,p)=>s+p.gpu_payload_bytes,0)}};}
function initial(){const m=mesh([-1,-1,0,1,-1,0,0,1,0,10,-1,0,12,-1,0,11,1,0]),meshes=new Map([['part_000',m]]),parts=[part('part_000',m)],marker={parts,source_nodes:[node('P',['C0','C1'],3,'part_000',m),node('terminal',[],3,'part_000',m,3)],indices:6,gpu_payload_bytes:parts[0].gpu_payload_bytes};return {frontier:new SourceFrontier(marker,meshes),mesh:m,marker,meshes};}

test('every child upload completes before exact parent indices disappear',()=>{const {frontier,mesh:m}=initial(),candidate=bundle('P',4,['C0','C1']);frontier.applyMasks();const ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);assert.equal(frontier.commit(ticket,candidate.meshes),false);assert.deepEqual([...frontier.visible],['P','terminal']);assert.equal(m.geometry.groups.reduce((s,g)=>s+g.count,0),6);frontier.markReady(ticket,1);assert.equal(frontier.commit(ticket,candidate.meshes),true);frontier.applyMasks();assert.deepEqual(new Set(frontier.visible),new Set(['C0','C1','terminal']));assert.deepEqual(m.geometry.groups,[{start:3,count:3,materialIndex:0}]);assert.equal(frontier.maxDepth,4);assert.equal(frontier.bytes,initial().marker.gpu_payload_bytes+candidate.marker.gpu_payload_bytes);});
test('missing siblings, invalid bytes and budget rejection preserve the complete parent',()=>{const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']);for(const marker of [{...candidate.marker,source_nodes:candidate.marker.source_nodes.slice(0,1)},{...candidate.marker,gpu_payload_bytes:NaN}])assert.throws(()=>frontier.begin(marker,128*1048576));assert.throws(()=>frontier.begin(candidate.marker,1));assert.deepEqual([...frontier.visible],['P','terminal']);});
test('camera reset rejects stale completion and restores complete parent draws',()=>{const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']),old=frontier.begin(candidate.marker,128*1048576);assert.equal(frontier.cancel(old),true);const current=frontier.begin(candidate.marker,128*1048576);assert.equal(frontier.markReady(old,0),false);assert.equal(frontier.commit(old,candidate.meshes),false);frontier.reset();assert.equal(frontier.markReady(current,0),false);assert.deepEqual([...frontier.visible],['P','terminal']);});
test('visible picking never returns hidden parents through genuine child geometry holes',()=>{const {frontier}=initial(),ray=new Ray(new Vector3(0,0,5),new Vector3(0,0,-1));assert.equal(pickVisibleSource(frontier,ray).node.name,'P');const candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);frontier.applyMasks();assert.equal(pickVisibleSource(frontier,ray),null);frontier.rollback('P');frontier.applyMasks();assert.equal(pickVisibleSource(frontier,ray).node.name,'P');});
test('nested coarsening retires descendants and preserves the independent terminal leaf',()=>{const {frontier}=initial(),a=bundle('P',4,['C0','C1']);a.marker.source_nodes[0].children=['G0','G1'];const t=frontier.begin(a.marker,128*1048576);frontier.markReady(t,0);frontier.markReady(t,1);frontier.commit(t,a.meshes);const b=bundle('C0',5,['G0','G1']),u=frontier.begin(b.marker,128*1048576);frontier.markReady(u,0);frontier.markReady(u,1);frontier.commit(u,b.meshes);assert.deepEqual(new Set(frontier.visible),new Set(['G0','G1','C1','terminal']));assert.equal(frontier.rollback('P').length,2);assert.deepEqual([...frontier.visible],['terminal','P']);assert.equal(frontier.nodes.size,2);});
test('corrupt source spans, physical byte counts and atlas dimensions are rejected',()=>{const {marker,meshes}=initial();for(const change of [m=>m.source_nodes[1].spans[0].first=0,m=>m.parts[0].gpu_payload_bytes=1,m=>m.parts[0].atlas_size=2048]){const bad=structuredClone(marker);change(bad);assert.throws(()=>validateSourceBundle(bad,meshes));}});

test('a terminal center surface does not block visible neighbor refinement',()=>{const {marker,meshes}=initial();marker.source_nodes[0].children=[];marker.source_nodes[1].children=['T0','T1'];const frontier=new SourceFrontier(marker,meshes),camera=new PerspectiveCamera(90,2,.1,100);camera.position.set(0,0,15);camera.lookAt(0,0,0);const candidates=visibleSourceCandidates(frontier,camera,720,'P');assert.equal(candidates.length,1);assert.equal(candidates[0].node.name,'terminal');assert.equal(candidates[0].center,false);});
test('offscreen and sufficiently sharp sources are excluded, quality and coverage drive priority',()=>{const {frontier}=initial(),camera=new PerspectiveCamera(50,1,.1,100);camera.position.set(0,0,5);camera.lookAt(0,0,0);assert.equal(visibleSourceCandidates(frontier,camera,720,'P')[0].node.name,'P');assert.equal(sourceRefinementScore(5,200,720,0),0);assert.ok(sourceRefinementScore(12,300,720,.2)>sourceRefinementScore(12,30,720,.2));});


test('fully hidden physical GPU pages retire once and parent CPU geometry remains recoverable',()=>{
 const m=mesh([-1,-1,0,1,-1,0,0,1,0]),meshes=new Map([['part_000',m]]),parts=[part('part_000',m)];
 const marker={parts,source_nodes:[node('P',['C0','C1'],3,'part_000',m)],indices:3,gpu_payload_bytes:parts[0].gpu_payload_bytes};
 const frontier=new SourceFrontier(marker,meshes);frontier.applyMasks();let geometryRetired=0,textureRetired=0;
 m.geometry.addEventListener('dispose',()=>geometryRetired++);m.material[0].map.addEventListener('dispose',()=>textureRetired++);
 const candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);frontier.applyMasks();frontier.applyMasks();
 assert.equal(m.visible,false);assert.equal(geometryRetired,1);assert.equal(textureRetired,1);assert.equal(frontier.bytes,candidate.marker.gpu_payload_bytes);
 assert.equal(frontier.retainedPayloadBytes,marker.gpu_payload_bytes+candidate.marker.gpu_payload_bytes);assert.equal(m.geometry.attributes.position.count,3);
 assert.equal(frontier.rollbackPlan('P').bytes,marker.gpu_payload_bytes);frontier.rollback('P');frontier.applyMasks();assert.equal(m.visible,true);assert.equal(frontier.bytes,marker.gpu_payload_bytes);assert.equal(pickVisibleSource(frontier,new Ray(new Vector3(0,0,5),new Vector3(0,0,-1))).node.name,'P');
});
test('rollback that needs more active GPU memory is rejected without changing the cut',()=>{
 const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);
 const before=[...frontier.visible];assert.deepEqual(frontier.rollback('P',-frontier.bytes),[]);assert.deepEqual([...frontier.visible],before);
});
test('larger visible quality deficit outranks a terminal-direction center preference',()=>{
 const center={score:2,center:true},foreground={score:8,center:false};assert.equal(rankSourceCandidates([center,foreground])[0],foreground);assert.equal(rankSourceCandidates([center,{score:2,center:false}])[0],center);
});
test('resident branch priority uses the same actual camera as incoming visible candidates',()=>{
 const {frontier}=initial(),camera=new PerspectiveCamera(52,991/683,.5,60000);camera.up.set(0,0,1);camera.position.set(0,-10,12);camera.lookAt(0,0,0);const candidates=visibleSourceCandidates(frontier,camera,683);
 for(const candidate of candidates)assert.ok(Math.abs(candidate.score-sourceViewPriority(candidate.node,camera,683))<1e-9);
});


test('budget planning can coarsen two independent families in one root without mutating a failed attempt',()=>{
 const {frontier,marker}=initial();marker.source_nodes[1].children=['T0','T1'];
 for(const [parent,names] of [['P',['C0','C1']],['terminal',['T0','T1']]]){const candidate=bundle(parent,4,names),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);}
 const residents=new Map([[1,{frontier}]]),before=[...frontier.visible],cost=20*1048576,limit=30*1048576;
 assert.equal(planSourceBudget(residents,{id:2,parent:'incoming',score:10},cost,1,()=>0),null);assert.deepEqual([...frontier.visible],before);
 const actions=planSourceBudget(residents,{id:2,parent:'incoming',score:10},cost,limit,()=>0);assert.equal(actions.length,2);assert.deepEqual([...frontier.visible],before);
 for(const action of actions)frontier.rollback(action.parent);assert.ok(frontier.bytes+cost<=limit);
});
test('budget planning never coarsens an ancestor of the node being staged',()=>{
 const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);
 assert.equal(planSourceBudget(new Map([[1,{frontier}]]),{id:1,parent:'C0',score:100},frontier.bytes,frontier.bytes,()=>0),null);
});


test('an explicitly backed low-value seed root can yield to newly visible foreground detail',()=>{
 const {frontier}=initial(),residents=new Map([[1,{frontier}]]),cost=6*1048576,limit=7*1048576;
 assert.equal(planSourceBudget(residents,{id:2,parent:'incoming',score:10},cost,limit,()=>0),null);
 assert.deepEqual(planSourceBudget(residents,{id:2,parent:'incoming',score:10},cost,limit,()=>0,()=>0),[{root:1,parent:null}]);
 assert.equal(planSourceBudget(residents,{id:1,parent:'P',score:10},cost,limit,()=>0,()=>0),null);
 assert.equal(frontier.bytes,initial().frontier.bytes);
});


test('a retired frontier ticket cancels staging without replacing or failing the live parent',async()=>{
 const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576),staged=new Group(),loaded=[],ready=[];
 const options={marker:candidate.marker,downloads:{load:async part=>{loaded.push(part);return {scene:new Group().add(candidate.meshes.get(part))};}},urlForPart:p=>p.directory,group:staged,prepare:()=>{},stillWanted:()=>frontier.pending?.ticket===ticket,dispose:()=>{},onReady:i=>{ready.push(frontier.markReady(ticket,i));},yieldFrame:async()=>{frontier.cancel(ticket);}};
 await assert.rejects(()=>stageSourceParts(options),SourceLoadCancelled);
 assert.deepEqual(loaded,['part_000']);assert.deepEqual(ready,[true]);assert.equal(staged.children.length,1);assert.deepEqual([...frontier.visible],['P','terminal']);assert.equal(frontier.commit(ticket,candidate.meshes),false);
 const next=frontier.begin(candidate.marker,128*1048576);assert.notEqual(next,ticket);assert.equal(frontier.markReady(next,0),true);
});


function releasedParent(){
 const m=mesh([-1,-1,0,1,-1,0,0,1,0]),meshes=new Map([['part_000',m]]),parts=[part('part_000',m)],marker={parts,source_nodes:[node('P',['C0','C1'],3,'part_000',m)],indices:3,gpu_payload_bytes:parts[0].gpu_payload_bytes};
 const frontier=new SourceFrontier(marker,meshes),root=frontier.bundles.get('$root'),scene=new Group().add(m),candidate=bundle('P',4,['C0','C1']);candidate.marker.source_nodes[0].children=['G0','G1'];
 const ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);frontier.applyMasks();
 let closed=0;m.material[0].map.source.data.close=()=>closed++;const report=frontier.releaseHiddenPages();
 return {frontier,root,scene,report,closed:()=>closed,parent:()=>mesh([-1,-1,0,1,-1,0,0,1,0])};
}
function restoredBatch(fixture){return {marker:structuredClone(fixture.root.marker),meshes:new Map([['part_000',fixture.parent()]]),dispose(){this.disposed=true;}};}

test('hidden CPU pages close source bitmaps once, detach meshes and retain source metadata',()=>{
 const f=releasedParent();assert.equal(f.report.pages,1);assert.equal(f.closed(),1);assert.equal(f.scene.children.length,0);assert.equal(f.root.meshes.size,0);assert.equal(f.frontier.retainedPayloadBytes,f.frontier.bytes);assert.equal(f.frontier.nodes.get('P').bundle,f.root);assert.equal(f.frontier.releaseHiddenPages().pages,0);assert.equal(f.closed(),1);
});

test('a missing CPU parent cannot become visible or reset synchronously',()=>{
 const f=releasedParent(),visible=[...f.frontier.visible],version=f.frontier.cutVersion,plan=f.frontier.rollbackPlan('P');assert.equal(plan.missingPages.length,1);assert.deepEqual(f.frontier.rollback('P'),[]);assert.deepEqual([...f.frontier.visible],visible);assert.equal(f.frontier.cutVersion,version);assert.throws(()=>f.frontier.reset(),/尚未恢复/);assert.deepEqual([...f.frontier.visible],visible);
});

test('validated restored pages recover the exact parent cut and picking',()=>{
 const f=releasedParent();f.frontier.restorePages(f.root,new Map([['part_000',f.parent()]]));assert.equal(f.frontier.rollback('P').length,1);f.frontier.applyMasks();assert.deepEqual([...f.frontier.visible],['P']);assert.equal(pickVisibleSource(f.frontier,new Ray(new Vector3(0,0,5),new Vector3(0,0,-1))).node.name,'P');
});

test('restoration rejects wrong geometry before installing any page',()=>{
 const f=releasedParent(),bad=f.parent();bad.geometry.index.count=0;assert.throws(()=>f.frontier.restorePages(f.root,new Map([['part_000',bad]])));assert.equal(f.root.meshes.size,0);assert.deepEqual([...f.frontier.visible],['C0','C1']);
});

test('a physical page shared with a visible neighbor cannot be CPU-retired',()=>{
 const {frontier}=initial(),candidate=bundle('P',4,['C0','C1']),ticket=frontier.begin(candidate.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,candidate.meshes);frontier.applyMasks();assert.equal(frontier.releaseHiddenPages().pages,0);assert.equal(frontier.bundles.get('$root').meshes.size,1);
});

test('cancelled restoration disposes late pages and leaves all live cuts unchanged',async()=>{
 const f=releasedParent(),before=[...f.frontier.visible],batch=restoredBatch(f);let complete,started,wanted=true,applied=false;const began=new Promise(resolve=>{started=resolve;});
 const task=withSourceRestorations({actions:[{root:1,parent:'P'}],residents:new Map([[1,{frontier:f.frontier}]]),stillWanted:()=>wanted,limit:128*1048576,load:()=>{started();return new Promise(resolve=>{complete=resolve;});},apply:()=>{applied=true;}});
 await began;wanted=false;complete(batch);await assert.rejects(task,SourceLoadCancelled);assert.equal(batch.disposed,true);assert.equal(applied,false);assert.equal(f.root.meshes.size,0);assert.deepEqual([...f.frontier.visible],before);
});

test('an altered source identity cannot replace the displayed children',async()=>{
 const f=releasedParent(),batch=restoredBatch(f);batch.marker.gpu_payload_bytes++;
 await assert.rejects(()=>withSourceRestorations({actions:[{root:1,parent:'P'}],residents:new Map([[1,{frontier:f.frontier}]]),stillWanted:()=>true,limit:128*1048576,load:async()=>batch,apply:()=>assert.fail('must not apply')}),/不一致/);assert.equal(batch.disposed,true);assert.equal(f.root.meshes.size,0);
});

test('restoration snapshots reject another source commit while pages are being read',async()=>{
 const f=releasedParent(),batch=restoredBatch(f);let complete,started;const began=new Promise(resolve=>{started=resolve;});
 const task=withSourceRestorations({actions:[{root:1,parent:'P'}],residents:new Map([[1,{frontier:f.frontier}]]),stillWanted:()=>true,limit:128*1048576,load:()=>{started();return new Promise(resolve=>{complete=resolve;});},apply:()=>assert.fail('stale cut must not apply')});
 await began;const grand=bundle('C0',5,['G0','G1']),ticket=f.frontier.begin(grand.marker,128*1048576);f.frontier.markReady(ticket,0);f.frontier.markReady(ticket,1);f.frontier.commit(ticket,grand.meshes);complete(batch);await assert.rejects(task,SourceLoadCancelled);assert.equal(batch.disposed,true);assert.deepEqual(new Set(f.frontier.visible),new Set(['G0','G1','C1']));
});

test('two independent coarsenings sharing a parent page read it once before atomic application',async()=>{
 const {frontier,marker}=initial();marker.source_nodes[1].children=['T0','T1'];
 for(const [parent,names] of [['P',['C0','C1']],['terminal',['T0','T1']]]){const b=bundle(parent,4,names),ticket=frontier.begin(b.marker,128*1048576);frontier.markReady(ticket,0);frontier.markReady(ticket,1);frontier.commit(ticket,b.meshes);}frontier.applyMasks();frontier.releaseHiddenPages();const root=frontier.bundles.get('$root');let loads=0;
 const restored=initial();await withSourceRestorations({actions:[{root:1,parent:'P'},{root:1,parent:'terminal'}],residents:new Map([[1,{frontier}]]),stillWanted:()=>true,limit:128*1048576,load:async need=>{loads++;assert.equal(need.parts.length,1);return{marker:structuredClone(root.marker),meshes:restored.meshes,dispose(){}};},apply:batches=>{assert.equal(batches.length,1);frontier.restorePages(root,batches[0].meshes);frontier.rollback('P');frontier.rollback('terminal');frontier.applyMasks();}});
 assert.equal(loads,1);assert.deepEqual(new Set(frontier.visible),new Set(['P','terminal']));assert.equal(frontier.retainedPayloadBytes,frontier.bytes);
});

test('restoration rejects a budget overrun before issuing reads',async()=>{
 const f=releasedParent();await assert.rejects(()=>withSourceRestorations({actions:[{root:1,parent:'P'}],residents:new Map([[1,{frontier:f.frontier}]]),stillWanted:()=>true,reservedBytes:128*1048576,limit:128*1048576,load:()=>assert.fail('budget should reject before reads'),apply:()=>assert.fail('no apply')}),SourceLoadCancelled);
});

test('a fitting final parent still needs room beside the complete live child cut',async()=>{
 const f=releasedParent(),current=f.frontier.bytes,after=f.frontier.rollbackPlan('P').bytes,limit=Math.max(current,after),before=[...f.frontier.visible];
 await assert.rejects(()=>withSourceRestorations({actions:[{root:1,parent:'P'}],residents:new Map([[1,{frontier:f.frontier}]]),stillWanted:()=>true,limit,load:()=>assert.fail('temporary coexistence must reject before reads'),apply:()=>assert.fail('must keep child cut')}),SourceLoadCancelled);
 assert.deepEqual([...f.frontier.visible],before);assert.equal(f.root.meshes.size,0);
});

test('a whole-root budget eviction removes redundant descendant coarsening actions',()=>{
 const f=releasedParent(),residents=new Map([[1,{frontier:f.frontier}]]);assert.deepEqual(planSourceBudget(residents,{id:2,parent:'incoming',score:100},10*1048576,12*1048576,()=>0,()=>1),[{root:1,parent:null}]);assert.deepEqual([...f.frontier.visible],['C0','C1']);
});

test('source identity ignores leases and object key order, but checks original page fingerprints',()=>{
 const marker={schema:'x',parts:[{directory:'part_000',sha:'a'}],stamp:{a:1,b:2},cache_lease:'old'},same={stamp:{b:2,a:1},parts:[{sha:'a',directory:'part_000'}],schema:'x',cache_lease:'new'};assert.equal(sourceBundleIdentity(marker),sourceBundleIdentity(same));same.parts[0].sha='changed';assert.notEqual(sourceBundleIdentity(marker),sourceBundleIdentity(same));
});


test('a later restoration read failure disposes earlier staged pages and changes no resident',async()=>{
 const first=releasedParent(),second=releasedParent(),batch=restoredBatch(first),residents=new Map([[1,{frontier:first.frontier}],[2,{frontier:second.frontier}]]);let reads=0;
 await assert.rejects(()=>withSourceRestorations({actions:[{root:1,parent:'P'},{root:2,parent:'P'}],residents,stillWanted:()=>true,limit:128*1048576,load:async()=>{if(++reads===2)throw Error('test read unavailable');return batch;},apply:()=>assert.fail('must retain both displayed cuts')}),/test read unavailable/);
 assert.equal(reads,2);assert.equal(batch.disposed,true);for(const f of [first,second]){assert.equal(f.root.meshes.size,0);assert.deepEqual([...f.frontier.visible],['C0','C1']);}
});


test('tight atlas accepts only declared aligned bounded dimensions with exact mip accounting',()=>{
 const {marker,meshes}=initial(),m=meshes.get('part_000'),p=marker.parts[0];p.atlas_size=520;p.atlas_layout_policy='tight_square_gutter4_v1';m.material.map.source.data={width:520,height:520};let texture=0;for(let n=520;n>0;n=Math.floor(n/2))texture+=n*n*4;p.gpu_payload_bytes=p.vertices*64+p.indices*4+texture;marker.gpu_payload_bytes=p.gpu_payload_bytes;validateSourceBundle(marker,meshes);
 for(const change of [q=>delete q.atlas_layout_policy,q=>q.atlas_layout_policy='unknown',q=>q.atlas_size=521,q=>q.atlas_size=2056,q=>q.gpu_payload_bytes++]){const copy=structuredClone(marker);change(copy.parts[0]);assert.throws(()=>validateSourceBundle(copy,meshes));}
});


test('rectangular source pages validate real two-axis mip bytes and explicit clamp sampling',()=>{
 const chain=[[2048,520],[1024,260],[512,130],[256,65],[128,32],[64,16],[32,8],[16,4],[8,2],[4,1],[2,1],[1,1]];
 for(const policy of ['edge_clamped_rect_v1','edge_packed_rect_v1']) for(const [width,height] of [[2048,520],[520,2048]]){
  const {marker,meshes}=initial(),p=marker.parts[0],m=meshes.get(p.directory);
  p.atlas_layout_policy=policy;p.atlas_size=2048;p.atlas_extent=[width,height];
  m.material.map.source.data.width=width;m.material.map.source.data.height=height;
  m.material.map.wrapS=m.material.map.wrapT=ClampToEdgeWrapping;
  p.gpu_payload_bytes=p.vertices*64+p.indices*4+chain.reduce((sum,[w,h])=>sum+w*h*4,0);marker.gpu_payload_bytes=p.gpu_payload_bytes;
  validateSourceBundle(marker,meshes);
  for(const change of [q=>delete q.atlas_layout_policy,q=>q.atlas_layout_policy='unknown',q=>q.atlas_extent.reverse(),q=>q.atlas_extent=[2048,521],q=>q.gpu_payload_bytes++]){
   const copy=structuredClone(marker);change(copy.parts[0]);assert.throws(()=>validateSourceBundle(copy,meshes));
  }
  m.material.map.wrapS=RepeatWrapping;assert.throws(()=>validateSourceBundle(marker,meshes),/采样/);
 }
});
