import { ElMessageBox, ElMessage } from "element-plus";
import { HandleData } from "./interface";

/**
 * @description 操作单条数据信息 (二次确认【删除、禁用、启用、重置密码】)
 * @param {Function} api 操作数据接口的api方法 (必传)
 * @param {Object} params 携带的操作数据参数 {id,params} (必传)
 * @param {String} message 提示信息 (必传)
 * @param {String} confirmType icon类型 (不必传,默认为 warning)
 * @returns {Promise}
 */
export const useHandleData = async (
  api: (params: any) => Promise<any>,
  params: any = {},
  message: string,
  confirmType: HandleData.MessageType = "warning"
): Promise<boolean> => {
  try {
    await ElMessageBox.confirm(`是否${message}?`, "温馨提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: confirmType,
      draggable: true
    });
  } catch {
    return false;
  }
  let response: any;
  try {
    response = await api(params);
  } catch {
    return false;
  }
  const succeeded = response === true || (
    response !== null && typeof response === "object" &&
    (response.code === 0 || response.code === 200) && response.data !== false
  );
  if (!succeeded) {
    ElMessage({ type: "error", message: `${message}未完成，请核对记录状态后重试。` });
    return false;
  }
  ElMessage({ type: "success", message: `${message}成功!` });
  return true;
};
