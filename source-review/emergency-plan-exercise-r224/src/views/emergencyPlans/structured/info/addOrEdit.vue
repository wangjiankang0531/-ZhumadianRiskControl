<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns">
    <template #url>
      <UploadFiles ref="attachmentRef" v-model:fileList="fileList" :disabled="attachmentSubmitting" />
    </template>
  </MyForm>
  <div class="info-title">成员信息</div>
  <FormList title="副指挥长" v-model:list="deputyHeadList" />
  <FormList title="其他成员" v-model:list="othermemberList" />
  <FormList title="参与单位" v-model:list="companyList" />
  <div class="info-title">应急信息</div>
  <el-tabs v-model="activeName" class="demo-tabs" @tab-click="handleClick">
    <el-tab-pane label="应急物资" name="first">
      <GoodsList v-model:list="goodsList" @check="goodsListCheck" @delete="goodsListDelete" />
    </el-tab-pane>
    <el-tab-pane label="应急队伍" name="second">
      <TeamsList v-model:list="teamsList" @check="teamsListCheck" @delete="teamsListDelete" />
    </el-tab-pane>
    <el-tab-pane label="应急专家" name="third">
      <ExpertsList v-model:list="expertsList" @check="expertsListCheck" @delete="expertsListDelete" />
    </el-tab-pane>
  </el-tabs>
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import GoodsList from "../components/goodsList.vue";
import TeamsList from "../components/teamsList.vue";
import ExpertsList from "../components/expertsList.vue";
import { ElMessage, TabsPaneContext } from "element-plus";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import UploadFiles from "@/components/Upload/Files.vue";
import { save, updateById, getById } from "@/api/emergencyPlans/structured";
import { useDict } from "@/hooks/useDict";
import FormList from "../components/formList.vue";

const goodsList = ref<any>([]);
const teamsList = ref<any>([]);
const expertsList = ref<any>([]);
const goodsIdsList = ref<any>([]);
const teamsIdsList = ref<any>([]);
const expertsIdsList = ref<any>([]);

const deputyHeadList = ref<any>([]);
const othermemberList = ref<any>([]);
const companyList = ref<any>([]);

const activeName = ref("first");
const goodsListCheck = (data: any) => {
  let obj = goodsList.value.find(item => item.id == data.id);
  if (obj === undefined) {
    goodsList.value?.push(data);
    goodsIdsList.value?.push(data.id);
  }
};
const goodsListDelete = (index: number) => {
  if (!Number.isInteger(index) || index < 0 || index >= goodsList.value.length) return;
  const removed = goodsList.value.splice(index, 1)[0];
  goodsIdsList.value = goodsIdsList.value.filter(id => id != removed.id);
};

const teamsListCheck = (data: any) => {
  let obj = teamsList.value.find(item => item.id == data.id);
  if (obj === undefined) {
    teamsList.value?.push(data);
    teamsIdsList.value?.push(data.id);
  }
};
const teamsListDelete = (index: number) => {
  if (!Number.isInteger(index) || index < 0 || index >= teamsList.value.length) return;
  const removed = teamsList.value.splice(index, 1)[0];
  teamsIdsList.value = teamsIdsList.value.filter(id => id != removed.id);
};
const expertsListCheck = (data: any) => {
  let obj = expertsList.value.find(item => item.id == data.id);
  if (obj === undefined) {
    expertsList.value?.push(data);
    expertsIdsList.value?.push(data.id);
  }
};
const expertsListDelete = (index: number) => {
  if (!Number.isInteger(index) || index < 0 || index >= expertsList.value.length) return;
  const removed = expertsList.value.splice(index, 1)[0];
  expertsIdsList.value = expertsIdsList.value.filter(id => id != removed.id);
};
const handleClick = (tab: TabsPaneContext, event: Event) => {
  console.log(tab, event);
};
const { emergencyPlanType, eventType } = useDict("safetycode", ["emergencyPlanType", "eventType"]);

const attachmentRef = ref<InstanceType<typeof UploadFiles> | null>(null);
const attachmentSubmitting = ref(false);
const fileList = ref<any>([]);

