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
export function chooseFeasibleSourceCandidate(candidates,{indexed=false,hasRoot=()=>false,feasible}){
 chooseRefinementCandidate(candidates);if(typeof feasible!=='function')throw Error('Missing source feasibility probe');
 const coverage=c=>indexed&&c.kind==='root'&&!hasRoot(c.id),lex=(a,b)=>a.key<b.key?-1:a.key>b.key?1:0;
 const ordered=candidates.filter(c=>c.score>0).sort((a,b)=>{const ac=coverage(a),bc=coverage(b);if(ac!==bc)return ac?-1:1;if(ac)return b.score-a.score||lex(a,b);const au=a.cost===null,bu=b.cost===null;if(au!==bu)return au?-1:1;return (au?0:b.score/b.cost-a.score/a.cost)||b.score-a.score||lex(a,b);});
 for(const c of ordered){if(c.cost===null)return c;const ok=feasible(c);if(typeof ok!=='boolean')throw Error('Invalid source feasibility result');if(ok)return c;}return null;
}
