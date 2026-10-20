import {ensureSourceWanted} from './lod_transaction.js';

const verifiedTiles=new WeakSet();
const shaPattern=/^[0-9a-f]{64}$/;
const vector=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
function checkBox(low,high){if(!vector(low)||!vector(high)||low.some((n,a)=>n>high[a]))throw Error('Invalid LEVEL bounds');}
function encloses(low,high,a,b){return a.every((v,i)=>v>=low[i]-1e-7&&b[i]<=high[i]+1e-7);}
function freeze(value){if(value&&typeof value==='object'){for(const v of Object.values(value))freeze(v);Object.freeze(value);}return value;}
const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');

// Exact AABB positive-vertex test; tangent boxes and near-plane crossings stay.
export function levelBoundsIntersect(low,high,planes){return planes.every(p=>p[0]*(p[0]>=0?high[0]:low[0])+p[1]*(p[1]>=0?high[1]:low[1])+p[2]*(p[2]>=0?high[2]:low[2])+p[3]>=-1e-7);}
export class LevelBoundsIndex{
 constructor(records,{leafSize=8}={}){
  if(!Array.isArray(records)||!records.length||!Number.isInteger(leafSize)||leafSize<1||leafSize>64)throw Error('Invalid LEVEL BVH');
  const ids=new Set();this.records=records.map(r=>{checkBox(r.boundsMin,r.boundsMax);if(!Number.isSafeInteger(r.id)||ids.has(r.id))throw Error('Duplicate LEVEL root');ids.add(r.id);return freeze(structuredClone(r));});
  const build=items=>{const low=[0,1,2].map(a=>Math.min(...items.map(i=>this.records[i].boundsMin[a]))),high=[0,1,2].map(a=>Math.max(...items.map(i=>this.records[i].boundsMax[a])));if(items.length<=leafSize)return {low,high,items};const axis=high.map((n,a)=>n-low[a]).reduce((best,n,a,ext)=>n>ext[best]?a:best,0);items.sort((i,j)=>(this.records[i].boundsMin[axis]+this.records[i].boundsMax[axis])-(this.records[j].boundsMin[axis]+this.records[j].boundsMax[axis]));const half=Math.floor(items.length/2);return {low,high,left:build(items.slice(0,half)),right:build(items.slice(half))};};
  this.tree=build(this.records.map((_,i)=>i));
 }
 query(planes){
  if(!Array.isArray(planes)||planes.length!==6||planes.some(p=>!Array.isArray(p)||p.length!==4||!p.every(Number.isFinite)||Math.hypot(...p.slice(0,3))<=0))throw Error('Invalid camera frustum');
  const hits=[],stats={visited:0,tested:0,hits:0};const visit=node=>{stats.visited++;if(!levelBoundsIntersect(node.low,node.high,planes))return;if(node.items){for(const i of node.items){stats.tested++;const r=this.records[i];if(levelBoundsIntersect(r.boundsMin,r.boundsMax,planes))hits.push(r);}}else{visit(node.left);visit(node.right);}};visit(this.tree);stats.hits=hits.length;return {records:hits,stats};
 }
}

async function readBounded(url,limit,{fetcher,stillWanted}){
 ensureSourceWanted(stillWanted);const response=await fetcher(url,{cache:'no-store'});ensureSourceWanted(stillWanted);if(!response.ok)throw Error('LEVEL index HTTP '+response.status);
 const declared=response.headers.get('Content-Length');if(declared!==null&&(!/^[0-9]+$/.test(declared)||Number(declared)>limit)){await response.body?.cancel().catch(()=>{});throw Error('LEVEL index exceeds bound');}
 if(!response.body?.getReader){const raw=new Uint8Array(await response.arrayBuffer());ensureSourceWanted(stillWanted);if(raw.byteLength>limit)throw Error('LEVEL index exceeds bound');return raw;}
 const reader=response.body.getReader(),chunks=[];let size=0;try{for(;;){ensureSourceWanted(stillWanted);const {done,value}=await reader.read();ensureSourceWanted(stillWanted);if(done)break;size+=value.byteLength;if(size>limit)throw Error('LEVEL index exceeds bound');chunks.push(value);}const raw=new Uint8Array(size);let at=0;for(const c of chunks){raw.set(c,at);at+=c.byteLength;}return raw;}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}
const parse=raw=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));