const field = ref<any>({});
const columns = ref<ColumnProps[]>([
  {
    el: "input",
    label: "应急预案名称",
    prop: "emergencyPlanName",
    required: true
  },
  {
    el: "select",
    label: "应急预案类型",
    prop: "emergencyPlanType",
    enumData: emergencyPlanType
  },
  {
    el: "select",
    label: "事故类型",
    prop: "accidentType",
    enumData: eventType
  },
  {
    el: "input",
    label: "事故区域",
    prop: "eventLocation"
  },

  {
    el: "input",
    label: "指挥长",
    prop: "commanderName"
  },
  {
    el: "input",
    label: "指挥长电话",
    rules: ["phone"],
    prop: "commanderPhone"
  },
  {
    el: "radio",
    label: "是否备案",
    prop: "isFilings",
    enumData: [
      { label: "是", value: "1" },
      { label: "否", value: "0" }
    ],
    required: true
  },
  {
    el: "input",
    prop: "disposalMeasures",
    label: "处置措施",
    attrs: {
      type: "textarea",
      maxlength: 500,
      showWordLimit: true,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    },
    span: 3
  },
  {
    prop: "url",
    label: "附件"
  }
]);

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

const handleSubmit = async () => {
  if (attachmentSubmitting.value || !attachmentRef.value?.ensureReady()) return false;
  attachmentSubmitting.value = true;
  try {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid = await formRef.value!.validate();
  if (!valid) return;
  if (!attachmentRef.value?.ensureReady()) return false;

  const params = JSON.parse(JSON.stringify(field.value));

  params.emergencyExpertIdList = expertsIdsList.value;
  params.emergencyExpertList = expertsList.value;
  params.emergencyGoodsManageIdList = goodsIdsList.value;
  params.emergencyGoodsManageList = goodsList.value;
  params.emergencyTeamIdList = teamsIdsList.value;
  params.emergencyTeamList = teamsList.value;
  params.emergencyPlanCompanyList = companyList.value;
  params.emergencyPlanDeputyHeadList = deputyHeadList.value;
  params.emergencyPlanOthermemberList = othermemberList.value;
  params.fileList = fileList.value.map((item: any) => {
    return {
      ...item,
      fileName: item.name,
      fileUrl: item.url
    };
  });
  let response: any;
  try {
    response = await api(params);
  } catch {
    return false;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("保存未完成，请保留当前内容，核对应急预案或事件报送后重试。");
    return false;
  }
  ElMessage.success(message);
  router.push({
    path: "/emergencyPlans/structured"
  });
  } finally { attachmentSubmitting.value = false; }
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    let res: any;
    try {
      res = await getById({ id: route.query.id });
    } catch {
      return false;
    }
    if (res?.code !== 0 || !res.data || typeof res.data !== "object" || Array.isArray(res.data)
        || typeof res.data.id !== "string" || !res.data.id.trim()) {
      ElMessage.error("预案详情未取得，请返回列表刷新后重试。");
      return false;
    }
    field.value = res.data;
    expertsIdsList.value = res.data.emergencyExpertIdList ?? [];
    expertsList.value = res.data.emergencyExpertList ?? [];
    goodsIdsList.value = res.data.emergencyGoodsManageIdList ?? [];
    goodsList.value = res.data.emergencyGoodsManageList ?? [];
    teamsIdsList.value = res.data.emergencyTeamIdList ?? [];
    teamsList.value = res.data.emergencyTeamList ?? [];
    companyList.value = res.data.emergencyPlanCompanyList ?? [];
    deputyHeadList.value = res.data.emergencyPlanDeputyHeadList ?? [];
    othermemberList.value = res.data.emergencyPlanOthermemberList ?? [];
    fileList.value = (res.data.fileList ?? []).map(item => {
      return {
        ...item,
        name: item.fileName,
        url: item.fileUrl
      };
    });
  } else {
    deputyHeadList.value = [{}];
    othermemberList.value = [{}];
    companyList.value = [{}];
  }
});

defineExpose({
  submit: handleSubmit
});
</script>

<style scoped lang="scss">
:deep(.el-upload__tip) {
  display: inline-block;
  margin-left: 16px;
  color: #86909c;
}
</style>
