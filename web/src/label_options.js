// Optional DLG presentation fields. Geometry and its original elevation are never changed.
export function labelOptions(label) {
  const placement=Object.hasOwn(label,'placement')?label.placement:'screen';
  if(!['screen','billboard'].includes(placement))throw Error('不支持的标牌显示方式');
  const heightM=Object.hasOwn(label,'heightM')?label.heightM:60;
  if(!Number.isFinite(heightM)||heightM<0||heightM>500)throw Error('立体标牌高度须为0到500米');
  return {placement,heightM};
}
