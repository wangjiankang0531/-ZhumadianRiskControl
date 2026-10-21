import {Texture,Source,Box2,Vector2,WebGLRenderTarget} from 'three';
export function staticTextureRegions(width,height,maxBytes=4*1048576){
 if(![width,height].every(n=>Number.isInteger(n)&&n>0&&n<=8192)||!Number.isInteger(maxBytes)||maxBytes<width*4||maxBytes>4*1048576)throw Error('Invalid static texture upload bounds');
 const rows=Math.floor(maxBytes/(width*4)),regions=[];for(let y=0;y<height;y+=rows)regions.push({y,height:Math.min(rows,height-y),bytes:width*Math.min(rows,height-y)*4});return regions;
}
// Public Source.dataReady allocates all original mip levels without uploading
// the DOM image. Public copyTextureToTexture submits each exact source region.
export async function uploadStaticTexture({texture,renderer,maxChunkBytes=4*1048576,yieldFrame=()=>new Promise(resolve=>requestAnimationFrame(resolve)),stillWanted=()=>true,verify=false,referenceImage=null,clock=()=>performance.now(),onProgress=()=>{}}){
 const image=texture?.image;if(!texture?.isTexture||texture.isCompressedTexture||texture.isDataTexture||texture.isCubeTexture||texture.isRenderTargetTexture||!texture.source.dataReady)throw Error('Unsupported static source texture');
 if(referenceImage&&(referenceImage.width!==image?.width||referenceImage.height!==image?.height))throw Error('Static reference image dimensions differ');
 const width=image?.width,height=image?.height,regions=staticTextureRegions(width,height,maxChunkBytes),originalMipmaps=texture.generateMipmaps,gl=renderer.getContext(),stats={width,height,chunks:0,bytes:0,maxUploadMs:0,allocationMs:0,verifiedPixels:0,differentChannels:0,sourceType:image?.constructor?.name,referenceSourceType:verify?(referenceImage??image)?.constructor?.name:null};let reference=null,target=null;
 const wanted=()=>{if(!stillWanted())throw Error('Static texture upload cancelled');};const checked=()=>{const code=gl.getError();if(code!==gl.NO_ERROR)throw Error('Static texture GL error '+code);};
 try{
  wanted();texture.source.dataReady=false;const start=clock();renderer.initTexture(texture);stats.allocationMs=clock()-start;checked();texture.generateMipmaps=false;await yieldFrame();
  const source=new Texture(image);
  for(let i=0;i<regions.length;i++){wanted();const region=regions[i];texture.generateMipmaps=originalMipmaps&&i===regions.length-1;const box=new Box2(new Vector2(0,region.y),new Vector2(width,region.y+region.height)),begin=clock();renderer.copyTextureToTexture(source,texture,box,new Vector2(0,region.y));stats.maxUploadMs=Math.max(stats.maxUploadMs,clock()-begin);checked();stats.chunks++;stats.bytes+=region.bytes;onProgress({...stats});await yieldFrame();}
  texture.generateMipmaps=originalMipmaps;texture.source.dataReady=true;
  if(verify){
   // A separate Source prevents Three from sharing the destination's GPU store.
   reference=texture.clone();reference.source=new Source(referenceImage??image);reference.needsUpdate=true;renderer.initTexture(reference);checked();
   target=new WebGLRenderTarget(width,regions[0].height,{depthBuffer:false,stencilBuffer:false,colorSpace:texture.colorSpace,format:texture.format,type:texture.type});renderer.initRenderTarget(target);
   for(const region of regions){wanted();const box=new Box2(new Vector2(0,region.y),new Vector2(width,region.y+region.height)),a=new Uint8Array(region.bytes),b=new Uint8Array(region.bytes);
    renderer.copyTextureToTexture(reference,target.texture,box,new Vector2(0,0));renderer.readRenderTargetPixels(target,0,0,width,region.height,a);renderer.copyTextureToTexture(texture,target.texture,box,new Vector2(0,0));renderer.readRenderTargetPixels(target,0,0,width,region.height,b);checked();
    for(let i=0;i<a.length;i++)if(a[i]!==b[i])stats.differentChannels++;stats.verifiedPixels+=width*region.height;onProgress({...stats});await yieldFrame();
   }
   if(stats.differentChannels)throw Error('Static texture pixels differ from monolithic reference');
  }
  wanted();return {...stats};
 }catch(error){texture.dispose();throw error;}
 finally{texture.generateMipmaps=originalMipmaps;texture.source.dataReady=true;reference?.dispose();target?.dispose();}
}
