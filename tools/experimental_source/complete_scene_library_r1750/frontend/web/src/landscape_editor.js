import {validateSourceConfiguration} from './business_source_configuration.js';
import {planLandscapeImport} from './landscape_import.js';
import {mergeCloudFeatures} from './cloud_feature_merge.js';
import {prepareLandscapeDocument,validateLandscapeDocument} from './landscape_document.js';

const clone=value=>structuredClone(value);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fields=(patch,allowed)=>{if(!patch||Array.isArray(patch)||typeof patch!=='object'||Object.keys(patch).some(k=>!allowed.includes(k)))throw Error('不支持的编辑字段');return clone(patch);};
const index=(value,size,insert=false)=>{if(!Number.isInteger(value)||value<0||value>size-(insert?0:1))throw Error('顶点序号无效');return value;};
const point=value=>{if(!Array.isArray(value)||value.length!==3||value.some(n=>!Number.isFinite(n)||Math.abs(n)>100000))throw Error('坐标须为有效的东/北/高程三元组');return [...value];};
const defaultLabel=name=>({visible:true,text:name,fontPx:16,color:'#FFFFFF',opacity:1,offset:[12,-16],placement:'billboard',heightM:12});

// Own the document: UI previews, undo and asynchronous save acknowledgements cannot
// mutate a caller's document or overwrite a newer edit. Network/CAS lives outside.
export class LandscapeEditor {
  #doc;#saved;#past=[];#future=[];#gesture=null;#generation=0;#limit;#bytes;#saves=new WeakMap();#ackGeneration=-1;
  constructor(document,{historyLimit=64,historyBytes=32*1024*1024}={}){
    if(!Number.isInteger(historyLimit)||historyLimit<1||historyLimit>256||!Number.isInteger(historyBytes)||historyBytes<1024||historyBytes>256*1024*1024)throw Error('撤销容量无效');
    this.#doc=prepareLandscapeDocument(document);this.#saved=clone(this.#doc);this.#limit=historyLimit;this.#bytes=historyBytes;
  }
  document(){return clone(this.#doc);}
  get state(){return {generation:this.#generation,dirty:!equal(this.#doc,this.#saved),canUndo:this.#past.length>0&&!this.#gesture,canRedo:this.#future.length>0&&!this.#gesture,dragging:!!this.#gesture};}
  #layer(doc,id,editable=true){const l=doc.layers.find(l=>l.id===id);if(!l)throw Error('图层不存在');if(editable&&l.locked)throw Error('图层已锁定，请先解锁');return l;}
  #feature(doc,layerId,featureId){const l=this.#layer(doc,layerId),f=l.features.find(f=>f.id===featureId);if(!f)throw Error('标注不存在');return f;}
  #trim(){let bytes=0;for(let i=this.#past.length-1;i>=0;i--){bytes+=this.#past[i].bytes;if(this.#past.length-i>this.#limit||bytes>this.#bytes){this.#past.splice(0,i+1);break;}}}
  #entry(doc,label){return {doc,label,bytes:new TextEncoder().encode(JSON.stringify(doc)).length};}
  #remember(before,label){this.#past.push(this.#entry(before,label));this.#future=[];this.#trim();this.#generation++;}
  #apply(label,change){if(this.#gesture)throw Error('请先完成或取消顶点拖动');const next=clone(this.#doc);change(next);validateLandscapeDocument(next);if(equal(next,this.#doc))return false;this.#remember(this.#doc,label);this.#doc=next;return true;}
  importDocument(document,{mode='objects',includeSourceConfiguration=false,expectedGeneration}={}){if(expectedGeneration!==undefined&&expectedGeneration!==this.#generation)throw Object.assign(Error('预览期间工程已更新，请重新选择文件'),{code:'LAYER_IMPORT_STALE'});const plan=planLandscapeImport(this.#doc,document,{mode,includeSourceConfiguration});const changed=this.#apply('导入图层',d=>{d.layers=clone(plan.document.layers);if(includeSourceConfiguration)d.businessSources=clone(plan.document.businessSources);});return {changed,summary:plan.summary};}
  replaceSceneDocument(document,{expectedGeneration}={}){if(expectedGeneration!==undefined&&expectedGeneration!==this.#generation)throw Object.assign(Error('打开期间图层已变化，请重新读取场景'),{code:'LAYER_IMPORT_STALE'});const next=prepareLandscapeDocument(document);return this.#apply('打开完整场景',d=>{for(const key of Object.keys(d))delete d[key];Object.assign(d,clone(next));});}
  setSourceConfiguration(value){const next=value===null?null:validateSourceConfiguration(value);return this.#apply('配置标牌数据接口',d=>{if(next===null)delete d.businessSources;else d.businessSources=clone(next);});}
  createLayer(layer){return this.#apply('新增图层',d=>d.layers.push(clone(layer)));}
  updateLayer(id,patch){const p=fields(patch,['name','visible','locked']);return this.#apply('修改图层',d=>Object.assign(this.#layer(d,id,false),p));}
  deleteLayer(id){return this.#apply('删除图层',d=>{this.#layer(d,id);d.layers=d.layers.filter(l=>l.id!==id);});}
  addFeature(layerId,feature){return this.#apply('新增标注',d=>this.#layer(d,layerId).features.push(clone(feature)));}
  updateFeature(layerId,id,patch){const p=fields(patch,['name','style','label','business']);return this.#apply('修改标注',d=>{const f=this.#feature(d,layerId,id);for(const [key,value]of Object.entries(p)){if(['style','label','business'].includes(key)){if(!value||typeof value!=='object'||Array.isArray(value))throw Error('标注属性须为对象');f[key]={...(key==='label'&&!f.label?defaultLabel(f.name):f[key]),...value};}else f[key]=value;}});}
  setLabelAnchor(layerId,id,anchor){return this.#apply('修改标牌落点',d=>{const f=this.#feature(d,layerId,id);if(!f.label)f.label=defaultLabel(f.name);if(anchor===null)delete f.label.anchor;else f.label.anchor=clone(anchor);});}
  setLabelBindings(layerId,id,bindings){return this.updateFeature(layerId,id,{label:{placement:'billboard',dataBindings:clone(bindings)}});}
  deleteFeature(layerId,id){return this.#apply('删除标注',d=>{this.#feature(d,layerId,id);const l=this.#layer(d,layerId);l.features=l.features.filter(f=>f.id!==id);});}
  moveFeature(layerId,id,targetLayerId){return this.#apply('移动标注到图层',d=>{const f=this.#feature(d,layerId,id),target=this.#layer(d,targetLayerId);if(layerId===targetLayerId)return;const source=this.#layer(d,layerId);source.features=source.features.filter(v=>v.id!==id);target.features.push(f);});}
  setVertex(layerId,id,i,value){return this.#apply('修改顶点',d=>{const f=this.#feature(d,layerId,id);f.positions[index(i,f.positions.length)]=point(value);});}
  insertVertex(layerId,id,i,value){return this.#apply('插入顶点',d=>{const f=this.#feature(d,layerId,id);if(f.type==='point')throw Error('点标注只能有一个顶点');f.positions.splice(index(i,f.positions.length,true),0,point(value));});}
  deleteVertex(layerId,id,i){return this.#apply('删除顶点',d=>{const f=this.#feature(d,layerId,id);if(f.positions.length<=({point:1,line:2,region:3}[f.type]))throw Error('顶点数量已达到最少要求');f.positions.splice(index(i,f.positions.length),1);});}
  beginVertexDrag(layerId,id,i){if(this.#gesture)throw Error('已有顶点正在拖动');const f=this.#feature(this.#doc,layerId,id);index(i,f.positions.length);const token=Symbol('vertex drag');this.#gesture={token,before:this.#doc,layerId,id,i};return token;}
  previewVertexDrag(token,value){const g=this.#gesture;if(!g||g.token!==token)throw Error('顶点拖动已失效');const next=clone(this.#doc);this.#feature(next,g.layerId,g.id).positions[g.i]=point(value);validateLandscapeDocument(next);if(equal(next,this.#doc))return false;this.#doc=next;return true;}
  endVertexDrag(token,{cancel=false}={}){const g=this.#gesture;if(!g||g.token!==token)throw Error('顶点拖动已失效');this.#gesture=null;if(cancel){this.#doc=g.before;return false;}if(equal(g.before,this.#doc))return false;this.#remember(g.before,'拖动顶点');return true;}
  undo(){if(this.#gesture)throw Error('请先完成或取消顶点拖动');const entry=this.#past.pop();if(!entry)return false;this.#future.push(this.#entry(this.#doc,entry.label));this.#doc=entry.doc;this.#generation++;return true;}
  redo(){if(this.#gesture)throw Error('请先完成或取消顶点拖动');const entry=this.#future.pop();if(!entry)return false;this.#past.push(this.#entry(this.#doc,entry.label));this.#doc=entry.doc;this.#trim();this.#generation++;return true;}
  rebaseCloud(base,remote,{resolvedDocument}={}){
    if(this.#gesture)throw Error('请先完成或取消顶点拖动');
    const next=resolvedDocument===undefined?mergeCloudFeatures(base,this.#doc,remote):prepareLandscapeDocument(resolvedDocument);
    let saved=prepareLandscapeDocument(remote);let pruned=0;
    const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
    if(JSON.stringify(canonical(next))===JSON.stringify(canonical(saved)))saved=clone(next);
    // Rebase every retained undo/redo snapshot onto remote changes. A snapshot
    // that conflicts cannot be used to overwrite another editor; drop that
    // snapshot and its older chain, retaining the newer safe portion.
    const rebase=entries=>{const result=[];let reference=next;
      for(let i=entries.length-1;i>=0;i--){let document;
        try{document=mergeCloudFeatures(base,entries[i].doc,remote);}
        catch(error){if(error.code!=='CLOUD_EDIT_CONFLICT')throw error;pruned+=i+1;break;}
        if(!equal(document,reference)){result.unshift(this.#entry(document,entries[i].label));reference=document;}
      }return result;};
    const past=rebase(this.#past),future=rebase(this.#future),changed=!equal(next,this.#doc);
    this.#doc=clone(next);this.#saved=saved;this.#past=past;this.#future=future;this.#saves=new WeakMap();
    if(changed)this.#generation++;this.#ackGeneration=this.#generation;this.#trim();
    return {changed,historyPruned:pruned};
  }
  acknowledgeCloud(document){this.#saved=prepareLandscapeDocument(document);this.#saves=new WeakMap();this.#ackGeneration=this.#generation;}
  captureSave(){if(this.#gesture)throw Error('请先完成或取消顶点拖动');const snapshot={generation:this.#generation,document:this.document()};this.#saves.set(snapshot,{generation:this.#generation,document:this.document()});return snapshot;}
  acknowledgeSave(snapshot){const owned=snapshot&&this.#saves.get(snapshot);if(!owned)throw Error('保存回执无效');if(owned.generation<this.#ackGeneration)return false;this.#saved=clone(owned.document);this.#ackGeneration=owned.generation;return true;}
}

export function newAnnotation({id,name,type,positions,style={},label={}}){
  return {id,name,type,positions:clone(positions),style:{icon:'pin',pattern:'solid',sizePx:24,widthPx:3,color:'#22D3EE',fillColor:'#22D3EE',opacity:1,fillOpacity:.2,...clone(style)},label:{...defaultLabel(name),...clone(label)}};
}