// The active read-only service pins the manifest; the manifest pins every file.
// No server-supplied URL or source path is followed.
export async function loadSourceLevelIndex({fetcher=fetch,stillWanted=()=>true,hash=digest,cacheSize=16}={}){
 if(!Number.isInteger(cacheSize)||cacheSize<1||cacheSize>16)throw Error('Invalid LEVEL cache bound');const options={fetcher,stillWanted};
 const status=parse(await readBounded('api/level-index/status',4096,options));if(status.schema!=='zhumadian.level_bounds.status.v1'||!shaPattern.test(status.identity)||status.roots!==2346||status.exactBounds!==true||status.sourceWrites!==false)throw Error('LEVEL service identity unavailable');
 const prefix='api/level-index/files/';const raw=await readBounded(prefix+'index_manifest.json',4*1048576,options);if(await hash(raw)!==status.identity)throw Error('LEVEL manifest SHA differs');
 const manifest=parse(raw);if(manifest.schema!=='zhumadian.level_bounds.manifest.v1'||!shaPattern.test(manifest.sourceManifestSHA256)||!shaPattern.test(manifest.rootIndexSHA256)||manifest.boundsSource!=='exact_original_geometry'||manifest.sourceWrites!==0||!Array.isArray(manifest.tiles)||manifest.tiles.length!==2346)throw Error('Invalid LEVEL manifest');
 const entries=new Map();for(const e of manifest.tiles){if(!Number.isInteger(e.tile)||e.tile<1||e.tile>2346||entries.has(e.tile)||e.path!==`tile_${e.tile}.json`||!shaPattern.test(e.sha256)||!Number.isSafeInteger(e.bytes)||e.bytes<1||e.bytes>16*1048576||!Number.isSafeInteger(e.sourceNodes)||e.sourceNodes<1)throw Error('Incomplete LEVEL manifest');entries.set(e.tile,freeze({...e}));}if([...entries.values()].reduce((n,e)=>n+e.sourceNodes,0)!==manifest.sourceNodes)throw Error('LEVEL node count differs');
 const rootRaw=await readBounded(prefix+'root_index.json',4*1048576,options);if(await hash(rootRaw)!==manifest.rootIndexSHA256)throw Error('LEVEL root SHA differs');const root=parse(rootRaw);
 if(root.schema!=='zhumadian.level_bounds.roots.v1'||root.sourceManifestSHA256!==manifest.sourceManifestSHA256||root.coordinateSystem!=='source_local_metres'||root.boundsSource!=='union_of_original_subtree_geometry'||root.roots?.length!==2346)throw Error('Invalid LEVEL root index');
 for(const r of root.roots){if(r.id!==r.tile||!entries.has(r.tile)||!shaPattern.test(r.catalogSHA256))throw Error('LEVEL root identity differs');}
 const index=new LevelBoundsIndex(root.roots),byRoot=new Map(index.records.map(r=>[r.tile,r])),cache=new Map(),inflight=new Map();
 const tile=async id=>{
  if(!entries.has(id))throw Error('Invalid LEVEL tile');ensureSourceWanted(stillWanted);if(cache.has(id)){const v=cache.get(id);cache.delete(id);cache.set(id,v);return v;}if(inflight.has(id))return inflight.get(id);
  if(inflight.size>=cacheSize)throw Error('LEVEL tile request bound reached');
  const job=(async()=>{const e=entries.get(id),bytes=await readBounded(prefix+e.path,e.bytes,options);if(bytes.byteLength!==e.bytes||await hash(bytes)!==e.sha256)throw Error('LEVEL tile SHA differs');const value=parse(bytes);validateLevelTile(value,{tile:id,sourceManifestSHA256:manifest.sourceManifestSHA256,catalogSHA256:byRoot.get(id).catalogSHA256,sourceNodes:e.sourceNodes,rootBounds:byRoot.get(id)});ensureSourceWanted(stillWanted);freeze(value);cache.set(id,value);while(cache.size>cacheSize)cache.delete(cache.keys().next().value);return value;})();inflight.set(id,job);try{return await job;}finally{inflight.delete(id);}
 };
 return Object.freeze({identity:status.identity,sourceManifestSHA256:manifest.sourceManifestSHA256,index,tile,get cachedTiles(){return cache.size;},get pendingTiles(){return inflight.size;}});
}

