import spatialTypes from '../../shared/spatial_types.json' with {type:'json'};
export const objectTypeNames = Object.fromEntries(Object.entries(spatialTypes.categories).filter(([,item])=>item.businessReference).map(([key,item])=>[key,item.name]));

// References only: live business records remain owned by their source system.
export function validateBusiness(binding) {
  if (!binding || typeof binding !== 'object' || Array.isArray(binding)) throw Error('业务关联须为对象');
  const fields = ['objectType', 'businessId', 'enterpriseId', 'sourceSystem'];
  if (Object.keys(binding).some(key => !fields.includes(key))) throw Error('业务关联包含不支持的字段');
  if (!Object.hasOwn(objectTypeNames, binding.objectType)) throw Error('空间对象类别无效');
  for (const [key, maximum, required] of [['businessId', 256, true], ['enterpriseId', 256, false], ['sourceSystem', 128, true]]) {
    const value = binding[key];
    if (value === undefined && !required) continue;
    if (typeof value !== 'string' || (required && !value) || new TextEncoder().encode(value).length > maximum || /[\x00-\x20\x7f]/u.test(value)) {
      throw Error('业务编号、企业编号和来源系统须在长度限制内，且不含空白或控制字符');
    }
  }
  return binding;
}

export function businessSearchText(feature) {
  const b = feature.business;
  return b ? [objectTypeNames[b.objectType], b.businessId, b.enterpriseId, b.sourceSystem].filter(Boolean).join(' ') : '';
}

export function businessDetailRows(feature) {
  const b = feature.business;
  return b ? [['业务数据状态', '仅登记关联，业务数据未接入'], ['空间对象编号', feature.id], ['对象类别', objectTypeNames[b.objectType]],
    ['业务编号', b.businessId], ['所属企业编号', b.enterpriseId || '未指定'],
    ['来源系统', b.sourceSystem]]
    : [['空间对象编号', feature.id], ['业务关联', '未挂接']];
}
