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
import { save, updateById, getById } from "@/api/emergencyResources/materials";
import { useOrgTree } from "@/hooks/useOrgTree";
import { useUserStore } from "@/store/modules/user";
import MapPoint from "@/components/MapPoint/index.vue";
import { useDict } from "@/hooks/useDict";

const userStore = useUserStore();
const { orgTree } = useOrgTree();

// import { useDict } from "@/hooks/useDict";

const { materialType } = useDict("safetycode", ["materialType"]);

const field = ref<any>({});

const columns1 = ref<ColumnProps[]>([
  {
    el: "input",
    prop: "materialName",
    label: "物资名称",
    required: true
  },
  {
    el: "select",
    prop: "materialType",
    label: "物资类型",
    enumData: materialType,
    attrs: {
      filterable: true
    },
    required: true
  },
  {
    el: "input",
    prop: "materialModel",
    label: "物资型号"
  },
  {
    el: "input",
    prop: "materialQuantity",
    label: "物资数量",
    rules: ["number"]
  },
  {
    el: "input",
    prop: "unit",
    label: "物资单位"
  },
  {
    el: "input",
    prop: "storageLocation",
    label: "存放地点"
  },

  {
    el: "input",
    prop: "person",
    label: "责任人"
  },
  {
    el: "input",
    prop: "phone",
    label: "联系方式"
  },
  {
    el: "input",
    prop: "technicalRequirement",
    label: "技术要求"
  },

  {
    prop: "department",
    label: "所属部门",
    required: true,
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
    prop: "coordinate",
    label: "坐标信息",
    required: true
  },
  {
    el: "input",
    prop: "remark",
    label: "备注",
    attrs: {
      type: "textarea",
      maxlength: 200,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    },
    span: 3
  }
]);

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
    path: "/emergencyResources/materials"
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
