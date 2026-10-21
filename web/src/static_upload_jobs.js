// Both jobs stage detached resources. A failed job cancels its sibling, waits
// for cleanup, and disposes already completed resources before rejecting.
export async function runStaticUploadJobs(jobs,{concurrency=2,stillWanted=()=>true}={}){
 if(!Array.isArray(jobs)||jobs.length!==2||jobs.some(j=>typeof j!=='function')||![1,2].includes(concurrency))throw Error('Invalid static upload jobs');
 let cursor=0,failure=null;const values=new Array(jobs.length),completed=[];const wanted=()=>!failure&&stillWanted();
 const worker=async()=>{while(!failure&&cursor<jobs.length){const index=cursor++;try{if(!wanted())throw Error('Static uploads cancelled');const value=await jobs[index](wanted);values[index]=value;completed.push(value);if(!wanted())throw Error('Static uploads cancelled');}catch(error){if(!failure)failure=error;}}};
 await Promise.all(Array.from({length:concurrency},worker));
 if(failure){for(const value of completed)try{value?.dispose?.();}catch{}throw failure;}
 return values;
}
