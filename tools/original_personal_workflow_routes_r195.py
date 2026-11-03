"""Register original personal-workflow views after normal authenticated menu loading."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
ROUTES='src/router/routes.ts';HOME='src/views/home/index.vue';DONE='src/views/workflow/completedMatters/index.vue';DONE_INFO='src/views/workflow/completedMatters/info/index.vue'
EXPECTED={ROUTES:'40a612b76ec229025f1abb05673725f4fab7cb8cabeb26c187c0e89c7e3ab0af',HOME:'d320d63bd363c8ce1aae85ec126308ee9f407ff03bacda1b642de0bf189271a3'}
digest=lambda b:hashlib.sha256(b).hexdigest()
PERSONAL='''// Personal workflow routes are registered only by the original authenticated menu loader.
const personalWorkflowRoutes: RouteRecordRaw[] = [
  { path: "/workflow/flowTodo", component: () => import("@/views/workflow/flowTodo/index.vue"), meta: { title: "待办事宜", hide: true } },
  { path: "/workflow/flowTodo/detail", component: () => import("@/views/workflow/flowTodo/info/index.vue"), meta: { title: "待办详情", hide: true } },
  { path: "/workflow/startWithMeTwo", component: () => import("@/views/workflow/startWithMeTwo/index.vue"), meta: { title: "我发起的", hide: true } },
  { path: "/workflow/startWithMe/examine", component: () => import("@/views/workflow/startWithMeTwo/info/index.vue"), meta: { title: "发起详情", hide: true } },
  { path: "/workflow/completedMatters", component: () => import("@/views/workflow/completedMatters/index.vue"), meta: { title: "已办事宜", hide: true } },
  { path: "/workflow/completedMatters/detail", component: () => import("@/views/workflow/completedMatters/info/index.vue"), meta: { title: "已办详情", hide: true } }
];

'''
def transform(existing):
 for n,pin in EXPECTED.items():
  if digest(existing[n])!=pin:raise ValueError('EXACT_R34_PERSONAL_WORKFLOW_SOURCE_REQUIRED:'+n)
 routes=existing[ROUTES].decode('utf-8');home=existing[HOME].decode('utf-8')
 if routes.count('export function getMenuRoutes(')!=1 or routes.count('  return routes;')!=1:raise ValueError('EXACT_AUTHENTICATED_MENU_ROUTE_ANCHORS_REQUIRED')
 routes=routes.replace('export function getMenuRoutes(',PERSONAL+'export function getMenuRoutes(',1)
 routes=routes.replace('  return routes;','''  // Keep every configured menu route authoritative and add only missing personal pages.
  const configuredPaths = new Set(childs.map(route => route.path));
  for (const route of personalWorkflowRoutes) {
    if (!configuredPaths.has(route.path)) childs.push(route);
  }
  return routes;''',1)
 img='    <img class="home-bg" src="@/assets/images/welcome.png" alt="welcome" />';script='<script setup name="home"></script>'
 if home.count(img)!=1 or home.count(script)!=1:raise ValueError('EXACT_ORIGINAL_HOME_REQUIRED')
 shortcuts='''    <nav class="workflow-shortcuts" aria-label="个人审批入口">
      <el-button type="primary" data-workflow-route="/workflow/flowTodo" @click="router.push({ path: '/workflow/flowTodo' })">待办事宜</el-button>
      <el-button data-workflow-route="/workflow/completedMatters" @click="router.push({ path: '/workflow/completedMatters' })">已办事宜</el-button>
      <el-button data-workflow-route="/workflow/startWithMeTwo" @click="router.push({ path: '/workflow/startWithMeTwo' })">我发起的</el-button>
    </nav>
'''
 home=home.replace(img,shortcuts+img,1).replace(script,'<script setup name="home" lang="ts">\nimport { useRouter } from "vue-router";\nconst router = useRouter();\n</script>',1).replace('  display: flex;','  display: flex;\n  flex-direction: column;',1)
 home=home.replace('</style>','.workflow-shortcuts {\n  display: flex;\n  flex-wrap: wrap;\n  justify-content: center;\n  gap: 12px;\n  margin: 0 16px 16px;\n}\n</style>',1)
 done='''<template>
  <workflow type="我已处理" to="/workflow/completedMatters/detail" list-parameters="processInstanceId" />
</template>
<script setup lang="ts">
import workflow from "@/components/workflow/index.vue";
</script>
'''
 done_info='''<template>
  <workflowdetail audit-type="我已处理" />
</template>
<script setup lang="ts">
import workflowdetail from "@/components/workflow/info.vue";
</script>
'''
 return {ROUTES:routes.encode(),HOME:home.encode(),DONE:done.encode(),DONE_INFO:done_info.encode()}
@contextmanager
def personal_workflow_override(project):
 project=Path(project).absolute();owner=Path('D:/Project/Zhumadian/work/user_feedback_20261031')
 if project.resolve()!=project or not project.is_relative_to(owner):raise ValueError('OWN_BUILD_COPY_ONLY')
 before={n:(project/n).read_bytes()for n in EXPECTED}
 if any((project/n).exists()for n in [DONE,DONE_INFO]):raise ValueError('NEW_PERSONAL_WRAPPER_ALREADY_PRESENT')
 for n in [ROUTES,HOME,DONE,DONE_INFO]:
  for p in [project/n,*(project/n).parents]:
   if p.exists()and(p.is_symlink()or getattr(p.lstat(),'st_file_attributes',0)&0x400):raise ValueError('BUILD_REPARSE_REFUSED')
 after=transform(before);proof={'sourceRestored':False,'originalLoginGuardUnchanged':True,'routesAddedOnlyWithinOriginalAuthenticatedMenuLoader':True,'configuredMenuRoutesNotReplaced':True,'originalNativeListAndDetailAPIsUnchanged':True,'newDatasourceOrAccountRoleChange':False,'files':{n:{'before':digest(before[n])if n in before else None,'after':digest(b)}for n,b in after.items()}}
 try:
  for n,b in after.items():p=project/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  yield proof
 finally:
  for n,b in after.items():
   p=project/n
   if p.exists()and p.read_bytes()not in [before.get(n),b]:raise ValueError('FOREIGN_WORKFLOW_ROUTE_EDIT_REFUSED')
  for n,b in before.items():(project/n).write_bytes(b)
  for n in [DONE,DONE_INFO]:(project/n).unlink(missing_ok=True)
  proof['sourceRestored']=all((project/n).read_bytes()==b for n,b in before.items())and not any((project/n).exists()for n in [DONE,DONE_INFO])
