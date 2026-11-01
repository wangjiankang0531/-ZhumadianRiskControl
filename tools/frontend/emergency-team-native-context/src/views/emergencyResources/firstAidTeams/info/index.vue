<template>
  <InfoView>
    <template #content>
      <AddOrEdit ref="addOrEditRef" v-if="['add', 'edit'].includes(type)" />
      <Detail v-else />
    </template>
    <template #footer>
      <el-button type="primary" v-if="['add', 'edit'].includes(type)" :disabled="!addOrEditRef?.canSubmit" :loading="addOrEditRef?.isSubmitting" @click="addOrEditRef?.submit">提交</el-button>
      <el-button @click="handleCancel">{{ ["add", "edit"].includes(type) ? "取消" : "返回" }}</el-button>
    </template>
  </InfoView>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import AddOrEdit from "./addOrEdit.vue";
import Detail from "./detail.vue";
import InfoView from "@/components/InfoView/index.vue";

const route = useRoute();
const type = computed(() => typeof route.query.type === "string" ? route.query.type : "");

const router = useRouter();

const addOrEditRef = ref<InstanceType<typeof AddOrEdit> | null>(null);

const handleCancel = () => {
  if (addOrEditRef.value?.isSubmitting) ElMessage.warning("正在处理的保存请求不会自动撤回，请返回列表核对结果。");
  router.push({
    path: "/emergencyResources/firstAidTeams"
  });
};
</script>

<style scoped lang="scss"></style>
