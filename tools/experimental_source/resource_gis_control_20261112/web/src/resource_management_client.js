// Host supplies its original authenticated transport; no global fetch or stored credentials.
import{readJSON}from'./http_json.js';
const failure=code=>Object.assign(Error(code),{code});
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const identifier=x=>typeof x==='string'&&/^[a-f0-9]{32}$/.test(x);
const paths=['gis','renderData','icons','downloads','dlgDrafts','sceneDrafts'];
const terminal=new Set(['passed','failed','cancelled']);
export const RESOURCE_TOPIC='resource-management';
export function validateResourceConfiguration(value){
 if(!object(value)||value.schema!=='xnby.client-resources.configuration.v1'||typeof value.workspaceRoot!=='string'||value.workspaceRoot.length>1024||!value.workspaceRoot||/[\x00-\x1f]/.test(value.workspaceRoot)||typeof value.canConfigure!=='boolean'||typeof value.saved!=='boolean'||!object(value.paths)||Object.keys(value.paths).length!==paths.length)throw failure('RESOURCE_RESPONSE_INVALID');
 for(const key of paths){const path=value.paths[key];if(typeof path!=='string'||path.length>512||!path||path.split('/').some(p=>!p||p==='.'||p==='..'||/[\\:\x00-\x1f]/.test(p)))throw failure('RESOURCE_RESPONSE_INVALID');}
 return value;
}
export function validateResourceAudit(value){
 if(!object(value)||value.schema!=='xnby.client-resources.audit.v1'||!identifier(value.id)||!['preflight','running','cancelling',...terminal].includes(value.state)||!object(value.progress))throw failure('RESOURCE_RESPONSE_INVALID');
 for(const key of['expectedFiles','completedFiles','verifiedFiles','readBytes','expectedBytes','catalogsValidated','stabilityFiles'])if(Object.hasOwn(value.progress,key)&&(!Number.isSafeInteger(value.progress[key])||value.progress[key]<0))throw failure('RESOURCE_RESPONSE_INVALID');
 if(value.reportId!==null&&!identifier(value.reportId))throw failure('RESOURCE_RESPONSE_INVALID');
 if(value.state==='passed'&&(!object(value.result)||value.result.passed!==true))throw failure('RESOURCE_RESPONSE_INVALID');
 if(value.state==='cancelled'&&(!object(value.result)||value.result.cancelled!==true))throw failure('RESOURCE_RESPONSE_INVALID');
 return value;
}
export function validateResourceGISStatus(v){
 if(!object(v)||v.schema!=='xnby.client-resources.gis-status.v1'||!['unconfigured','missing-workspace','stopped','starting','ready','stopping','recovery-required'].includes(v.phase)||typeof v.owned!=='boolean'||typeof v.operationActive!=='boolean')throw failure('RESOURCE_RESPONSE_INVALID');return v;
}
export function validateResourceGISOperation(v){
 if(!object(v)||v.schema!=='xnby.client-resources.gis-operation.v1'||!identifier(v.id)||!['start','stop'].includes(v.action)||!['preflight','running','completed','failed','cancelled'].includes(v.state)||typeof v.accepted!=='boolean'||typeof v.phase!=='string'||!/^[a-z-]{1,60}$/.test(v.phase))throw failure('RESOURCE_RESPONSE_INVALID');
 if(v.state==='completed'&&(!object(v.result)||!['stopped','starting','ready','stopping','recovering'].includes(v.result.phase)||typeof v.result.observationExpired!=='boolean'))throw failure('RESOURCE_RESPONSE_INVALID');return v;
}
export function createResourceManagementClient({request}={}){
 if(typeof request!=='function')throw failure('RESOURCE_AUTHENTICATED_TRANSPORT_REQUIRED');
 let retired=false,epoch=0;const pending=new Set();
 async function call(route,method='GET',body){
  if(retired)throw failure('RESOURCE_CLIENT_RETIRED');const generation=epoch,control=new AbortController();pending.add(control);
  try{
   const response=await request('api/client-resources/v1/'+route,{method,signal:control.signal,...(body===undefined?{}:{body:JSON.stringify(body),headers:{'Content-Type':'application/json'}})});
   if(retired||generation!==epoch)throw failure('RESOURCE_CLIENT_RETIRED');
   if(response.status===401||response.status===403){try{await response.body?.cancel();}catch{}throw failure('RESOURCE_AUTHORIZATION_REQUIRED');}
   const{document}=await readJSON(response,262144);if(retired||generation!==epoch)throw failure('RESOURCE_CLIENT_RETIRED');
   if(!response.ok)throw failure(typeof document?.code==='string'&&/^[A-Z_]{1,80}$/.test(document.code)?document.code:'RESOURCE_REQUEST_FAILED');
   return document;
  }finally{pending.delete(control);}
 }
 function id(value){if(!identifier(value))throw failure('RESOURCE_IDENTIFIER_INVALID');return value;}
 return Object.freeze({
  async gisStatus(){return validateResourceGISStatus(await call('gis/status'));},
  async startGIS(){return validateResourceGISOperation(await call('gis/start','POST',{}));},
  async stopGIS(){return validateResourceGISOperation(await call('gis/stop','POST',{}));},
  async gisOperation(value){return validateResourceGISOperation(await call('gis/operations/'+id(value)));},
  async configuration(){return validateResourceConfiguration(await call('configuration'));},
  async save(workspaceRoot){if(typeof workspaceRoot!=='string'||!workspaceRoot||workspaceRoot.length>1024||/[\x00-\x1f]/.test(workspaceRoot))throw failure('RESOURCE_WORKSPACE_INVALID');return validateResourceConfiguration(await call('configuration','POST',{workspaceRoot}));},
  async startAudit(){return validateResourceAudit(await call('audits','POST',{}));},
  async audit(value){return validateResourceAudit(await call('audits/'+id(value)));},
  async cancelAudit(value){return validateResourceAudit(await call('audits/'+id(value)+'/cancel','POST',{}));},
  async reports(){const v=await call('reports');if(!object(v)||v.schema!=='xnby.client-resources.reports.v1'||!Array.isArray(v.reports)||v.reports.length>32||v.reports.some(r=>!object(r)||!identifier(r.id)||typeof r.createdAt!=='string'||r.createdAt.length>80))throw failure('RESOURCE_RESPONSE_INVALID');return v.reports;},
  async report(value){const v=await call('reports/'+id(value));if(!object(v)||v.schema!=='xnby.offline-osgb.integrity.v1'||typeof v.passed!=='boolean'||typeof v.cancelled!=='boolean'||!Number.isSafeInteger(v.issueCount)||v.issueCount<0)throw failure('RESOURCE_RESPONSE_INVALID');return v;},
  close(){if(retired)return;retired=true;epoch++;for(const p of pending)p.abort();pending.clear();},
  get closed(){return retired;}
 });
}
