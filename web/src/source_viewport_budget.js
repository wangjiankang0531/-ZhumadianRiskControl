import {coverageDimensions} from './source_coverage.js';
import {planSourceRecoverySequence,applySourceRecoverySequence} from './source_recovery_plan.js';
import {ensureSourceWanted} from './lod_transaction.js';

// Resize is required fixed overhead, not an incoming detail with invented gain.
// Every intermediate original-source cut and restore coexistence peak still fit.
export async function resizeSourceViewport({width,height,guard,ledger,residents,priority,rootPriority,apply,stillWanted,onPlan=()=>{},onStep=()=>{}}){
 const target=coverageDimensions(width,height),beforeHeld=ledger.held;ensureSourceWanted(stillWanted);
 if(ledger.held-guard.bytes+target.bytes<=ledger.limit){guard.resize(width,height);return {rebalanced:false,steps:0,rootFallbacks:0,beforeHeld,afterHeld:ledger.held,targetBytes:target.bytes};}
 guard.release();ensureSourceWanted(stillWanted);
 const used=[...residents.values()].reduce((sum,r)=>sum+r.frontier.bytes,0),fixed=ledger.held-used,capacity=ledger.limit-fixed;
 if(!Number.isSafeInteger(fixed)||fixed<0||target.bytes>capacity)throw Error('Viewport budget partition unavailable');
 const sequence=planSourceRecoverySequence(residents,{id:0,parent:null,score:0},target.bytes,capacity,priority,rootPriority,{resourceKind:'viewport'});
 if(!sequence)throw Error('No complete viewport budget recovery fits');onPlan({capacity,sequence});
 let steps=0,rootFallbacks=0;
 if(sequence.steps.length){const applied=await applySourceRecoverySequence({sequence,residents,stillWanted,apply:async(actions,current,reserved)=>{const ok=await apply(actions,current,reserved,capacity);if(ok){steps++;rootFallbacks+=actions.filter(a=>a.parent===null).length;onStep({step:steps,actions,held:ledger.held});}return ok;}});if(!applied)throw Error('Viewport budget recovery did not commit');}
 ensureSourceWanted(stillWanted);if(ledger.held+target.bytes>ledger.limit)throw Error('Viewport allocation changed before admission');guard.resize(width,height);
 return {rebalanced:true,steps,rootFallbacks,beforeHeld,afterHeld:ledger.held,targetBytes:target.bytes,estimatedLoss:sequence.steps.at(-1)?.estimatedTotalLoss??0};
}
