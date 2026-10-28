// Bounded observation only. It never adds/removes residents or changes ranking.
export class SourceDemandHistory {
 constructor({capacity=32,rows=20}={}){if(!Number.isInteger(capacity)||capacity<1||capacity>64||!Number.isInteger(rows)||rows<1||rows>32)throw Error('Invalid demand observation bound');this.capacity=capacity;this.rows=rows;this.observations=0;this.viewChanges=0;this.sameViewDemandChanges=0;this.retiredRoots=0;this.previous=null;this.events=[];}
 record({view,wanted,loaded,decisions,timeMs,epoch,pending}){
  if(!Array.isArray(view)||view.length<6||view.length>16||!view.every(Number.isFinite)||![wanted,loaded].every(v=>Array.isArray(v)&&v.length<=2346&&new Set(v).size===v.length&&v.every(n=>Number.isInteger(n)&&n>=1&&n<=2346))||!(decisions instanceof Map)||!Number.isFinite(timeMs)||timeMs<0||!Number.isSafeInteger(epoch)||epoch<0||pending!==null&&typeof pending!=='string')throw Error('Invalid demand observation');
  const key=JSON.stringify(view),ids=[...wanted].sort((a,b)=>a-b),previous=this.previous,sameView=previous?.key===key,demandChanged=!!previous&&JSON.stringify(previous.ids)!==JSON.stringify(ids),desired=new Set(wanted),retired=loaded.filter(id=>!desired.has(id));
  this.observations++;if(previous&&!sameView)this.viewChanges++;if(sameView&&demandChanged)this.sameViewDemandChanges++;this.retiredRoots+=retired.length;
  if(!previous||!sameView||demandChanged||retired.length){
   const details=retired.slice(0,this.rows).map(root=>{const decision=decisions.get(root)??{reason:'bounds_index_not_selected'};return {root,...structuredClone(decision)};});
   this.events.push({timeMs,epoch,pending,view:[...view],sameView:!!sameView,demandChanged,wanted:ids.length,loaded:loaded.length,retired:retired.length,details,truncated:retired.length>details.length});if(this.events.length>this.capacity)this.events.shift();
  }
  this.previous={key,ids};
 }
 snapshot(){return structuredClone({scope:'bounded_demand_observation_not_budget_or_visibility_authority',observations:this.observations,viewChanges:this.viewChanges,sameViewDemandChanges:this.sameViewDemandChanges,retiredRoots:this.retiredRoots,events:this.events});}
}
