import {validateBusiness} from './business_binding.js';

const own = (value, key) => Object.hasOwn(value, key);
function object(value, allowed, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).some(key => !allowed.includes(key))) {
    throw Error(`${name}格式或字段无效`);
  }
}
function text(value, maximum, name, required = true) {
  if (typeof value !== 'string' || (required && !value.trim()) || new TextEncoder().encode(value).length > maximum || /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u.test(value)) {
    throw Error(`${name}为空、包含控制字符或超出长度限制`);
  }
}
function utc(value, name) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/u.test(value)) throw Error(`${name}须为 UTC 时间`);
  const time = Date.parse(value);
  const canonical = value.includes('.') ? value : value.replace('Z', '.000Z');
  if (!Number.isFinite(time) || new Date(time).toISOString() !== canonical) throw Error(`${name}日期无效`);
  return time;
}

// JSON tuple encoding prevents collisions when IDs contain punctuation.
export function businessRecordKey(binding) {
  return JSON.stringify([binding.sourceSystem, binding.objectType, binding.businessId]);
}

export function parseBusinessRecords(document, filename = '') {
  object(document, ['schema', 'scene', 'exportedAt', 'ttlHours', 'records'], '业务台账');
  if (document.schema !== 'xnby.business.records.v1' || document.scene !== 'zhumadian') throw Error('业务台账格式或场景不匹配');
  utc(document.exportedAt, '台账导出时间');
  if (!Number.isInteger(document.ttlHours) || document.ttlHours < 1 || document.ttlHours > 8760) throw Error('台账有效时长须为 1–8760 小时');
  if (!Array.isArray(document.records) || document.records.length > 10000) throw Error('业务台账最多支持 10000 条记录');
  const copy = structuredClone(document), byKey = new Map();
  for (const record of copy.records) {
    object(record, ['sourceSystem', 'objectType', 'businessId', 'enterpriseId', 'name', 'updatedAt', 'attributes'], '业务记录');
    const binding = {sourceSystem: record.sourceSystem, objectType: record.objectType, businessId: record.businessId};
    if (own(record, 'enterpriseId')) binding.enterpriseId = record.enterpriseId;
    validateBusiness(binding);text(record.name, 256, '记录名称');utc(record.updatedAt, '记录更新时间');
    if (!Array.isArray(record.attributes) || record.attributes.length > 32) throw Error('每条记录最多支持 32 项属性');
    const labels = new Set();
    for (const attribute of record.attributes) {
      object(attribute, ['label', 'value'], '业务属性');text(attribute.label, 96, '属性名称');
      if (labels.has(attribute.label)) throw Error('业务属性名称重复');labels.add(attribute.label);
      const v = attribute.value;
      if (typeof v === 'string') text(v, 4096, '属性值', false);
      else if (v !== null && typeof v !== 'boolean' && (typeof v !== 'number' || !Number.isFinite(v))) throw Error('属性值须为文本、有限数值、布尔或空值');
    }
    const key = businessRecordKey(record);
    if (byKey.has(key)) throw Error('来源系统、对象类别和业务编号组合重复');
    byKey.set(key, record);
  }
  return {document: copy, byKey, filename};
}

export function resolveBusinessRecord(binding, catalog, now = Date.now()) {
  if (!binding) return {state: 'unbound', text: '未挂接'};
  if (!catalog) return {state: 'unloaded', text: '仅登记关联，尚未加载业务台账'};
  const record = catalog.byKey.get(businessRecordKey(binding));
  if (!record) return {state: 'missing', text: '台账中未找到该编号'};
  if (binding.enterpriseId && record.enterpriseId && binding.enterpriseId !== record.enterpriseId) {
    return {state: 'enterprise-mismatch', text: '企业编号不一致，请核对'};
  }
  const exportTime = Date.parse(catalog.document.exportedAt), updateTime = Date.parse(record.updatedAt);
  if (exportTime > now + 300000 || updateTime > now + 300000) return {state: 'future', text: '台账时间异常，请核对'};
  const stale = Math.max(now - exportTime, now - updateTime) > catalog.document.ttlHours * 3600000;
  return {state: stale ? 'stale' : 'ready', text: stale ? '文件台账已过时，请核对' : '文件台账（非实时）', record};
}

export function businessRecordRows(binding, catalog, now) {
  const result = resolveBusinessRecord(binding, catalog, now);
  const rows = [['业务数据状态', result.text]];
  if (catalog && binding) rows.push(['台账文件', catalog.filename], ['台账导出时间', catalog.document.exportedAt]);
  if (result.record) {
    rows.push(['业务记录名称', result.record.name], ['记录更新时间', result.record.updatedAt]);
    for (const attribute of result.record.attributes) {
      const v = attribute.value;
      rows.push([attribute.label, v === null ? '未提供' : typeof v === 'boolean' ? (v ? '是' : '否') : String(v)]);
    }
  }
  return rows;
}

export function businessRecordSearchText(binding, catalog) {
  const result = resolveBusinessRecord(binding, catalog);
  return result.record ? result.record.name : '';
}

export function businessCoverage(layers, catalog, now = Date.now()) {
  let bound = 0, matched = 0, missing = 0, conflicts = 0;
  for (const layer of layers ?? []) for (const feature of layer.features) {
    if (!feature.business) continue;
    bound++;
    const result = resolveBusinessRecord(feature.business, catalog, now);
    if (result.record) matched++;
    else if (result.state === 'missing') missing++;
    else if (result.state !== 'unloaded') conflicts++;
  }
  return {bound, matched, missing, conflicts};
}
