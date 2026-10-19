export const classifications={'needs-verification':'待进一步核实','short-fluctuation':'短时波动','persistent':'持续异常','suspected-device':'疑似设备问题','emergency-concern':'建议应急关注'};
export const conclusions={'false-alarm':'误报','short-anomaly':'短时异常','device-fault':'设备故障','no-obvious-anomaly':'现场无明显异常','possibly-enterprise':'可能与企业活动有关','continue':'继续关注','emergency':'建议转应急关注'};
export const cooperationStates={explained:'已说明情况','supplement-required':'需补充材料',following:'继续跟踪','measures-taken':'已采取措施','focus-suggested':'建议纳入重点关注'};
export const activities={production:'生产',storage:'储存',pipeline:'管线',emission:'排放',loading:'装卸',maintenance:'检维修','special-work':'特殊作业',unknown:'尚不明确'};
export const eventStates={attention:'待关注',verified:'已核实',archived:'已归档'};
export const handoffStates={'pending-delivery':'待发送（未收到应急回执）',accepted:'应急系统已接收',rejected:'应急系统未接收',completed:'应急系统已完成'};
export const historyKinds={source:'来源事件', 'source-update':'来源更新',classify:'分类记录',verify:'现场核实',cooperate:'企业说明',material:'材料提交','handoff-request':'发起转办','handoff-result':'应急回执',archive:'归档',reopen:'重新关注',restricted:'其它企业记录（内容受限）'};
const fail=()=>Object.assign(Error('INVALID_BODY'),{code:'INVALID_BODY'});
export function verificationPayload(values,revision,materialRefs){
 const number=(key,min,max)=>{if(typeof values[key]!=='string'||!values[key].trim())throw fail();const value=Number(values[key]);if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(values[key])||!Number.isFinite(value)||value<min||value>max)throw fail();return value;};
 if(!Object.hasOwn(conclusions,values.conclusion)||typeof values.note!=='string'||!values.note.trim()||typeof values.verifiedAt!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/.test(values.verifiedAt)||!Number.isFinite(Date.parse(values.verifiedAt)))throw fail();
 if(!Number.isInteger(revision)||revision<1||!Array.isArray(materialRefs)||materialRefs.length>64||new Set(materialRefs).size!==materialRefs.length||materialRefs.some(id=>!/^[a-f0-9]{32}$/.test(id)))throw fail();
 const calendar=new Date(values.verifiedAt.slice(0,10)+'T00:00:00Z');if(!Number.isFinite(calendar.getTime())||calendar.toISOString().slice(0,10)!==values.verifiedAt.slice(0,10))throw fail();
 return {revision,conclusion:values.conclusion,note:values.note,verifiedAt:values.verifiedAt,location:{crs:'EPSG:4326',longitude:number('longitude',-180,180),latitude:number('latitude',-90,90),accuracyMeters:number('accuracyMeters',0,50000),capturedAt:values.verifiedAt,method:'manual'},materialRefs:[...materialRefs]};
}
export function canArchive(event){if(!event.verification||event.handoff&&['pending-delivery','accepted'].includes(event.handoff.state))return false;return ['false-alarm','short-anomaly','device-fault','no-obvious-anomaly'].includes(event.verification.conclusion)||event.handoff?.state==='completed'&&event.handoff.package?.source.document.sourceRevision===event.source.document.sourceRevision;}
export function canHandoff(event){return !!event.verification&&(!event.handoff||['rejected','completed'].includes(event.handoff.state));}
