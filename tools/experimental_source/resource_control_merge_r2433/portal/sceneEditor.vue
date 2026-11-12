<template>
  <section class="scene-editor-page" aria-label="三维图层编辑">
    <div class="scene-editor-status" role="status" :data-state="state.state" :data-code="state.code">
      <span>{{ statusText }}</span>
      <router-link class="scene-mode-link" to="/sceneViewer">返回三维查看</router-link>
      <router-link v-if="state.state !== 'ready' && route.query.topic !== 'resource-management'" class="scene-mode-link" :to="{path:route.path,query:{topic:'resource-management'}}">资源管理</router-link>
      <button v-if="state.state !== 'ready' && state.state !== 'loading'" type="button" @click="connect">重新连接</button>
    </div>
    <iframe ref="scene" title="驻马店三维图层编辑" referrerpolicy="no-referrer" :aria-busy="state.state === 'loading'" />
  </section>
</template>
<script setup name="sceneEditor">
import { computed, onActivated, onDeactivated, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { getToken } from '@/utils/token-util';
import { createProjectSceneHost } from './project_scene_host.js';
defineOptions({name:'sceneEditor'});
const route=useRoute(),router=useRouter();
const scene=ref(null),state=ref({state:'idle'});let owner,ownerGeneration=0,retiringOwner=Promise.resolve();
const messages={CLOUD_LOGIN_REQUIRED:'请先通过原业务平台登录',CLOUD_ACCOUNT_CHANGED:'账号已变化，旧会话已清除，请重新连接',CLOUD_NOT_INSTALLED:'服务器图层同步接口尚未安装',CLOUD_ACCESS_DENIED:'当前账号没有图层访问权限',CLOUD_HOST_PEER_INVALID:'三维页面地址已变化，连接已关闭',CLOUD_HOST_NOT_READY:'三维页面尚未就绪，请稍后重连',CLOUD_HOST_SESSION_REVOKED:'登录或项目权限已失效，旧三维会话已关闭',CLOUD_HOST_SESSION_CLOSED:'三维会话已断开，请重新连接'};
Object.assign(messages,{"LOCAL_GIS_UNAVAILABLE":"未能连接本机三维服务，请确认服务已启动并允许此站点访问本机网络后重连","LOCAL_GIS_VERSION_MISMATCH":"本机三维资源版本不匹配，请更新本机三维组件后重连","LOCAL_GIS_GRANT_REJECTED":"本机三维授权已失效，请重新连接","LOCAL_GIS_GRANT_UNAVAILABLE":"三维授权服务暂不可用，请稍后重连","LOCAL_GIS_SESSION_REQUIRED":"本机三维会话已结束，请重新连接","LOCAL_GIS_SOURCE_CHANGED":"本机地景资源已切换，请重新连接","LOCAL_GIS_RENEWAL_FAILED":"三维会话续期失败，请重新连接","LOCAL_GIS_ABORTED":"三维连接已中断，请重新连接"});
const statusText=computed(()=>state.value.capability==='client-resources'?(state.value.state==='ready'?'本机资源管理已连接；三维地景未加载':state.value.state==='loading'?'正在核对项目登录并连接本机资源管理':messages[state.value.code]??'资源服务尚未连接，可检查本机程序后重连'):state.value.state==='ready'?(state.value.access==='read-only'?'项目图层已连接，当前为只读；详见编辑面板':'项目图层已连接；保存与协同状态见三维编辑面板'):state.value.state==='loading'?'正在打开三维页面并核对项目登录':messages[state.value.code]??'三维图层编辑尚未连接');
const connect=()=>owner?.start().catch(()=>{});
async function mountOwner(topic=route.query.topic){const generation=++ownerGeneration,old=owner;owner=null;const closing=old?.dispose();retiringOwner=Promise.allSettled([retiringOwner,closing]);await retiringOwner;if(generation!==ownerGeneration||!scene.value)return;try{owner=createProjectSceneHost({frame:scene.value,origin:location.origin,topic,development:import.meta.env.VITE_SCENE_HOST_DEVELOPMENT==='true'&&location.hostname==='127.0.0.1',authorizationProvider:getToken,resourceEndpoint:import.meta.env.VITE_SCENE_HOST_DEVELOPMENT==='true'&&location.hostname==='127.0.0.1'?new URL('/xnby-client-resources/v1/',location.origin).href:undefined,onTopicRequest:value=>router.push({path:route.path,query:{topic:value}}),onState:value=>state.value=value});connect();}catch(error){state.value={state:'error',code:error.code??'CLOUD_HOST_FAILED'};}}
onMounted(()=>{void mountOwner();});watch(()=>route.query.topic,value=>{void mountOwner(value);});
onActivated(()=>{if(owner)connect();else void mountOwner();});onDeactivated(()=>{ownerGeneration++;const closing=owner?.stop();retiringOwner=Promise.allSettled([retiringOwner,closing]);return retiringOwner;});
onBeforeRouteLeave(async()=>{ownerGeneration++;await owner?.stop();await retiringOwner;});
onBeforeUnmount(()=>{ownerGeneration++;retiringOwner=Promise.allSettled([retiringOwner,owner?.dispose()]);owner=null;});
</script>
<style scoped>
.scene-editor-page{height:calc(100dvh - 110px);min-height:450px;display:flex;flex-direction:column;margin:12px;background:#0d2338}.scene-editor-status{display:flex;align-items:center;gap:12px;min-height:36px;padding:6px 12px;color:#dcecff;font-size:12px}.scene-editor-status button{cursor:pointer}iframe{flex:1;width:100%;min-height:0;border:0;background:#0d2338}
.scene-mode-link{color:#b9e1ff;text-decoration:underline;white-space:nowrap}.scene-editor-status{flex-wrap:wrap}</style>