export function validateLevelTile(data,{tile,sourceManifestSHA256,catalogSHA256,sourceNodes,rootBounds}){
 if(data.schema!=='zhumadian.level_bounds.tile.v1'||data.tile!==tile||data.complete!==true||data.sourceManifestSHA256!==sourceManifestSHA256||data.catalogSHA256!==catalogSHA256||!Array.isArray(data.nodes)||data.nodes.length!==sourceNodes||data.roots?.length!==1||data.root!==data.roots[0])throw Error('Incomplete LEVEL topology');
 const nodes=new Map();for(const n of data.nodes){checkBox(n.boundsMin,n.boundsMax);checkBox(n.subtreeMin,n.subtreeMax);if(!encloses(n.subtreeMin,n.subtreeMax,n.boundsMin,n.boundsMax)||!new RegExp(`^Tile_${tile}_L[0-9]+_0[0-9u]+\\.osgb$`).test(n.name)||nodes.has(n.name)||!shaPattern.test(n.sourceSHA256)||!Number.isSafeInteger(n.sourceBytes)||n.sourceBytes<1||!Number.isInteger(n.depth)||n.depth<0||n.depth>12||!Number.isInteger(n.level)||n.level<0||!Array.isArray(n.children)||new Set(n.children).size!==n.children.length||![n.edgeP90,n.texelP90].every(x=>Number.isFinite(x)&&x>=0))throw Error('Invalid LEVEL source node');nodes.set(n.name,n);}
 const seen=new Set();const visit=(name,depth)=>{const n=nodes.get(name);if(!n||seen.has(name)||n.depth!==depth)throw Error('Disconnected, cyclic or different LEVEL topology');seen.add(name);for(const child of n.children){const c=nodes.get(child);if(!c||!encloses(n.subtreeMin,n.subtreeMax,c.subtreeMin,c.subtreeMax))throw Error('LEVEL descendant bounds differ');visit(child,depth+1);}};visit(data.root,0);if(seen.size!==nodes.size)throw Error('Unreachable LEVEL source');const r=nodes.get(data.root);if(!encloses(rootBounds.boundsMin,rootBounds.boundsMax,r.subtreeMin,r.subtreeMax))throw Error('LEVEL root envelope differs');verifiedTiles.add(data);return true;
}

// Prove a replacement antichain covers all original descendant branches. This
// is a topology proof only; pixel coverage needs a separate GPU admission test.
export function validateIndexedDescendantCut(data,parent,names){
 const nodes=new Map(data.nodes.map(n=>[n.name,n])),p=nodes.get(parent),selected=new Set(names);if(!p?.children.length||!Array.isArray(names)||!names.length||names.length>16||selected.size!==names.length||selected.has(parent))throw Error('Invalid indexed descendant cut');
 const used=new Set();const visit=name=>{const n=nodes.get(name);if(!n)throw Error('Unknown indexed descendant');if(selected.has(name)){used.add(name);return;}if(!n.children.length)throw Error('Indexed descendant cut has a missing branch');for(const c of n.children)visit(c);};for(const c of p.children)visit(c);if(used.size!==selected.size)throw Error('Indexed cut is overlapping or outside parent');return true;
}


export function validateSourceAgainstLevelTile(data,marker){
 if(!verifiedTiles.has(data)||data.tile!==marker.tile_id||!Array.isArray(marker.source_nodes)||!marker.source_nodes.length)throw Error('Unverified or different LEVEL source tree');
 const nodes=new Map(data.nodes.map(n=>[n.name,n]));
 for(const n of marker.source_nodes){const original=nodes.get(n.name);if(!original||n.source_sha256!==original.sourceSHA256||n.depth!==original.depth||JSON.stringify(n.children)!==JSON.stringify(original.children)||original.triangles!==undefined&&n.triangles!==original.triangles)throw Error('Source differs from sealed LEVEL topology');}
 return true;
}
export function validateIndexedSourceReplacement(data,marker,parent){
 validateSourceAgainstLevelTile(data,marker);
 const p=data.nodes.find(n=>n.name===parent),names=marker.source_nodes.map(n=>n.name),depths=marker.source_nodes.map(n=>n.depth);
 if(marker.schema!=='zhumadian.osgb_source_descendants.v3'||marker.complete_source_cut!==true||marker.replacement_parent!==parent||!p||marker.parent_source_sha256!==p.sourceSHA256||!shaPattern.test(marker.source_cut_key)||marker.min_depth!==Math.min(...depths)||marker.max_depth!==Math.max(...depths))throw Error('Indexed source cut identity differs');
 return validateIndexedDescendantCut(data,parent,names);
}


// Match native initial coverage: choose the coarsest measured complete texture
// tier meeting six projected pixels, then refine shape with complete source cuts.
export function initialIndexedCoverageDepth(record,proposed,scale,distance){
 if(!Number.isInteger(proposed)||proposed<1||!Number.isFinite(scale)||scale<=0||!Number.isFinite(distance)||distance<=0)throw Error('Invalid indexed coverage projection');
 if(record.coverageTiers===undefined)return proposed;
 const tiers=record.coverageTiers;if(!Array.isArray(tiers)||tiers.length>3)throw Error('Invalid measured coverage tiers');const seen=new Set();
 for(const t of tiers){if(!Number.isInteger(t.depth)||t.depth<1||t.depth>3||seen.has(t.depth)||!Number.isSafeInteger(t.sourceCount)||t.sourceCount<1||!Number.isFinite(t.maxTexel)||t.maxTexel<=0)throw Error('Invalid measured coverage tier');seen.add(t.depth);}
 for(let depth=1;depth<Math.min(proposed,3);depth++){const t=tiers.find(t=>t.depth===depth);if(t&&t.maxTexel*4*scale/distance<=6)return depth;}return proposed;
}
export function indexedResidentCapacity(rootCount){if(!Number.isInteger(rootCount)||rootCount<1||rootCount>2346)throw Error('Invalid sealed root capacity');return rootCount;}
