// Counts are derived from registered enterprise references, never invented from map geometry.
export function commandEnterpriseStats(layers=[]){
 const seen=new Set(),groups=new Map();let count=0;
 for(const layer of layers)for(const feature of layer.features??[]){const b=feature.business;if(b?.objectType!=='enterprise')continue;
 const key=JSON.stringify([b.sourceSystem,b.businessId]);if(seen.has(key))continue;seen.add(key);count++;
 const name=layer.name.replace(/[（(].*$/u,'').trim()||'未分类企业';groups.set(name,(groups.get(name)??0)+1);}
 return {count,groups:[...groups].map(([name,count])=>({name,count}))};
}
export function updateCommandDashboard(doc,root=document){
 const stats=commandEnterpriseStats(doc?.layers),total=root.getElementById('command-enterprises');if(!total)return;
 total.textContent=doc?stats.count:'—';const groups=root.getElementById('command-groups');groups.replaceChildren();
 const colors=['#55dce8','#69aaf8','#edc570','#8bd9bd'];
 stats.groups.forEach((group,i)=>{const row=root.createElement('div');row.className='command-bar';row.style.setProperty('--bar-color',colors[i%4]);
 const name=root.createElement('span');name.textContent=group.name;const amount=root.createElement('b');amount.textContent=group.count;
 const track=root.createElement('i');track.style.setProperty('--bar-width',`${stats.count?group.count/stats.count*100:0}%`);row.append(name,amount,track);groups.append(row);});
 if(!stats.count){const empty=root.createElement('p');empty.className='command-empty';empty.textContent='当前图层尚无企业登记';groups.append(empty);}
 const resources=[...root.querySelectorAll('.crystal-resource-grid strong')].map(n=>Number(n.textContent)).filter(Number.isFinite);root.getElementById('command-resources').textContent=resources.reduce((a,b)=>a+b,0);
}
