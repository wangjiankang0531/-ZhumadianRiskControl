export function denseAuditLayout(width,height){
 if(![width,height].every(Number.isSafeInteger)||width<1||height<1||width>4096||height>2160)throw Error('Dense audit viewport exceeds bound');
 const tiles=[];for(let y=0;y<height;y+=64)for(let x=0;x<width;x+=96)tiles.push({x,y,width:Math.min(96,width-x),height:Math.min(64,height-y)});
 return {width,height,pixels:width*height,tiles,targetBytes:96*64*8};
}
// Translate the original physical viewport, rather than changing projection.
// Bottom-left framebuffer coordinates and top-left report coordinates differ.
export function denseTileViewport(tile,bufferHeight,viewport){return {x:viewport[0]-tile.x,y:viewport[1]-(bufferHeight-tile.y-tile.height),width:viewport[2],height:viewport[3]};}
export function denseSamplePixel(tile,x,y,width){
 if(!Number.isFinite(x)||!Number.isFinite(y)||Math.abs(x)>1||Math.abs(y)>1)throw Error('Invalid dense sample');
 const px=tile.x+Math.min(tile.width-1,Math.floor((x+1)*tile.width/2)),py=tile.y+tile.height-1-Math.min(tile.height-1,Math.floor((y+1)*tile.height/2));return {x:px,y:py,index:py*width+px};
}
export function denseCellIndex(x,y,width,height){return Math.min(2,Math.floor((y+.5)*3/height))*3+Math.min(2,Math.floor((x+.5)*3/width));}
export function projectedSourceQuality(node,depth,scale){
 const geometry=Number.isFinite(node?.longest_edge_p90_m)&&node.longest_edge_p90_m>=0?node.longest_edge_p90_m*scale/depth:null,texel=Number.isFinite(node?.texel_world_p90_m)&&node.texel_world_p90_m>0?node.texel_world_p90_m*scale/depth:null;
 return {geometry,texel,unknown:geometry===null||texel===null,over:geometry!==null&&geometry>6||texel!==null&&texel>1.5};
}
