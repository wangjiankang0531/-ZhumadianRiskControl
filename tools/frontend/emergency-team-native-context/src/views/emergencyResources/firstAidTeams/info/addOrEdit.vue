<template>
  <div class="info-title">基础信息</div>
  <el-alert v-if="loadState === 'error'" type="error" :title="loadError" :closable="false" show-icon />
  <el-button v-if="loadState === 'error'" @click="loadCurrent">重新加载</el-button>
  <div v-if="loadState === 'loading'" role="status">正在加载队伍信息</div>
  <MyForm v-show="loadState === 'ready'" ref="form1Ref" :field="field" :columns="columns1" :disabled="loadState !== 'ready' || isSubmitting">
    <!-- 经纬度 -->
    <template #coordinate>
      <div class="flx-align-center" style="width: 100%">
        <el-input
          :input-style="{ cursor: 'pointer' }"
          readonly
          :value="field.coordinate"
          placeholder="请选择"
          @click="openMapDialog"
        />
      </div>
    </template>
  </MyForm>
  <div class="info-title">应急人员</div>
  <fieldset v-if="loadState === 'ready'" :disabled="isSubmitting" style="border:0;padding:0;margin:0"><List :key="generation" v-model:data="list" /></fieldset>
  <MapPoint ref="mapPointRef" />
</template>

<script setup lang="tsx">
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById } from "@/api/emergencyResources/firstAidTeams";
import { useOrgTree } from "@/hooks/useOrgTree";
import { useUserStore } from "@/store/modules/user";
import List from "../components/List/index.vue";
import MapPoint from "@/components/MapPoint/index.vue";

const userStore = useUserStore();
const { orgTree } = useOrgTree();

const field = ref<any>({});

const list = ref<any>([]);

const columns1 = ref<ColumnProps[]>([
  {
    el: "input",
    prop: "teamName",
    label: "队伍名称",
    required: true
  },
  {
    el: "input",
    prop: "teamType",
    label: "队伍类型",
    required: true
  },
  {
    el: "input",
    prop: "leaderName",
    label: "负责人名称",
    required: true
  },
  {
    el: "input",
    prop: "leaderPhone",
    label: "负责人电话",
    rules: ["phone"],
    required: true
  },
  {
    prop: "department",
    label: "所属部门",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.department}
          data={orgTree.value}
          check-strictly={true}
          clearable={true}
          filterable={true}
          props={{
            label: "fullName",
            value: "fullName"
          }}
        />
      );
    },
    required: true
  },
  {
    el: "input",
    prop: "teamLocation",
    label: "队伍位置"
  },
  {
    prop: "coordinate",
    label: "坐标信息",
    required: true
  }
]);

// const tableColumns = ref<ColumnProps[]>([
//   {
//     el: "input",
//     prop: "memberName",
//     label: "人员名称"
//   },
//   {
//     el: "input",
//     prop: "memberPhone",
//     label: "人员电话"
//   },
//   {
//     el: "input",
//     prop: "gender",
//     label: "性别"
//   },
//   {
//     el: "input",
//     prop: "major",
//     label: "专业"
//   },
//   {
//     el: "input",
//     prop: "position",
//     label: "职位"
//   }
// ]);

const form1Ref = ref<InstanceType<typeof MyForm> | null>(null);
const loadState = ref<"loading" | "ready" | "error">("loading");
const loadError = ref("");
const isSubmitting = ref(false);
let mounted = true;
let generation = 0;
let loadedKey = "";
const context = () => {
  const type = route.query.type;
  const id = typeof route.query.id === "string" ? route.query.id : "";
  if ((type !== "add" && type !== "edit") || (type === "edit" && !id)) return null;
  return { type, id: type === "edit" ? id : "", actor: userStore.info?.userId, department: userStore.info?.departmentId };
};
const keyOf = (value: ReturnType<typeof context>) => value ? JSON.stringify([value.type, value.id, value.actor ?? null, value.department ?? null]) : "";
const current = (epoch: number, key: string) => mounted && epoch === generation && key !== "" && key === keyOf(context());
const canSubmit = computed(() => mounted && loadState.value === "ready" && loadedKey === keyOf(context()) && !isSubmitting.value && !!form1Ref.value);
const loadCurrent = async () => {
  const epoch = ++generation;
  const value = context();
  const key = keyOf(value);
  loadedKey = "";
  field.value = {};
  list.value = [];
  loadError.value = "";
  loadState.value = "loading";
  if (!value) {
    loadState.value = "error";
    loadError.value = "队伍标识或操作方式无效，请返回列表重新选择。";
    return;
  }
  if (value.type === "add") { loadedKey = key; loadState.value = "ready"; return; }
  try {
    const response = await getById({ id: value.id });
    if (!current(epoch, key)) return;
    const data = response?.data;
    if (response?.code !== 0 || !data?.teams || String(data.teams.id) !== value.id || !Array.isArray(data.members) || data.members.some(row => !row || String(row.teamId) !== value.id)) throw new Error("TEAM_DETAIL_NOT_CONFIRMED");
    field.value = { ...data.teams };
    list.value = data.members.map(row => ({ ...row }));
    loadedKey = key;
    loadState.value = "ready";
  } catch {
    if (!current(epoch, key)) return;
    loadState.value = "error";
    loadError.value = "队伍信息加载未完成，请重新加载后再编辑。";
  }
};
const handleSubmit = async () => {
  if (!canSubmit.value) return;
  const value = context();
  if (!value) return;
  const epoch = generation;
  const key = keyOf(value);
  isSubmitting.value = true;
  try {
    const valid = await form1Ref.value!.validate();
    if (!valid || !current(epoch, key) || loadedKey !== key) return;
    const payload = { ...field.value };
    if (value.type === "edit") {
      if (String(payload.id) !== value.id) return;
      payload.id = value.id;
      payload.updatedBy = value.actor;
    } else {
      delete payload.id;
      payload.createdBy = value.actor;
      payload.createDept = value.department;
    }
    const members = list.value.map(row => ({ ...row }));
    if (value.type === "edit" && members.some(row => row.teamId != null && String(row.teamId) !== value.id)) return;
    const response = await (value.type === "edit" ? updateById : save)({ teams: payload, members });
    if (!current(epoch, key)) return;
    if (response?.code !== 0 || response?.data !== true) {
      ElMessage.error("保存未完成，请保留当前内容，核对队伍状态后重试。");
      return;
    }
    ElMessage.success(value.type === "edit" ? "编辑成功！" : "新增成功！");
    await router.push({ path: "/emergencyResources/firstAidTeams" });
  } catch {
    // The retained request layer reports transport/business errors; keep current inputs.
    return;
  } finally {
    isSubmitting.value = false;
  }
};

const router = useRouter();
const route = useRoute();

const mapPointRef = ref<InstanceType<typeof MapPoint> | null>(null);

const openMapDialog = () => {
  if (!canSubmit.value) return;
  const epoch = generation;
  const key = keyOf(context());
  const params = {
    title: "坐标信息",
    isView: false,
    callback: val => { if (current(epoch, key) && loadState.value === "ready" && !isSubmitting.value && loadedKey === key) field.value.coordinate = val; }
  };
  mapPointRef.value!.acceptParams(params, field.value.coordinate);
};

watch(() => [route.query.type, route.query.id, userStore.info?.userId, userStore.info?.departmentId], loadCurrent, { immediate: true });
onBeforeUnmount(() => { mounted = false; generation++; loadedKey = ""; });

defineExpose({
  submit: handleSubmit,
  canSubmit,
  isSubmitting
});
</script>
