<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="form1Ref" :field="field" :columns="columns1">
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
  <List v-model:data="list" />
  <MapPoint ref="mapPointRef" />
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
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
const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid1 = await form1Ref.value!.validate();
  if (!valid1) return;

  // if (!field.value.coordinate) {
  //   ElMessage.error("请选择坐标！");
  //   return;
  // }

  if (route.query.type == "edit") {
    field.value.updatedBy = userStore.info?.userId;
  }
  if (route.query.type == "add") {
    field.value.createdBy = userStore.info?.userId;
    field.value.createDept = userStore.info?.departmentId;
  }

  let response: any;
  try {
    response = await api({ teams: field.value, members: list.value });
  } catch {
    return;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("保存未完成，请保留当前内容，核对队伍状态后重试。");
    return;
  }
  ElMessage.success(message);
  router.push({
    path: "/emergencyResources/firstAidTeams"
  });
};

const router = useRouter();
const route = useRoute();

const mapPointRef = ref<InstanceType<typeof MapPoint> | null>(null);

const openMapDialog = () => {
  const params = {
    title: "坐标信息",
    isView: false,
    callback: val => (field.value.coordinate = val)
  };
  mapPointRef.value!.acceptParams(params, field.value.coordinate);
};

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    const res: any = await getById({ id: route.query.id });
    field.value = res.data.teams;
    list.value = res.data.members;
    // if (!field.value?.coordinate) return;
    // let arr = field.value.coordinate.split(",");
    // const [lng, lat] = arr;
    // mapRef.value!.setMarker({ lng, lat });
    // mapRef.value!.setMapCenter({ lng, lat });
  }
});

defineExpose({
  submit: handleSubmit
});
</script>
