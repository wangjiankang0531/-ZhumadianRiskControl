/** 全局安装 */
import type { App, Plugin } from "vue";
import "element-plus/theme-chalk/src/index.scss";
import "ele-admin-plus/es/style/index.scss";
import "cropperjs/dist/cropper.css";
import "xgplayer/dist/index.min.css";

let target: App | undefined;
let loading: Promise<void> | undefined;

// Share code loading only. User information, permissions and tokens remain uncached here.
export function ensureAuthenticatedComponents(): Promise<void> {
  if (!target) return Promise.reject(new Error("APPLICATION_INSTALLER_NOT_READY"));
  if (!loading) {
    loading = import("./OriginalAuthenticatedInstallerR817").then(({ default: installer }) => {
      target!.use(installer);
    }).catch(error => {
      loading = undefined;
      throw error;
    });
  }
  return loading;
}

const installer: Plugin = {
  install(app: App) {
    target = app;
  }
};

export default installer;
