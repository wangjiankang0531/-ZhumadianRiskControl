// 可读等价实现；本轮产物来自受限发布文件转换，不宣称由此文件全量构建。
import request from "@/utils/request";
import md5 from "md5";
import { encrypt } from "@/utils/common";
import { setToken } from "@/utils/token-util";
import type { ApiResult } from "@/api";
import type { LoginParam, LoginResult, CaptchaResult } from "./model";

/**
 * 登录
 */
export async function login(data: LoginParam) {
  const params = { ...data };
  params.password = encrypt(md5(data.password));
  const res = await request.post<LoginResult>("/jnpf/oauth/Login", undefined, {
    params,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });

  setToken(res.data?.token, data.remember);
  return "登录成功";
}

/**
 * 获取验证码
 */
export async function getCaptcha() {
  const res = await request.get<ApiResult<CaptchaResult>>("/captcha");
  if (res.data.code === 200 && res.data.data) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
