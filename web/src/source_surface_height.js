// Presentation-only height on the currently visible source cut.
// Coordinates in the user's DLG stay unchanged. No camera-dependent projection is used.
export function sourceSurfaceHeight(frontiers,x,y){
 let highest=null;
 for(const frontier of frontiers){
  const nodes=frontier.nodes;
  for(const name of frontier.visible){
   const {node,bundle}=nodes.get(name),low=node.bounds_min,high=node.bounds_max;
   if(!low||!high||x<low[0]-1e-7||x>high[0]+1e-7||y<low[1]-1e-7||y>high[1]+1e-7)continue;
   for(const span of node.spans){
    const mesh=bundle.meshes.get(span.part);
    if(!mesh||mesh.visible===false)continue;
    const p=mesh.geometry.attributes.position.array,index=mesh.geometry.index.array;
    for(let at=span.first;at<span.first+span.count;at+=3){
     const a=index[at]*3,b=index[at+1]*3,c=index[at+2]*3;
     const ax=p[a],ay=p[a+1],bx=p[b],by=p[b+1],cx=p[c],cy=p[c+1];
     const determinant=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);
     if(Math.abs(determinant)<1e-12)continue;
     const u=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/determinant,v=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/determinant,w=1-u-v;
     if(u>=-1e-7&&v>=-1e-7&&w>=-1e-7){const z=u*p[a+2]+v*p[b+2]+w*p[c+2];if(Number.isFinite(z)&&(highest===null||z>highest))highest=z;}
    }
   }
  }
 }
 return highest;
}

