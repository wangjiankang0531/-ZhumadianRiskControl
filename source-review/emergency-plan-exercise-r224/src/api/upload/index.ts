import request from "@/utils/request";
// 附件上传
export const uploadFile = (params, signal?: AbortSignal) => {
  return request.post<{ url: string }>(`/serv/sys-file/upload`, params, { signal });
};
