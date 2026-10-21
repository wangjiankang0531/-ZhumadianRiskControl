// Lazy benefit-per-byte selection. Unknown costs need metadata only; measured
// gains replace upper bounds before a candidate may reserve GPU memory.
export function chooseRefinementCandidate(candidates){
 const seen=new Set();let best=null;
 for(const c of candidates){
  if(typeof c.key!=='string'||!c.key||seen.has(c.key)||!Number.isFinite(c.score)||c.score<0||c.cost!==null&&(!Number.isSafeInteger(c.cost)||c.cost<=0))throw Error('Invalid refinement candidate');
  seen.add(c.key);if(!c.score)continue;
  if(!best){best=c;continue;}
  const unknown=c.cost===null,priorUnknown=best.cost===null;
  if(unknown!==priorUnknown){if(unknown)best=c;continue;}
  const density=unknown?0:c.score/c.cost,prior=priorUnknown?0:best.score/best.cost;
  if(density>prior||density===prior&&(c.score>best.score||c.score===best.score&&c.key<best.key))best=c;
 }
 return best;
}


// Indexed mode follows the native coverage phase: seed still-visible roots
// before spending the remaining budget on local refinement. Merely learning a
// cost is not a reason to abandon a useful in-flight complete source load.
export function chooseIndexedCoverageCandidate(candidates,hasRoot){
 const refinement=chooseRefinementCandidate(candidates);let coverage=null;
 for(const c of candidates)if(c.kind==='root'&&!hasRoot(c.id)&&c.score>0&&(!coverage||c.score>coverage.score||c.score===coverage.score&&c.key<coverage.key))coverage=c;
 return coverage??refinement;
}

// Sorting is independent of feasibility. Probe in exactly the previous winner
// order and stop at its first admissible candidate, avoiding exhaustive plans.
function orderedSourceCandidates(candidates,{indexed=false,hasRoot=()=>false}={}){
 chooseRefinementCandidate(candidates);
 const coverage=c=>indexed&&c.kind==='root'&&!hasRoot(c.id),lex=(a,b)=>a.key<b.key?-1:a.key>b.key?1:0;
 const ordered=candidates.filter(c=>c.score>0).sort((a,b)=>{const ac=coverage(a),bc=coverage(b);if(ac!==bc)return ac?-1:1;if(ac)return b.score-a.score||lex(a,b);const au=a.cost===null,bu=b.cost===null;if(au!==bu)return au?-1:1;return (au?0:b.score/b.cost-a.score/a.cost)||b.score-a.score||lex(a,b);});
 return ordered;
}

export function chooseFeasibleSourceCandidate(candidates,options){
 if(typeof options?.feasible!=='function')throw Error('Missing source feasibility probe');
 for(const c of orderedSourceCandidates(candidates,options)){if(c.cost===null)return c;const ok=options.feasible(c);if(typeof ok!=='boolean')throw Error('Invalid source feasibility result');if(ok)return c;}return null;
}

// A cursor over the complete original priority order. No candidate count limit:
// time is checked between indivisible probes, so one probe can exceed a slice.
// The caller must invalidate on every input change before consuming a result.
export class SourceAllocationScan{
 constructor(candidates,options){if(typeof options?.feasible!=='function')throw Error('Missing source feasibility probe');this.ordered=orderedSourceCandidates(candidates,options);this.feasible=options.feasible;this.cursor=0;this.probes=0;this.slices=0;this.yields=0;this.done=false;this.cancelled=false;this.candidate=null;}
 cancel(){this.done=true;this.cancelled=true;this.candidate=null;return this.snapshot();}
 snapshot(){return {done:this.done,cancelled:this.cancelled,candidate:this.candidate,cursor:this.cursor,total:this.ordered.length,probes:this.probes,slices:this.slices,yields:this.yields};}
 step({budgetMs=4,clock=()=>performance.now(),isCurrent=()=>true}={}){
  if(!Number.isFinite(budgetMs)||budgetMs<=0||typeof clock!=='function'||typeof isCurrent!=='function')throw Error('Invalid allocation scan slice');
  if(!isCurrent())return this.cancel();if(this.done)return this.snapshot();
  const start=clock();if(!Number.isFinite(start))throw Error('Invalid allocation scan clock');this.slices++;
  try{while(this.cursor<this.ordered.length){
   const c=this.ordered[this.cursor];let ok=true;if(c.cost!==null){this.probes++;ok=this.feasible(c);if(typeof ok!=='boolean')throw Error('Invalid source feasibility result');}
   this.cursor++;if(ok){this.candidate=c;this.done=true;return this.snapshot();}
   if(this.cursor<this.ordered.length){const now=clock();if(!Number.isFinite(now)||now<start)throw Error('Invalid allocation scan clock');if(now-start>=budgetMs){this.yields++;return this.snapshot();}}
  }this.done=true;return this.snapshot();}catch(error){this.cancel();throw error;}
 }
}
