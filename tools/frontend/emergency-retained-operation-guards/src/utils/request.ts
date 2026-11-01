/**
 * axios实例
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { unref } from "vue";
import type { Action } from "element-plus";
import { ElMessageBox, ElMessage } from "element-plus/es";
import { API_BASE_URL, LAYOUT_PATH } from "@/config/setting";
import type { ApiResult } from "@/api";
import router from "@/router";
import { getToken /*setToken*/ } from "./token-util";
import { logout, toURLSearch } from "./common";
import { useUserStore } from "@/store/modules/user";

const config = {
  baseURL: API_BASE_URL
};

class RequestHttp {
  service: AxiosInstance;
  public constructor(config: AxiosRequestConfig) {
    // instantiation
    this.service = axios.create(config);

    /**
     * @description 请求拦截器
     * 客户端发送请求 -> [请求拦截器] -> 服务器
     * token校验(JWT) : 接受服务器返回的 token,存储到 vuex/pinia/本地储存当中
     */
    this.service.interceptors.request.use(
      config => {
        // 添加token到header
        const token = getToken();
        if (token && config.headers) {
          config.headers["Authorization"] = token;
        }
        // get请求处理数组和对象类型参数
        if (config.method === "get" && config.params) {
          config.url = toURLSearch(config.params, config.url);
          config.params = {};
        }
        return config;
      },
      error => {
        return Promise.reject(error);
      }
    );

    /**
     * @description 响应拦截器
     *  服务器换返回信息 -> [拦截统一处理] -> 客户端JS获取到信息
     */
    this.service.interceptors.response.use(
      (res: AxiosResponse) => {
        // 登录过期处理
        if (res.data?.code === 600) {
          const userStore = useUserStore();
          const { path, fullPath } = unref(router.currentRoute);
          if (path == LAYOUT_PATH) {
            logout(true, void 0, router.push);
            userStore.$reset();
          } else if (path !== "/login") {
            ElMessageBox.close();
            ElMessageBox.alert("登录状态已过期, 请退出重新登录!", "系统提示", {
              confirmButtonText: "重新登录",
              callback: (action: Action) => {
                if (action === "confirm") {
                  logout(false, fullPath);
                  userStore.$reset();
                }
              },
              type: "warning",
              draggable: true
            });
          }
          return Promise.reject(new Error(res.data.msg));
        }

        if (res.data.code === 400 || (res.config?.url?.startsWith("/serv/") && Number.isInteger(res.data.code) && res.data.code >= 100000 && res.data.code <= 2147483647)) {
          const msg = res.data.message || res.data.msg;
          msg && ElMessage.error(msg);
          return Promise.reject(res);
        }

        // 成功请求（在页面上除非特殊情况，否则不用处理失败逻辑）
        return res.data;
      },
      error => {
        const msg = error?.response?.data?.message || error?.response?.data?.msg || error?.message;
        if (!axios.isCancel(error) && typeof msg === "string" && msg) ElMessage.error(msg);
        return Promise.reject(error);
      }
    );
  }
  /**
   * @description 常用请求方法封装
   */
  get<T>(url: string, params?: object, _object = {}): Promise<ApiResult<T>> {
    return this.service.get(url, { params, ..._object });
  }
  post<T>(url: string, params?: object | string, _object = {}): Promise<ApiResult<T>> {
    return this.service.post(url, params, _object);
  }
  put<T>(url: string, params?: object, _object = {}): Promise<ApiResult<T>> {
    return this.service.put(url, params, _object);
  }
  delete<T>(url: string, params?: any, _object = {}): Promise<ApiResult<T>> {
    return this.service.delete(url, { params, ..._object });
  }
  download(url: string, params?: object, _object = {}): Promise<BlobPart> {
    return this.service.get(url, { params, ..._object, responseType: "blob" });
  }
}

export default new RequestHttp(config);
