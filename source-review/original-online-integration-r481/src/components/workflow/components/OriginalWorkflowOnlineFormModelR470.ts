/** Original SDK online-form input schemas. This module never executes stored form scripts or fetches data. */
export type FormData = Record<string, unknown>;
export type OnlineFormField = {
  key: string;
  label: string;
  showLabel: boolean;
  span: number;
  type: "text" | "textarea" | "password";
  value: string | number;
  writable: boolean;
  required: boolean;
  maxlength?: number;
  minlength?: number;
  placeholder: string;
  showWordLimit: boolean;
};
export type OnlineFormView = {
  fields: OnlineFormField[];
  errors: string[];
  labelWidth: number;
  labelPosition: "left" | "right" | "top";
};
const object = (value: unknown): value is Record<string, any> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const binding = (value: unknown): value is string =>
  typeof value === "string" && /^[A-Za-z_][A-Za-z0-9_]{0,127}$/.test(value) &&
  !["__proto__", "prototype", "constructor"].includes(value);
const limit = (value: unknown, maximum: number): number | undefined =>
  Number.isInteger(value) && Number(value) >= 0 && Number(value) <= maximum ? Number(value) : undefined;

export function originalOnlineFormView(
  propertyJson: unknown,
  data: unknown,
  operations: unknown,
  mode: "view" | "edit" = "view"
): OnlineFormView {
  const result: OnlineFormView = { fields: [], errors: [], labelWidth: 100, labelPosition: "right" };
  if (mode !== "view" && mode !== "edit") return { ...result, errors: ["表单显示方式无效"] };
  let schema: unknown = propertyJson;
  if (typeof propertyJson === "string") {
    if (propertyJson.length > 1024 * 1024) return { ...result, errors: ["表单配置过大"] };
    try { schema = JSON.parse(propertyJson); }
    catch { return { ...result, errors: ["表单配置无法读取"] }; }
  }
  if (!object(schema) || !Array.isArray(schema.fields) || schema.fields.length > 256)
    return { ...result, errors: ["表单字段配置无效"] };
  if (!object(data) || !Array.isArray(operations)) return { ...result, errors: ["表单数据或字段权限无效"] };
  result.labelWidth = limit(schema.labelWidth, 1000) ?? 100;
  if (["left", "right", "top"].includes(schema.labelPosition)) result.labelPosition = schema.labelPosition;
  const seen = new Set<string>();
  for (const raw of schema.fields) {
    if (!object(raw) || !object(raw.__config__) || !binding(raw.__vModel__)) {
      result.errors.push("表单字段绑定无效"); continue;
    }
    const config = raw.__config__, key = raw.__vModel__;
    if (seen.has(key)) { result.errors.push("表单存在重复字段"); continue; }
    seen.add(key);
    if (!["input", "comInput"].includes(config.jnpfKey)) {
      result.errors.push("此表单包含尚不支持的字段类型"); continue;
    }
    const matches = operations.filter(item => object(item) && item.id === key);
    if (matches.length > 1) { result.errors.push("表单字段权限重复"); continue; }
    const permission = matches[0];
    if (config.noShow === true || permission?.read === false) continue;
    if (Array.isArray(config.visibility) && config.visibility.length && !config.visibility.includes("pc")) continue;
    const value = Object.hasOwn(data, key) ? data[key] : "";
    if (value !== null && value !== undefined && !["string", "number", "boolean"].includes(typeof value)) {
      result.errors.push("表单字段值类型不匹配"); continue;
    }
    if (typeof value === "number" && !Number.isFinite(value)) { result.errors.push("表单字段值无效"); continue; }
    const span = limit(config.span, 24);
    result.fields.push({
      key,
      label: typeof config.label === "string" ? config.label : "",
      showLabel: config.showLabel !== false,
      span: span && span > 0 ? span : 24,
      type: ["textarea", "password"].includes(raw.type) ? raw.type : "text",
      value: value == null ? "" : typeof value === "boolean" ? String(value) : value as string | number,
      writable: mode === "edit" && permission?.write === true && schema.disabled !== true && raw.disabled !== true && raw.readonly !== true,
      required: permission?.required === true || permission?.required === undefined && config.required === true,
      maxlength: limit(raw.maxlength, 1000000),
      minlength: limit(raw.minlength, 1000000),
      placeholder: typeof raw.placeholder === "string" ? raw.placeholder : "",
      showWordLimit: raw.showWordLimit === true
    });
  }
  // Refuse a partial form instead of silently omitting a field whose schema is unsupported.
  if (result.errors.length) result.fields = [];
  return result;
}

export function updateOriginalOnlineField(data: FormData, field: OnlineFormField, value: unknown): FormData {
  if (!field.writable || !binding(field.key) || !["string", "number"].includes(typeof value) ||
      typeof value === "number" && !Number.isFinite(value)) throw new Error("表单字段不可修改");
  return { ...data, [field.key]: value };
}

export function originalOnlineFieldErrors(fields: OnlineFormField[]): { key: string; message: string }[] {
  return fields.filter(field => field.writable).flatMap(field => {
    const value = String(field.value);
    if (field.required && !value.trim()) return [{ key: field.key, message: "请填写" + field.label }];
    if (field.minlength !== undefined && value.length < field.minlength)
      return [{ key: field.key, message: field.label + "长度不足" }];
    if (field.maxlength !== undefined && value.length > field.maxlength)
      return [{ key: field.key, message: field.label + "长度超出限制" }];
    return [];
  });
}
