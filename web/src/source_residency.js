import {SourceLoadCancelled,ensureSourceWanted} from './lod_transaction.js';
import {validateSourcePart} from './source_frontier.js';
import {sourceRestorationFootprint} from './source_page_budget.js';

export class SourceRestoreUnavailable extends Error{constructor(message){super(message);this.name='SourceRestoreUnavailable';}}

const stable=value=>Array.isArray(value)?value.map(stable):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,stable(value[key])])):value;
export function sourceBundleIdentity(marker){return JSON.stringify(stable(Object.fromEntries(['schema','complete_source_cut','source_cut_key','min_depth','max_depth','source_format','parent_source_sha256','longest_edge_p90_m','texel_world_p90_m','tile_id','depth','replacement_parent','family_key','texture_policy','source_nodes','parts','stamp','gpu_payload_bytes','indices'].map(key=>[key,marker[key]]))));}

// Load all missing parent pages while the live cut remains untouched. The caller
// applies one synchronous cut change only after every page and snapshot is valid.
export async function withSourceRestorations({actions,residents,load,stillWanted,apply,reservedBytes=0,limit}){
 const snapshots=new Map(),requirements=new Map(),batches=[];
 for(const action of actions){const ready=residents.get(action.root);if(!ready)throw new SourceLoadCancelled();snapshots.set(action.root,{ready,frontier:ready.frontier,version:ready.frontier.cutVersion});}
 const current=()=>stillWanted()&&[...snapshots].every(([id,s])=>residents.get(id)===s.ready&&s.ready.frontier===s.frontier&&s.frontier.cutVersion===s.version);
 const preview=()=>{
  const copies=new Map([...residents].map(([id,ready])=>[id,ready.frontier.copyForPlanning()]));
  for(const action of actions){const copy=copies.get(action.root);if(!copy)throw new SourceLoadCancelled();if(action.parent===null)copies.delete(action.root);else if(!copy.rollback(action.parent).length)throw new SourceLoadCancelled();}
  if([...copies.values()].reduce((sum,copy)=>sum+copy.bytes,0)+reservedBytes>limit)throw new SourceLoadCancelled();
 };
 ensureSourceWanted(current);preview();if(sourceRestorationFootprint(residents,actions)>limit)throw new SourceLoadCancelled();
 for(const action of actions)if(action.parent!==null){
  const {ready}=snapshots.get(action.root),plan=ready.frontier.rollbackPlan(action.parent);if(!plan)throw new SourceLoadCancelled();
  for(const {bundle,part} of plan.missingPages){if(!requirements.has(bundle))requirements.set(bundle,{root:action.root,ready,bundle,parts:new Map()});requirements.get(bundle).parts.set(part.directory,part);}
 }
 try{
  for(const need of requirements.values()){
   try{ensureSourceWanted(current);const batch=await load({...need,parts:[...need.parts.values()]},current);batches.push(batch);ensureSourceWanted(current);
   if(sourceBundleIdentity(batch.marker)!==sourceBundleIdentity(need.bundle.marker)||batch.meshes.size!==need.parts.size)throw Error('回退源包与当前场景不一致');
   for(const [directory,part] of need.parts){if(need.bundle.meshes.has(directory))throw new SourceLoadCancelled();validateSourcePart(part,batch.meshes.get(directory));}
   batch.root=need.root;batch.ready=need.ready;batch.bundle=need.bundle;
   }catch(error){if(error instanceof SourceLoadCancelled)throw error;throw new SourceRestoreUnavailable(error.message);}
  }
  ensureSourceWanted(current);preview();return apply(batches);
 }finally{for(const batch of batches)batch.dispose();}
}
