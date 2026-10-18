// URLs are derived from pinned hashes, never supplied by an external descriptor.
const SHA=/^[0-9a-f]{64}$/;
export class PreparedTextureIndex{
 constructor(value,base,fetcher=fetch){
  if(value?.schema!=='xnby.prepared_texture_index.v1'||!Array.isArray(value.entries)||value.entries.length>4096)throw Error('Invalid prepared texture index');
  this.base=new URL('./',base).href;this.fetcher=(...args)=>fetcher(...args);this.entries=new Map();
  for(const row of value.entries){if(!SHA.test(row.sourceSHA256)||!SHA.test(row.payloadSHA256)||this.entries.has(row.sourceSHA256))throw Error('Invalid prepared texture entry');this.entries.set(row.sourceSHA256,row.payloadSHA256);}
 }
 has(part){return this.entries.has(part.files?.find(f=>f.name==='atlas.jpg')?.sha256);}
 // A rejected prepared payload stays on its verified JPEG fallback this session.
 reject(part){const source=part?.files?.find(f=>f.name==='atlas.jpg')?.sha256;if(!SHA.test(source))throw Error('Invalid rejected photograph identity');return this.entries.delete(source);}
 url(part,name){const source=part.files?.find(f=>f.name==='atlas.jpg')?.sha256,payload=this.entries.get(source);if(!payload||!['manifest.json','texture.bc7'].includes(name))throw Error('Prepared source texture is not indexed');return new URL(`prepared-textures/${source}/${payload}/${name}`,this.base).href;}
 async manifest(part){const response=await this.fetcher(this.url(part,'manifest.json'),{cache:'no-store'});if(!response.ok)throw Error('Prepared descriptor HTTP '+response.status);const value=await response.json();if(value.sourceSHA256!==part.files.find(f=>f.name==='atlas.jpg').sha256||value.payloadSHA256!==this.entries.get(value.sourceSHA256))throw Error('Prepared descriptor differs from index');return value;}
 async payload(part){const response=await this.fetcher(this.url(part,'texture.bc7'),{cache:'no-store'});if(!response.ok)throw Error('Prepared texture HTTP '+response.status);return response.arrayBuffer();}
}
