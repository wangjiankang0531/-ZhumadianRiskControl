<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :disable="disableConfig" :columns="columns1">
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
import { ref, onMounted, computed } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById } from "@/api/emergencyResponse/response";
import { useDict } from "@/hooks/useDict";
import { useUserStore } from "@/store/modules/user";
import UploadImgs from "@/components/Upload/Imgs.vue";
import moment from "moment";
import MapPoint from "@/components/MapPoint/index.vue";

const userStore = useUserStore();
const { eventType, eventLevel, /*reportType, eventStatus, researchStatus,*/ functionArea } = useDict("safetycode", [
  "eventType",
  "eventLevel",
  // "reportType",
  // "eventStatus",
  // "researchStatus",
  "functionArea"
]);

const field = ref<any>({
  fileList: []
});
const disableConfig = computed(() => {
  let disableField = { reporterName: true, researchStatus: true };
  if (route.query.type == "edit") {
    disableField.researchStatus = false;
  }
  return disableField;
});

/** 当前用户信息 */
const loginUser = computed<any>(() => userStore.info ?? {});

const columns1 = ref<ColumnProps[]>([
  // {
  //   el: "input",
  //   prop: "pointId",
  //   label: "巡检点id",
  //   // required: true
  // },
  {
    el: "input",
    prop: "eventNumber",
    label: "事件编号",
    attrs: {
      disabled: true,
      placeholder: "系统自动生成"
    }
  },
  {
    el: "input",
    prop: "eventName",
    label: "事件名称",
    required: true
  },
  {
    el: "select",
    prop: "eventLocation",
    label: "事件区域",
    enumData: functionArea,
    attrs: {
      filterable: true
    },
    required: true
  },
  {
    el: "input",
    prop: "eventContent",
    label: "事件内容",
    required: true,
    attrs: {
      type: "textarea",
      maxlength: 200,
      showWordLimit: true,
      rows: 3
    },
    span: 3,
    rules: [{ max: 200, message: "处置描述最大长度200", trigger: "blur" }]
  },
  {
    el: "select",
    prop: "eventType",
    label: "事件类型",
    enumData: eventType,
    attrs: {
      filterable: true
    },
    required: true
  },
  {
    el: "date-picker",
    prop: "reportTime",
    label: "上报时间",
    attrs: { valueFormat: "YYYY-MM-DD HH:mm:ss", type: "datetime" },
    required: true
  },
  {
    el: "input",
    prop: "reporterName",
    label: "上报人",
    required: true
  },
  {
    el: "select",
    prop: "eventLevel",
    label: "事件级别",
    enumData: eventLevel
  },
  {
    prop: "coordinate",
    label: "坐标信息",
    required: true
  },
  {
    prop: "fileUrl",
    label: "事件图片",
    render: () => <UploadImgs v-model:file-list={field.value.fileList} />,
    span: 3
  }

  // {
  //   el: "select",
  //   prop: "reportType",
  //   label: "上报类型",
  //   enumData: reportType
  // },
  // {
  //   el: "select",
  //   prop: "eventStatus",
  //   label: "事件状态",
  //   enumData: eventStatus
  // },
  // {
  //   el: "select",
  //   prop: "researchStatus",
  //   label: "研判状态",
  //   enumData: researchStatus,
  //   required: true,
  //   render: () => {
  //     return (
  //       route.query.type == "add" ?
  //         <el-select
  //           v-model={field.value.researchStatus}
  //           options={researchStatus.value}
  //           disabled={true}
  //           props={{
  //             value: "value",
  //             label: "label"
  //           }}
  //           placeholder="请选择"
  //         /> : <el-select
  //           v-model={field.value.researchStatus}
  //           options={researchStatus.value.map(e => {
  //             e.disabled = e.label === '待研判' ? true : false;
  //             return e
  //           })}
  //           props={{
  //             value: "value",
  //             label: "label"
  //           }}
  //           placeholder="请选择"
  //         />
  //     );
  //   }
  // },
  // {
  //   el: "input",
  //   prop: "researchResult",
  //   label: "研判结果"
  // },
  // {
  //   el: "select",
  //   prop: "isTaskPrimary",
  //   label: "是否为主关联任务信息",
  //   enumData: [
  //     {label: "否", value: "0"},
  //     {label: "是", value: "1"}
  //   ]
  // }
  // {
  //   prop: "coordinate",
  //   label: "坐标"
  // }
]);

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

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

const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid1 = await formRef.value!.validate();
  if (!valid1) return;
  const params = JSON.parse(JSON.stringify(field.value));

  // if (!params.coordinate) {
  //   ElMessage.error("请选择坐标！");
  //   return;
  // }

  params.fileUrl = field.value.fileList.map(item => item.url).join(",");
  delete params.fileList;

  let response: any;
  try {
    response = await api(params);
  } catch {
    return false;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("保存未完成，请保留当前内容，核对事件或任务状态后重试。");
    return false;
  }
  ElMessage.success(message);
  router.push({
    path: "/emergencyResponse/response"
  });
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  field.value.reporterName = loginUser.value?.userName ?? "";
  field.value.researchStatus = "0";
  field.value.reportTime = moment(new Date()).format("YYYY-MM-DD HH:mm:ss");
  if (route.query.type == "edit" && route.query.id) {
    let res: any;
    try {
      res = await getById({ id: route.query.id });
    } catch {
      return false;
    }
    const detail = res?.data;
    if (res?.code !== 0 || !detail || typeof detail !== "object" || Array.isArray(detail)
      || typeof detail.id !== "string" || !detail.id.trim()
      || (detail.fileUrl != null && typeof detail.fileUrl !== "string")) {
      ElMessage.error("详情未取得，请返回列表刷新后重试。");
      return false;
    }
    field.value = detail;
    const fileList = res.data.fileUrl ? res.data.fileUrl.split(",") : [];
    field.value.fileList = fileList.map(item => ({ name: item, url: item }));

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
