// Metadata-only recovery planning. Copies own their maps, never live meshes.
// A final target is not permission to upload: every individual coexistence peak
// must fit and the estimated loss of each full intermediate cut must stay within
// the final target's combined estimate. These are source-quality model scores.
import {sourceRestorationFootprint} from './source_page_budget.js';
import {SourceLoadCancelled} from './lod_transaction.js';

export function sourceRecoverySnapshot(residents){return JSON.stringify([...residents].map(([root,ready])=>[root,ready.frontier.cutVersion,[...ready.frontier.visible].sort(),[...ready.frontier.bundles.keys()].sort(),ready.frontier.bytes]));}
function clones(residents){return new Map([...residents].map(([root,ready])=>{const frontier=ready.frontier.copyForPlanning();frontier.bundles=new Map([...frontier.bundles].map(([key,bundle])=>[key,{...bundle,meshes:new Map(bundle.meshes)}]));return [root,{frontier}];}));}
function simulate(states,action){
 if(action.parent===null){states.delete(action.root);return;}
 const f=states.get(action.root).frontier,plan=f.rollbackPlan(action.parent);
 for(const {bundle,part} of plan.missingPages)bundle.meshes.set(part.directory,{});
 if(!f.rollback(action.parent).length)throw Error('Recovery simulation made no progress');
 for(const bundle of f.bundles.values()){
  const needed=new Set(bundle.marker.source_nodes.filter(n=>f.visible.has(n.name)).flatMap(n=>n.spans.map(s=>s.part)));
  for(const directory of bundle.meshes.keys())if(!needed.has(directory))bundle.meshes.delete(directory);
 }
}

export function planSourceRecoverySequence(residents,request,cost,limit,priority,rootPriority=null){
 const states=clones(residents),steps=[],qualityActions=[];let used=[...states.values()].reduce((sum,r)=>sum+r.frontier.bytes,0),peak=used,loss=0,remaining=1+[...states.values()].reduce((sum,r)=>sum+r.frontier.bundles.size+1,0);
 while(used+cost>limit){
  if(--remaining<0)return null;const choices=[];
  for(const [root,ready] of states){const f=ready.frontier,original=residents.get(root).frontier;
   const admit=(action,freed,nextQuality)=>{const nextLoss=nextQuality.reduce((sum,a)=>sum+a.loss,0);if(freed<=0||nextLoss<loss||!(nextLoss*2<request.score))return;const uploadPeak=sourceRestorationFootprint(states,[action]);if(uploadPeak<=limit)choices.push({action,freed,quality:nextQuality,loss:nextLoss,peak:uploadPeak,ratio:(nextLoss-loss)/freed});};
   for(const parent of f.bundles.keys())if(parent!=='$root'){
    const plan=f.rollbackPlan(parent);if(root===request.id&&plan.subtree.has(request.parent))continue;
    const originalPlan=original.rollbackPlan(parent),action={root,parent},score=priority(root,original.nodes.get(parent).node,originalPlan.subtree);
    admit(action,f.bytes-plan.bytes,[...qualityActions.filter(a=>a.root!==root||!originalPlan.subtree.has(a.parent)),{...action,loss:score}]);
   }
   if(rootPriority&&root!==request.id){const action={root,parent:null};admit(action,f.bytes,[...qualityActions.filter(a=>a.root!==root),{...action,loss:rootPriority(root,new Set(original.visible))}]);}
  }
  choices.sort((a,b)=>a.ratio-b.ratio||b.freed-a.freed||a.peak-b.peak||a.action.root-b.action.root||String(a.action.parent).localeCompare(String(b.action.parent)));
  const choice=choices[0];if(!choice)return null;const before=sourceRecoverySnapshot(states);simulate(states,choice.action);peak=Math.max(peak,choice.peak);qualityActions.splice(0,qualityActions.length,...choice.quality);loss=choice.loss;used=[...states.values()].reduce((sum,r)=>sum+r.frontier.bytes,0);
  steps.push({...choice.action,before,after:sourceRecoverySnapshot(states),uploadPeakBytes:choice.peak,estimatedTotalLoss:loss});
 }
 return {steps,targets:qualityActions.map(({root,parent})=>({root,parent})),limit,cost,finalBytes:used,peakBytes:Math.max(peak,used+cost)};
}

// Each completed step is a valid complete cut. Cancellation or read failure
// preserves that last complete cut, and never uploads the incoming family.
export async function applySourceRecoverySequence({sequence,residents,stillWanted,apply}){
 if(!sequence?.steps.length)return false;
 for(let i=0;i<sequence.steps.length;i++){
  const step=sequence.steps[i];if(!stillWanted()||sourceRecoverySnapshot(residents)!==step.before)throw new SourceLoadCancelled();
  if(!await apply([{root:step.root,parent:step.parent}],stillWanted,i===sequence.steps.length-1?sequence.cost:0))return false;
  if(sourceRecoverySnapshot(residents)!==step.after)throw new SourceLoadCancelled();
 }
 return true;
}
