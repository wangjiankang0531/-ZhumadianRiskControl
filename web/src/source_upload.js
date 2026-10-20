import {Scene} from 'three';

// Upload every mesh once, then restore the caller's culling policy even if GPU
// submission fails. Source staging must remain detached from the live scene.
export function uploadSourceScene({scene,renderer,camera,target}){
 if(!scene||scene.parent)throw Error('Source upload requires a detached scene');
 const uploadScene=new Scene(),priorTarget=renderer.getRenderTarget(),saved=[];
 try{
  scene.traverse(node=>{if(node.isMesh){saved.push([node,node.frustumCulled]);node.frustumCulled=false;}});
  uploadScene.add(scene);renderer.setRenderTarget(target);renderer.render(uploadScene,camera);
 }finally{
  uploadScene.remove(scene);for(const [node,culled] of saved)node.frustumCulled=culled;
  renderer.setRenderTarget(priorTarget);
 }
}
