<!-- 可读等价实现；本轮产物来自限定发布文件转换，不宣称由此文件全量构建。 -->
<template>
  <InfoView>
    <template #content>
      <AddOrEdit ref="addOrEditRef" v-if="['add', 'edit'].includes(type)" />
      <Detail v-else ref="detailRef" />
    </template>
    <template #footer>
      <el-button type="primary" v-if="['add', 'edit'].includes(type)" @click="addOrEditRef?.submit">提交</el-button>
      <el-button type="primary" v-if="route.query.judge" :loading="detailRef?.submitting" :disabled="detailRef?.submitting" @click="detailRef?.submit">提交</el-button>
      <el-button @click="handleCancel">{{ ["add", "edit"].includes(type) ? "取消" : "返回" }}</el-button>
    </template>
  </InfoView>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AddOrEdit from "./addOrEdit.vue";
import Detail from "./detail.vue";
import InfoView from "@/components/InfoView/index.vue";

const route = useRoute();
const type = route.query.type as string;

const router = useRouter();

const addOrEditRef = ref<InstanceType<typeof AddOrEdit> | null>(null);
const detailRef = ref<InstanceType<typeof Detail> | null>(null);

const handleCancel = () => {
  router.push({
    path: "/emergencyResponse/taskSend"
  });
};
</script>

<style scoped lang="scss"></style>
