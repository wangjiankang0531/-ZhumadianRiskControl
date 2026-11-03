<template>
  <el-alert v-if="detailView.error" :title="detailView.error" type="error" :closable="false">
    <el-button link type="primary" @click="reloadDetail">重试</el-button>
  </el-alert>
  <div v-if="detailView.loading" role="status">正在加载详情…</div>
  <div v-if="detailView.data">
  <div class="info-title">基础信息</div>
  <MyDetail :field="field" :columns="columns" />
  <div class="info-title">成员信息</div>
  <FormList title="副指挥长" v-model:list="deputyHeadList" is-view />
  <FormList title="其他成员" v-model:list="othermemberList" is-view />
  <FormList title="参与单位" v-model:list="companyList" is-view />
  <div class="info-title">应急信息</div>
  <el-tabs v-model="activeName">
    <el-tab-pane label="应急物资" name="first">
      <GoodsList v-model:list="goodsList" is-view />
    </el-tab-pane>
    <el-tab-pane label="应急队伍" name="second">
      <TeamsList v-model:list="teamsList" is-view />
    </el-tab-pane>
    <el-tab-pane label="应急专家" name="third">
      <ExpertsList v-model:list="expertsList" is-view />
    </el-tab-pane>
  </el-tabs>
  </div>
</template>

<script setup lang="tsx">
import { ref, watch, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import GoodsList from "../components/goodsList.vue";
import TeamsList from "../components/teamsList.vue";
import ExpertsList from "../components/expertsList.vue";
import MyDetail from "@/components/Detail/index.vue";
import { EmergencyReadonlyDetail, emptyDetailView } from "@/components/Detail/OriginalEmergencyReadonlyDetail";
import FormList from "../components/formList.vue";
import { ColumnProps } from "@/components/Detail/interface";
import { getById } from "@/api/emergencyPlans/structured";
import { useDict } from "@/hooks/useDict";

const proxy = import.meta.env.VITE_API_URL + "/serv";

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

const { emergencyPlanType, eventType } = useDict("safetycode", ["emergencyPlanType", "eventType"]);

const fileList = ref<any>([]);

const detailView = ref(emptyDetailView());
const field = ref<any>({});
const columns = ref<ColumnProps[]>([
  { label: "应急预案名称", prop: "emergencyPlanName" },
  { label: "应急预案类型", prop: "emergencyPlanType", enumData: emergencyPlanType },
  { label: "事故类型", prop: "accidentType", enumData: eventType },
  { label: "事故区域", prop: "eventLocation" },

  { label: "指挥长", prop: "commanderName" },
  { label: "指挥长电话", prop: "commanderPhone" },
  {
    label: "是否备案",
    prop: "isFilings",
    enumData: [
      { label: "是", value: "1" },
      { label: "否", value: "0" }
    ]
  },
  {
    prop: "disposalMeasures",
    label: "处置措施",
    span: 3,
    attrs: {
      type: "textarea",
      maxlength: 200,
      showWordLimit: true,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    }
  },
  {
    prop: "url",
    label: "附件",
    render: () => {
      if (!fileList.value.length) return "--";
      return (
        <div>
          {fileList.value.map(item => {
            return (
              <el-link style="display:block" type="primary" underline={false} href={proxy + item.fileUrl} target="_blank">
                {item.fileName}
              </el-link>
            );
          })}
        </div>
      );
    }
  }
]);

const route = useRoute();


const detailLoader = new EmergencyReadonlyDetail("plan", getById, value => {
  detailView.value = value;
  field.value = value.data ?? {};
  expertsIdsList.value = value.data?.emergencyExpertIdList ?? [];
  expertsList.value = value.data?.emergencyExpertList ?? [];
  goodsIdsList.value = value.data?.emergencyGoodsManageIdList ?? [];
  goodsList.value = value.data?.emergencyGoodsManageList ?? [];
  teamsIdsList.value = value.data?.emergencyTeamIdList ?? [];
  teamsList.value = value.data?.emergencyTeamList ?? [];
  companyList.value = value.data?.emergencyPlanCompanyList ?? [];
  deputyHeadList.value = value.data?.emergencyPlanDeputyHeadList ?? [];
  othermemberList.value = value.data?.emergencyPlanOthermemberList ?? [];
  fileList.value = value.data?.fileList ?? [];
});
const reloadDetail = () => detailLoader.load(route.query.id);
watch(() => route.query.id, reloadDetail, { immediate: true });
onBeforeUnmount(() => detailLoader.dispose());
</script>

<style scoped></style>
