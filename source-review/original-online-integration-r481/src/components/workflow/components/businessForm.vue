<template>
  <div>
    <div v-if="props.businessFormName" class="title mb12">{{ props.businessFormName }}</div>
    <el-skeleton v-if="loading" :rows="4" animated />
    <el-alert v-else-if="loadError" :title="loadError" type="error" :closable="false" show-icon />
    <component v-else-if="legacyComponent" :is="legacyComponent" :workflow-task-id="props.workflowTaskId" />
    <template v-else-if="onlineForm">
      <OriginalOnlineForm ref="onlineRef" :property-json="props.formInfo.propertyJson" :form-data="props.formData"
        :form-operates="props.formOperates" :editable="props.editable"
        @update:form-data="value => emit('update:formData', value)" />
      <section v-if="associatedTask" class="associated-task">
        <div class="title mb12">任务详情</div>
        <TaskDetail :key="props.workflowTaskId" :workflow-task-id="props.workflowTaskId" />
      </section>
    </template>
    <el-empty v-else-if="props.workflowTaskId" description="此流程尚未配置可显示的表单" :image-size="64" />
  </div>
</template>
<script setup lang="ts">
import { computed, defineAsyncComponent, markRaw, onBeforeUnmount, ref, watch } from "vue";
import OriginalOnlineForm from "./OriginalWorkflowOnlineFormR470.vue";
const TaskDetail = defineAsyncComponent(() => import("@/views/emergencyResponse/taskSend/info/detail.vue"));
const props = withDefaults(defineProps<{
  businessFormName?: string;
  workflowTaskId?: string;
  componentUrl?: string;
  formInfo?: Record<string, any>;
  formData?: Record<string, unknown>;
  formOperates?: unknown[];
  editable?: boolean;
}>(), { businessFormName: "", workflowTaskId: "", componentUrl: "", formInfo: () => ({}), formData: () => ({}), formOperates: () => [], editable: false });
const emit = defineEmits<{ (event: "update:formData", data: Record<string, unknown>): void }>();
const onlineForm = computed(() => !props.componentUrl?.trim() && Number(props.formInfo.formType) === 2);
const associatedTask = computed(() => onlineForm.value && props.formInfo.enCode === "tj_eventTask" && !!props.workflowTaskId);
const onlineRef = ref();
const legacyComponent = ref<any>(null);
const loading = ref(false), loadError = ref("");
let generation = 0;
const modules = import.meta.glob("/src/views/**/**.vue");
watch(() => props.componentUrl, async raw => {
  const version = ++generation;
  legacyComponent.value = null; loadError.value = ""; loading.value = false;
  if (!raw?.trim()) return;
  const relative = raw.trim().replace(/^\/?src\/views\//, "").replace(/^\/+/, "");
  const exact = "/src/views/" + relative;
  const loader = modules[exact] || (!relative.endsWith(".vue") ? modules[exact + ".vue"] : undefined);
  if (!loader) { loadError.value = "暂时无法打开此业务表单，请刷新后重试"; return; }
  loading.value = true;
  try {
    const result: any = await loader();
    if (version !== generation) return;
    if (!result?.default) { loadError.value = "暂时无法打开此业务表单，请刷新后重试"; return; }
    legacyComponent.value = markRaw(result.default);
  } catch {
    if (version === generation) loadError.value = "暂时无法打开此业务表单，请刷新后重试";
  } finally {
    if (version === generation) loading.value = false;
  }
}, { immediate: true });
onBeforeUnmount(() => { generation++; });
function validate() { return !onlineForm.value || onlineRef.value?.validate() === true; }
defineExpose({ validate });
</script>
<style scoped>
.mb12 { margin-bottom: 12px; }
.associated-task { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--el-border-color-light); }
</style>
