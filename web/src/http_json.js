// Bound each response while streaming, before allocating a complete JSON body.
export async function readJSON(response,maximum){
  const type=response.headers.get('Content-Type')??'';
  if(!/^application\/(?:[a-z0-9.+-]+\+)?json(?:\s*;|$)/i.test(type))throw Error('INVALID_JSON');
  const length=response.headers.get('Content-Length');if(length&&/^\d+$/.test(length)&&Number(length)>maximum)throw Error('RESPONSE_TOO_LARGE');
  if(!response.body)throw Error('INVALID_JSON');
  const reader=response.body.getReader(),chunks=[];let bytes=0;
  try{while(true){const part=await reader.read();if(part.done)break;bytes+=part.value.byteLength;if(bytes>maximum){await reader.cancel();throw Error('RESPONSE_TOO_LARGE');}chunks.push(part.value);}}
  catch(error){try{await reader.cancel();}catch{}throw error;}
  finally{reader.releaseLock();}
  const raw=new Uint8Array(bytes);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.byteLength;}
  return {document:JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)),bytes};
}
