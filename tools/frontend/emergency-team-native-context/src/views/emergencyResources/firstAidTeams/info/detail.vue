<template>
  <el-alert v-if="loadState === 'error'" title="队伍详情未加载完成，请重新加载。" type="error" :closable="false" show-icon />
  <el-button v-if="loadState === 'error'" @click="loadDetail">重新加载</el-button>
  <div v-if="loadState === 'loading'" role="status">正在加载队伍详情</div>
  <div v-if="loadState === 'ready'">
  <div class="info-title">基础信息</div>
  <MyDetail :field="field" :columns="columns1" />
  <div class="info-title">应急人员</div>
  <List v-model:data="list" is-view />
  <MapPoint ref="mapPointRef" />
  </div>
</template>

<script setup lang="tsx">
import { ref, watch, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import MyDetail from "@/components/Detail/index.vue";
import { ColumnProps } from "@/components/Detail/interface";
import { getById } from "@/api/emergencyResources/firstAidTeams";
import List from "../components/List/index.vue";
import MapPoint from "@/components/MapPoint/index.vue";
// import { useDict } from "@/hooks/useDict";

// const { specialHomework } = useDict("safetycode", ["specialHomework"]);
const field = ref<any>({});
const columns1 = ref<ColumnProps[]>([
  {
    prop: "teamName",
    label: "队伍名称"
  },
  {
    prop: "teamType",
    label: "队伍类型"
  },
  {
    prop: "leaderName",
    label: "负责人名称"
  },
  {
    prop: "leaderPhone",
    label: "负责人电话"
  },
  {
    prop: "department",
    label: "所属部门",
    render: () => <el-input model-value={field.value.department ?? "--"} />
  },
  {
    prop: "teamLocation",
    label: "队伍位置"
  },
  {
    prop: "coordinate",
    label: "坐标信息",
    render: () => {
      if (!field.value.coordinate) return <el-input value="--" />;
      return (
        <el-link type="primary" onClick={openMapDialog}>
          查看坐标
        </el-link>
      );
    }
  }
]);

const mapPointRef = ref<InstanceType<typeof MapPoint> | null>(null);

const openMapDialog = () => {
  const params = {
    title: "坐标信息",
    isView: true
  };
  mapPointRef.value!.acceptParams(params, field.value.coordinate);
};

const list = ref<any>([]);

const route = useRoute();

const loadState = ref<"loading" | "ready" | "error">("loading");
let generation = 0;
let mounted = true;
const loadDetail = async () => {
  const epoch = ++generation;
  const id = typeof route.query.id === "string" ? route.query.id : "";
  field.value = {};
  list.value = [];
  loadState.value = "loading";
  if (!id) { loadState.value = "error"; return; }
  const current = () => mounted && epoch === generation && route.query.id === id;
  try {
    const response: any = await getById({ id });
    if (!current()) return;
    const data = response?.data;
    if (response?.code !== 0 || !data?.teams || String(data.teams.id) !== id || !Array.isArray(data.members) || data.members.some(row => !row || String(row.teamId) !== id)) throw new Error("TEAM_DETAIL_NOT_CONFIRMED");
    field.value = { ...data.teams };
    list.value = data.members.map(row => ({ ...row }));
    loadState.value = "ready";
  } catch {
    if (current()) loadState.value = "error";
  }
};
watch(() => route.query.id, loadDetail, { immediate: true });
onBeforeUnmount(() => { mounted = false; generation++; });
</script>
