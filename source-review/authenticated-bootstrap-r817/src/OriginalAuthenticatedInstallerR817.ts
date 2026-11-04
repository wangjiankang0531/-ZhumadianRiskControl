/** Original complete global component registration, deferred until authenticated navigation. */
import type { App, Plugin } from "vue";
import ElementPlus from "element-plus/es";
import EleAdminPlus from "ele-admin-plus/es";

const installer: Plugin = {
  install(app: App) {
    app.use(ElementPlus);
    app.use(EleAdminPlus);
  }
};
export default installer;
