// URLs are derived from pinned hashes, never supplied by a descriptor.
const SHA=/^[0-9a-f]{64}$/;
export class PreparedTextureIndex{
 constructor(value,base,fetcher=fetch){
  if(!['xnby.prepared_texture_index.v1','xnby.prepared_texture_index.v2'].includes(value?.schema)||!Array.isArray(value.entries)||value.entries.length>4096)throw Error('Invalid prepared texture index');
  this.base=new URL('./',base).href;this.fetcher=(...args)=>fetcher(...args);this.entries=new Map();this.formats=new Map();
  for(const row of value.entries){const format=value.schema==='xnby.prepared_texture_index.v1'?'bc7':row.format;if(!SHA.test(row.sourceSHA256)||!SHA.test(row.payloadSHA256)||!['bc7','bc7_rgba_overlap'].includes(format)||this.entries.has(row.sourceSHA256))throw Error('Invalid prepared texture entry');this.entries.set(row.sourceSHA256,row.payloadSHA256);this.formats.set(row.sourceSHA256,format);}
 }
 source(part){return part.files?.find(f=>f.name==='atlas.jpg')?.sha256;}
 has(part){return this.entries.has(this.source(part));}
 get hybridCount(){return [...this.formats.values()].filter(v=>v==='bc7_rgba_overlap').length;}
 rejectHybrids(){for(const [source,format] of this.formats)if(format==='bc7_rgba_overlap'){this.entries.delete(source);this.formats.delete(source);}}
 reject(part){const source=this.source(part);if(!SHA.test(source))throw Error('Invalid rejected photograph identity');this.formats.delete(source);return this.entries.delete(source);}
 url(part,name){const source=this.source(part),payload=this.entries.get(source),hybrid=this.formats.get(source)==='bc7_rgba_overlap';if(!payload||!(hybrid?['manifest.json','prefix.bc7','tail.rgba','overlap.rgba']:['manifest.json','texture.bc7']).includes(name))throw Error('Prepared source texture is not indexed');return new URL(`${hybrid?'prepared-hybrid-textures':'prepared-textures'}/${source}/${payload}/${name}`,this.base).href;}
 async manifest(part){const response=await this.fetcher(this.url(part,'manifest.json'),{cache:'no-store'});if(!response.ok)throw Error('Prepared descriptor HTTP '+response.status);const value=await response.json(),source=this.source(part),hybrid=this.formats.get(source)==='bc7_rgba_overlap';if(value.sourceSHA256!==source||value.payloadSHA256!==this.entries.get(source)||hybrid!==(value.schema==='xnby.prepared_hybrid_scene.v1'))throw Error('Prepared descriptor differs from index');return value;}
 async payload(part){const read=async name=>{const response=await this.fetcher(this.url(part,name),{cache:'no-store'});if(!response.ok)throw Error('Prepared texture HTTP '+response.status);return response.arrayBuffer();};if(this.formats.get(this.source(part))!=='bc7_rgba_overlap')return read('texture.bc7');const [prefix,tail,overlap]=await Promise.all([read('prefix.bc7'),read('tail.rgba'),read('overlap.rgba')]);return {prefix,tail,overlap};}
}
