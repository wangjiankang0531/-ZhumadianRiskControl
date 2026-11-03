import type { RouteRecordRaw } from "vue-router";
import { menuToRoutes, eachTree } from "ele-admin-plus/es";
import type { MenuItem } from "ele-admin-plus/es/ele-pro-layout/types";
import { HOME_PATH, LAYOUT_PATH, REDIRECT_PATH } from "@/config/setting";
import Layout from "@/layout/index.vue";
import RedirectLayout from "@/components/RedirectLayout/index.vue";
const modules = import.meta.glob("/src/views/**/index.vue");

/**
 * 静态路由
 */
export const routes = [
  {
    path: "/home",
    redirect: to => ({ path: "/home/index", query: to.query, hash: to.hash })
  },
  {
    path: "/login",
    component: () => import("@/views/login/index.vue"),
    meta: { title: "登录" }
  },
  // 404
  {
    path: "/:path(.*)*",
    component: () => import("@/views/exception/404/index.vue")
  }
];

/**
 * 根据菜单生成动态路由
 * @param menus 菜单数据
 * @param homePath 主页地址
 */
// Personal workflow routes are registered only by the original authenticated menu loader.
const personalWorkflowRoutes: RouteRecordRaw[] = [
  { path: "/workflow/flowTodo", component: () => import("@/views/workflow/flowTodo/index.vue"), meta: { title: "待办事宜", hide: true } },
  { path: "/workflow/flowTodo/detail", component: () => import("@/views/workflow/flowTodo/info/index.vue"), meta: { title: "待办详情", hide: true } },
  { path: "/workflow/startWithMeTwo", component: () => import("@/views/workflow/startWithMeTwo/index.vue"), meta: { title: "我发起的", hide: true } },
  { path: "/workflow/startWithMe/examine", component: () => import("@/views/workflow/startWithMeTwo/info/index.vue"), meta: { title: "发起详情", hide: true } },
  { path: "/workflow/completedMatters", component: () => import("@/views/workflow/completedMatters/index.vue"), meta: { title: "已办事宜", hide: true } },
  { path: "/workflow/completedMatters/detail", component: () => import("@/views/workflow/completedMatters/info/index.vue"), meta: { title: "已办详情", hide: true } }
];

export function getMenuRoutes(menus?: MenuItem[], homePath?: string) {
  const childs: RouteRecordRaw[] = [
    // 用于刷新的路由
    {
      path: REDIRECT_PATH + "/:path(.*)",
      component: RedirectLayout,
      meta: { hideFooter: true }
    }
  ];
  const routes: RouteRecordRaw[] = [
    {
      path: LAYOUT_PATH,
      component: Layout,
      redirect: HOME_PATH ?? homePath,
      children: childs
    }
  ];
  // 路由铺平处理
  eachTree(menuToRoutes(menus, getComponent), route => {
    const temp = Object.assign({}, route, { children: void 0 });
    if (route.meta?.layout === false) {
      routes.push(temp); // 不需要外层布局的路由
    } else {
      childs.push(temp); // 需要外层布局的路由
    }
  });
  // Keep every configured menu route authoritative and add only missing personal pages.
  const configuredPaths = new Set(childs.map(route => route.path));
  for (const route of personalWorkflowRoutes) {
    if (!configuredPaths.has(route.path)) childs.push(route);
  }
  return routes;
}

/**
 * 解析路由组件
 * @param component 组件名称
 */
function getComponent(component?: string) {
  if (component) {
    const module = modules[`/src/views${component}.vue`];
    if (!module) {
      return modules[`/src/views${component}/index.vue`];
    }
    return module;
  }
}
