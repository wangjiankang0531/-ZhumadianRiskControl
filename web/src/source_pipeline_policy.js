// Default acceleration is scoped to the independently negotiated complete index.
// A query override is an acceptance option only when qa=1.
export function sourcePipelinePolicy({verifiedOriginalIndex=false,search=''}={}){
 if(typeof verifiedOriginalIndex!=='boolean')throw Error('Invalid source pipeline capability');
 const params=new URLSearchParams(search),qa=params.get('qa')==='1',root=qa?params.get('planAhead'):null,geometry=qa?params.get('geometryReads'):null,pages=qa?params.get('pageLoads'):null;
 return Object.freeze({rootLookahead:root==='0'?false:root==='1'?true:verifiedOriginalIndex,geometryReads:geometry==='1'?1:geometry==='2'?2:verifiedOriginalIndex?2:1,pageLoads:pages==='2'?2:1,verifiedOriginalIndex,scope:'one_metadata_plan_and_at_most_two_geometry_files_per_page; fresh_GPU_admission_and_single_prepared_page_default'});
}
