// Evidence remains a download, never executable content or an inline document.
export const materialMaxBytes=8*1048576;
const types={'application/pdf':['.pdf'],'image/png':['.png'],'image/jpeg':['.jpg','.jpeg']},sha=/^[a-f0-9]{64}$/;
const failure=code=>Object.assign(new Error(code),{code});
function nameType(name,type){if(typeof name!=='string'||!name.trim()||name!==name.trim()||new TextEncoder().encode(name).length>256||name.includes(String.fromCharCode(92))||/[\/:\x00-\x1f\x7f]/.test(name)||/\p{Cf}/u.test(name)||!types[type]?.some(s=>name.toLowerCase().endsWith(s)))throw failure('MATERIAL_INVALID');}
async function digest(raw){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(n=>n.toString(16).padStart(2,'0')).join('');}
export async function prepareMaterialUpload(file,revision,description){
 if(!file||typeof file.name!=='string'||!Number.isSafeInteger(file.size)||file.size<1||file.size>materialMaxBytes||!Number.isSafeInteger(revision)||revision<1)throw failure('MATERIAL_INVALID');
 const mediaType=file.type||Object.entries(types).find(([,suffixes])=>suffixes.some(s=>file.name.toLowerCase().endsWith(s)))?.[0];nameType(file.name,mediaType);
 if(typeof description!=='string'||!description.trim()||new TextEncoder().encode(description).length>4000||/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(description))throw failure('MATERIAL_INVALID');
 const raw=new Uint8Array(await file.arrayBuffer());if(raw.byteLength!==file.size)throw failure('MATERIAL_INVALID');let text='';for(let i=0;i<raw.length;i+=32768)text+=String.fromCharCode(...raw.subarray(i,i+32768));
 return {payload:{revision,name:file.name,mediaType,description,base64:btoa(text)},sha256:await digest(raw)};
}
export async function readMaterialResponse(response,metadata,stillCurrent=()=>true){
 const wanted=()=>{if(!stillCurrent())throw failure('CANCELLED');};wanted();
 if(!metadata||!Number.isSafeInteger(metadata.bytes)||metadata.bytes<1||metadata.bytes>materialMaxBytes||!sha.test(metadata.sha256)||!/^[a-f0-9]{32}$/.test(metadata.id))throw failure('DATA_INVALID');
 try{nameType(metadata.name,metadata.mediaType);}catch{throw failure('DATA_INVALID');}
 const length=response.headers.get('Content-Length'),disposition=response.headers.get('Content-Disposition')??'',identity=response.headers.get('X-XNBY-Authorization-Version'),filename=/filename\*=UTF-8''([^;]+)/i.exec(disposition);
 let decodedName;try{decodedName=filename?decodeURIComponent(filename[1]):null;}catch{throw failure('DATA_INVALID');}
 if(!/^attachment;/i.test(disposition)||!filename||decodedName!==metadata.name||!/^\d{1,8}$/.test(length??'')||Number(length)!==metadata.bytes||response.headers.get('Content-Type')!==metadata.mediaType||response.headers.get('X-XNBY-Material-SHA256')!==metadata.sha256||!sha.test(identity??''))throw failure('DATA_INVALID');
 const chunks=[];let total=0;
 if(response.body?.getReader){const reader=response.body.getReader();try{for(;;){wanted();const {value,done}=await reader.read();wanted();if(done)break;if(!(value instanceof Uint8Array))throw failure('DATA_INVALID');total+=value.byteLength;if(total>metadata.bytes)throw failure('DATA_INVALID');chunks.push(value);}}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}}
 else{const raw=new Uint8Array(await response.arrayBuffer());wanted();total=raw.length;if(total>metadata.bytes)throw failure('DATA_INVALID');chunks.push(raw);}
 if(total!==metadata.bytes)throw failure('DATA_INVALID');const data=new Uint8Array(total);let offset=0;for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.length;}
 if(await digest(data)!==metadata.sha256)throw failure('DATA_INVALID');wanted();return {data,name:metadata.name,mediaType:metadata.mediaType,sha256:metadata.sha256,authorizationVersion:identity};
}
