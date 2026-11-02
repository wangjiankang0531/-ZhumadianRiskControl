import {validatePNGIconData,maximumPNGIconDimension} from './png_icon.js';

// A failed icon stays failed until document replacement. It must not start a new
// decoder or show an error on every animation frame.
export class CustomIconCache{
  constructor({createImage=()=>new Image(),onError=()=>{}}={}){this.createImage=createImage;this.onError=onError;this.entries=new Map();this.generation=0;}
  get(key){
    const old=this.entries.get(key);if(old)return old.status==='ready'?old.image:null;
    const record={status:'loading',image:null},generation=this.generation;
    this.entries.set(key,record);
    const current=()=>generation===this.generation&&this.entries.get(key)===record;
    const detach=()=>{if(record.image){record.image.onload=null;record.image.onerror=null;}};
    const failed=error=>{if(!current()||record.status==='failed')return;detach();record.status='failed';record.image=null;this.onError(error);};
    try{
      validatePNGIconData(key);
      const image=this.createImage();record.image=image;
      image.onload=()=>{
        if(!current())return;
        if(!image.naturalWidth||!image.naturalHeight||image.naturalWidth>maximumPNGIconDimension||image.naturalHeight>maximumPNGIconDimension){failed(Error('自定义图标尺寸不能超过 2048×2048'));return;}
        detach();record.status='ready';
      };
      image.onerror=()=>failed(Error('自定义 PNG 图标无法解码'));
      image.src=key;
    }catch(error){failed(error);}
    return record.status==='ready'?record.image:null;
  }
  clear(){
    this.generation++;
    for(const record of this.entries.values())if(record.image){record.image.onload=null;record.image.onerror=null;}
    this.entries.clear();
  }
}
