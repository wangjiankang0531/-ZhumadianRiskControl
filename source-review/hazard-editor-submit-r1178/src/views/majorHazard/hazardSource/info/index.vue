<template>
  <InfoView>
    <template #content>
      <AddOrEdit ref="addOrEditRef" v-if="['add', 'edit'].includes(type)" />
      <Detail v-else />
    </template>
    <template #footer>
      <el-button type="primary" v-if="['add', 'edit'].includes(type)" :loading="addOrEditRef?.submitting" :disabled="addOrEditRef?.submitting || addOrEditRef?.writeCommitted || !addOrEditRef?.detailReady" @click="addOrEditRef?.submit">提交</el-button>
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

const handleCancel = () => {
  router.push({
    path: "/majorHazard/hazardSource"
  });
};
</script>

<style scoped lang="scss"></style>
