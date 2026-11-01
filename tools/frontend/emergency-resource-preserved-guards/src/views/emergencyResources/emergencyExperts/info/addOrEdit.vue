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
  <MapPoint ref="mapPointRef" />
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById } from "@/api/emergencyResources/emergencyExperts/index";
import { useOrgTree } from "@/hooks/useOrgTree";
import { useUserStore } from "@/store/modules/user";
import MapPoint from "@/components/MapPoint/index.vue";

const userStore = useUserStore();
const { orgTree } = useOrgTree();

// import { useDict } from "@/hooks/useDict";

// const { specialHomework } = useDict("safetycode", ["specialHomework"]);

const field = ref<any>({});

const columns1 = ref<ColumnProps[]>([
  {
    el: "input",
    prop: "expertName",
    label: "专家姓名",
    required: true
  },
  {
    el: "input",
    prop: "expertPhone",
    label: "专家电话",
    rules: ["phone"],
    required: true
  },
  {
    el: "input",
    prop: "expertField",
    label: "专家领域",
    required: true
  },
  {
    el: "input",
    prop: "expertEducation",
    label: "专家学历"
  },
  {
    el: "input",
    prop: "expertMajor",
    label: "专家专业"
  },
  {
    el: "input",
    prop: "workingYears",
    label: "工作年限",
    rules: ["number"]
  },
  {
    el: "input",
    prop: "expertLocation",
    label: "住址"
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
    }
  },
  {
    el: "input",
    prop: "notes",
    label: "备注"
  },
  {
    prop: "coordinate",
    label: "坐标信息"
  }
]);

const form1Ref = ref<InstanceType<typeof MyForm> | null>(null);
const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid1 = await form1Ref.value!.validate();
  if (!valid1) return;

  if (route.query.type == "edit") {
    field.value.updatedBy = userStore.info?.userId;
  } else if (route.query.type == "add") {
    field.value.createdBy = userStore.info?.userId;
    field.value.createDept = userStore.info?.departmentId;
  }

  let response: any;
  try {
    response = await api(field.value);
  } catch {
    return;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("保存未完成，请保留当前内容，核对当前记录状态后重试。");
    return;
  }
  ElMessage.success(message);
  router.push({
    path: "/emergencyResources/emergencyExperts"
  });
};

const router = useRouter();
const route = useRoute();

// 经纬度选择
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
    const res = await getById({ id: route.query.id });
    field.value = res.data;
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
