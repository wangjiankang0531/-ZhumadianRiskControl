const TIERS=Object.freeze([512,1024,2048]);
export function resolveSourceBudget({configuredMiB=512,qa=false,requestedMiB=null}={}){
 if(!Number.isInteger(configuredMiB)||!TIERS.includes(configuredMiB))throw Error('Unsupported configured source budget');
 let mib=configuredMiB,source='configured';
 if(qa&&requestedMiB!==null){if(typeof requestedMiB!=='string'||!TIERS.map(String).includes(requestedMiB))throw Error('Unsupported QA source budget');mib=Number(requestedMiB);source='qa_override';}
 return Object.freeze({schema:'xnby.source_budget_policy.v1',mib,bytes:mib*1024*1024,source,configuredMiB,scope:'tracked_source_geometry_textures_staging_restore_and_fixed_targets_not_total_vram'});
}
export async function loadSourceBudgetPolicy({search='',fetchConfig,timeoutMs=2500}={}){
 const query=new URLSearchParams(search);let configuredMiB=512,notice=null;
 try{
  if(typeof fetchConfig!=='function')throw Error('Missing configuration reader');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
   const response=await fetchConfig('application/config.json',{cache:'no-store',credentials:'omit',redirect:'error',referrerPolicy:'no-referrer',signal:controller.signal});if(!response.ok)throw Error('Viewer configuration unavailable');
   const config=await response.json(),value=response.headers?.get?.('X-XNBY-Source-Budget-MiB');
   if(value!==undefined&&value!==null){if(config.schema!=='xnby.portal.config.v1'||!TIERS.map(String).includes(value))throw Error('Viewer budget header differs');configuredMiB=resolveSourceBudget({configuredMiB:Number(value)}).mib;}
  }finally{clearTimeout(timer);}
 }catch(error){configuredMiB=512;notice=String(error.message??error);}
 const resolved=resolveSourceBudget({configuredMiB,qa:query.get('qa')==='1',requestedMiB:query.get('sourceBudgetMiB')});return Object.freeze({...resolved,notice});
}
