export async function clickStableOriginalDownload({evaluate,send,session,save,until}){
 let hit,last=null,stableSince=0;
 await until(async()=>{
  const row=await evaluate('(()=>{const buttons=Array.from(document.querySelectorAll(".el-drawer button")).filter(e=>e.getClientRects().length&&e.textContent.trim()==="下载");if(buttons.length!==1||buttons[0].disabled)return null;const b=buttons[0],r=b.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,top=document.elementFromPoint(x,y);return{x,y,width:r.width,height:r.height,viewWidth:innerWidth,viewHeight:innerHeight,inside:r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,topmost:!!top&&(b===top||b.contains(top)),moving:b.closest(".el-drawer").getAnimations({subtree:true}).some(a=>a.playState==="running"||a.pending)}})()');
  if(row)await save('download-target-observation.private.json',row);
  const okay=row?.inside&&row.topmost&&!row.moving;
  const unchanged=okay&&last&&['x','y','width','height'].every(k=>Math.abs(row[k]-last[k])<0.1);
  if(!unchanged)stableSince=Date.now();last=okay?row:null;
  if(!okay||Date.now()-stableSince<400)return false;hit=row;return true;
 });
 await save('download-click-target.json',{visibleOriginalButton:true,insideViewport:true,topmost:true,positionStableAtLeastMilliseconds:400,noRunningDrawerAnimation:true,actualInputDispatch:true});
 await send('Input.dispatchMouseEvent',{type:'mousePressed',x:hit.x,y:hit.y,button:'left',clickCount:1},session);
 await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:hit.x,y:hit.y,button:'left',clickCount:1},session);
}
