<template>
  <div class="layout-padding">
    <auditHead head-name="工作流"> </auditHead>
    <el-scrollbar>
      <div class="content">
        <div class="left-content">
          <div class="form-content">
            <!-- <businessForm :componentUrl="'/intelligentInspection/ledger/info/detail.vue'"></businessForm> -->
            <businessForm :key="workflowTaskId + ':' + businessRevision" :component-url="flowFormInfo.urlAddress" :workflow-task-id="workflowTaskId"></businessForm>
          </div>
          <div class="form-content">
            <div class="other">
              <el-tabs v-model="activeName">
                <el-tab-pane label="审批记录" name="first">
                  <auditRecord :data="flowWorkData" />
                </el-tab-pane>
                <el-tab-pane label="流程状态" name="second">
                  <auditState :data="flowWorkData" />
                </el-tab-pane>
                <el-tab-pane label="流程图" name="third">
                  <preview :data="flowTemplateJson" />
                </el-tab-pane>
                <el-tab-pane label="基本信息" name="fourth">
                  <baseInfo :data="baseInfoFrom" />
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
        </div>
        <div class="audit-content" v-if="auditFormIsShow">
          <!-- {{ formData }} -->
          <auditForm
            ref="auditFormRef"
            :type="props.auditType"
            :approvers-properties="approversProperties"
            :status="status"
            :flow-task-node-list="flowTaskNodeList"
            :flow-task-operator-record-list="flowWorkData"
            :form-data="formData"
            :reconcile-outcome="reconcileOutcome"
            @submit="submit"
            @preposition-cancel="prepositionCancel"
            :is-enable-preposition-cancel="true"
          />
        </div>
        <div class="audit-content" v-else-if="pendingCheckMessage" role="status" aria-live="polite">
          <el-alert :title="pendingCheckMessage" type="info" :closable="false" show-icon />
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>
<script setup lang="ts">
import auditRecord from "./components/auditRecord.vue";
import auditState from "./components/auditState.vue";
import baseInfo from "./components/baseInfo.vue";
import auditForm from "./components/auditForm.vue";
import businessForm from "./components/businessForm.vue";
import auditHead from "./components/auditHead.vue";
import preview from "./components/Process/index.vue";
// import { ProcessData } from "./components/Process/FlowCard/Process.ts"
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { flowInfo, flowBefore1 } from "@/api/workFlow";
import { TimestampToDate } from "./components/formatTime";
import { usePageTab } from "@/utils/use-page-tab";

const { removePageTab } = usePageTab();

defineOptions({
  name: "WorkFlowDetails"
});
// const ProcessObj = ref({})
const emit = defineEmits(["submit"]);
// 定义父组件传过来的值
const props = defineProps({
  // 表单名称
  auditType: {
    type: String,
    default: () => ""
  }
});
// 提交回调函数
// const router = useRouter();
function submit(params) {
  emit("submit", params);
  removePageTab({ key: route.path, active: route.path });
  // router.go(-1);
}
const activeName = ref("first");

const route = useRoute();
const auditFormRef = ref();
const prepositionCancel = params => {
  // console.log(1111111)
  //   // 设置定时器等待 5 秒
  //    setTimeout(() => {
  //   // 执行你想要的操作
  //   console.log('5 秒已过');
  //   // 例如，可以更新数据或导航到另一个组件

  // auditFormRef.value?.closeLoading();
  // }, 5000);
  // 业务处理
  // 回调提交方法
  auditFormRef.value?.prepositionCancelReceipt(params);
};

// const flowWorkData = ref([]); //审批记录
// const flowWorkData = ref([]); //审批记录
// const flowWorkData = ref([]); //审批记录
const flowWorkData = ref([]); //审批记录

const approversProperties = ref({} as any);
const status = ref("");
const flowTaskNodeList = ref([]);
const flowFormInfo = ref({} as any);
const workflowTaskId = ref("");
const businessRevision = ref(0);
const flowTemplateJson = ref({});
const auditFormIsShow = ref(false);
const pendingCheckMessage = ref("");
let detailLoadVersion = 0;
const formData = ref({});
const baseInfoFrom = ref({
  userName: "",
  creatorTime: "",
  flowTemplateInfoFullName: "",
  flowCategory: "",
  status: "",
  flowFormInfoFullName: ""
} as any);

const formatTemplateJSON = (nodeList, jsonData) => {
  let temp = JSON.parse(jsonData);

  for (let i = 0; i < nodeList.length; i++) {
    const nodeItem = nodeList[i];
    nodeItem.userName = nodeItem.userName?.split("/")[0];
    const loop = data => {
      if (Array.isArray(data)) data.forEach(d => loop(d));
      if (data.nodeId === nodeItem.nodeCode) {
        if (nodeItem.type == 0) data.state = "state-past";
        if (nodeItem.type == 1) data.state = "state-curr";
        if (nodeItem.nodeType === "approver" || nodeItem.nodeType === "start" || nodeItem.nodeType === "subFlow")
          data.content = nodeItem.userName;
        return;
      }
      if (data.conditionNodes && Array.isArray(data.conditionNodes)) loop(data.conditionNodes);
      if (data.childNode) loop(data.childNode);
    };

    loop(temp);
  }
  return temp;
};

// 获取工作流信息
const readWorkData = async () => {
  //调取工作流接口  拿到接口返回的flowTaskOperatorRecordList
  let params = {} as any;
  if (props.auditType === "我发起的" || props.auditType === "流程监控") {
    params = {
      taskOperatorId: route.query.id,
      flowId: route.query.flowId
    };
  } else {
    params = {
      taskNodeId: route.query.id,
      taskOperatorId: route.query.id,
      flowId: route.query.flowId
    };
  }
  return await flowInfo(route.query.id as string, params);
};
const applyWorkData = (res: any) => {
  initialPendingSignature.value = pendingSignature(res);
  businessRevision.value++;
  const records = Array.isArray(res.flowTaskOperatorRecordList) ? res.flowTaskOperatorRecordList : [];
  // Native status 2 is the initial submission; select before formatting timestamps.
  const initiatorRecord = records.filter(item => Number(item.handleStatus) === 2)
    .sort((a, b) => Number(a.creatorTime || 0) - Number(b.creatorTime || 0))[0];
  flowWorkData.value = [...records].reverse();
  workflowTaskId.value = String(res.flowTaskInfo?.id || "");
  flowFormInfo.value = res.flowFormInfo || {};
  flowTemplateJson.value = formatTemplateJSON(res.flowTaskNodeList, res.flowTemplateInfo.flowTemplateJson);
  formData.value = res.formData || {};
  flowWorkData.value.forEach((item: any) => {
    if (item.handleTime) {
      let timestamp = Number(item.handleTime);
      item.handleTime = TimestampToDate(timestamp);
    }
    if (item.creatorTime) {
      let timestamp = Number(item.creatorTime);
      item.creatorTime = TimestampToDate(timestamp);
    }
    if (item.userName) {
      let name = item.userName.split("/");
      item.userName = name[0];
    }
  });
  approversProperties.value = res.approversProperties;
  status.value = res.flowTaskInfo.status;
  flowTaskNodeList.value = res.flowTaskNodeList;

  if (props.auditType === "我发起的") {
    if (
      !(status.value == "1" && (approversProperties.value.hasRevokeBtn || approversProperties.value.hasRevokeBtn === undefined))
    ) {
      auditFormIsShow.value = false;
    }
  } else if (props.auditType === "我已处理" || props.auditType === "流程监控") {
    auditFormIsShow.value = false;
  }
  if (initiatorRecord) {
    const item: any = initiatorRecord;
    // 发起人身份
    baseInfoFrom.value.userName = item.userName;
    // 创建时间
    baseInfoFrom.value.creatorTime = item.creatorTime;
  }
  // 申请部门
  // 所属模板
  baseInfoFrom.value.flowTemplateInfoFullName = res.flowTemplateInfo.fullName;
  // 系统来源
  baseInfoFrom.value.flowCategory = res.flowTaskInfo.flowCategory; // 数据字典
  // 流程编号
  // 流程状态
  baseInfoFrom.value.status = res.flowTaskInfo.status; // 数据字典
  // 标签
  // 当前表单
  baseInfoFrom.value.flowFormInfoFullName = res.flowFormInfo.fullName;
};

const pendingSignature = (data: any) => (Array.isArray(data.flowTaskOperatorRecordList) ? data.flowTaskOperatorRecordList : [])
  .filter((item: any) => Number(item.handleStatus) === 18)
  .map((item: any) => [item.taskOperatorId, item.taskNodeId, item.handleId, item.operatorId, item.nodeCode].map(value => String(value ?? "")).join("|"))
  .sort().join(";");
const initialPendingSignature = ref("");
const hasOwnPendingFlow = async (taskId: string, operatorId?: string) => {
  const deadline = Date.now() + 15000;
  let currentPage = 1, seen = 0;
  for (;;) {
    const result: any = await flowBefore1({ currentPage, pageSize: 100 });
    const list = result?.list, total = Number(result?.pagination?.total);
    if (!Array.isArray(list) || !Number.isFinite(total) || total < 0) throw new Error("PENDING_STATE_UNCONFIRMED");
    if (list.some((item: any) => (String(item.id) === taskId || String(item.processInstanceId) === taskId) && (!operatorId || String(item.id) === operatorId))) return true;
    seen += list.length;
    if (seen >= total) return false;
    if (!list.length || Date.now() >= deadline) throw new Error("PENDING_STATE_UNCONFIRMED");
    currentPage++;
  }
};
const reconcileOutcome = async () => {
  const data: any = await readWorkData();
  if (!data?.flowTaskInfo?.id || String(data.flowTaskInfo.id) !== workflowTaskId.value || data.flowTaskInfo.status === undefined || data.flowTaskInfo.status === null) throw new Error("FLOW_STATE_UNCONFIRMED");
  const running = String(data.flowTaskInfo.status) === "1";
  if (props.auditType === "待办事宜" && running) {
    const pending = await hasOwnPendingFlow(String(data.flowTaskInfo.id));
    const signature = pendingSignature(data);
    if (pending && signature && signature === initialPendingSignature.value) return true;
  } else if (props.auditType === "我发起的" && running && data.approversProperties?.hasRevokeBtn !== false) {
    const signature = pendingSignature(data);
    if (signature && signature === initialPendingSignature.value) return true;
  }
  applyWorkData(data);
  auditFormIsShow.value = false;
  return false;
};
const getWorkData = async () => {
  const version = ++detailLoadVersion;
  auditFormIsShow.value = false;
  pendingCheckMessage.value = "";
  try {
    const data: any = await readWorkData();
    if (version !== detailLoadVersion) return;
    applyWorkData(data);
    const running = String(data.flowTaskInfo?.status) === "1";
    if (props.auditType === "待办事宜") {
      const taskId = String(data.flowTaskInfo?.id || "");
      const operatorId = typeof route.query.id === "string" ? route.query.id : "";
      if (!running || !taskId || !operatorId) {
        pendingCheckMessage.value = "当前任务暂不可审批，请在待办列表中查看最新状态";
        return;
      }
      pendingCheckMessage.value = "正在核实待办状态";
      const pending = await hasOwnPendingFlow(taskId, operatorId);
      if (version !== detailLoadVersion) return;
      auditFormIsShow.value = pending;
      pendingCheckMessage.value = pending ? "" : "当前任务暂不可审批，请在待办列表中查看最新状态";
    } else if (props.auditType === "我发起的") {
      auditFormIsShow.value = running && data.approversProperties?.hasRevokeBtn !== false;
    }
  } catch {
    if (version !== detailLoadVersion) return;
    auditFormIsShow.value = false;
    pendingCheckMessage.value = "暂时无法核实待办状态，请刷新后重试";
  }
};
onBeforeUnmount(() => { detailLoadVersion++; });

onMounted(() => {
  getWorkData(); //获取工作流信息
  // ProcessObj.value = ProcessData;
});
</script>

<style lang="scss" scoped>
.layout-padding {
  width: 100%;
  height: 100%;
  background: #f2f3f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  overflow: hidden auto;
  padding: 16px 0 0 16px;
  box-sizing: border-box;
  display: flex;

  .left-content {
    flex: 1;
    height: auto;
    margin-right: 16px;

    .form-content {
      width: 100%;
      // height: 500px;
      background: #ffffff;
      box-shadow: 0px 2px 4px 0px rgba(218, 218, 218, 0.5);
      padding: 16px;
      box-sizing: border-box;
      margin-bottom: 16px;
      box-sizing: border-box;
    }
  }

  .audit-content {
    width: 25%;
    height: 100%;
    background: #ffffff;
    box-shadow: 0px 2px 4px 0px rgba(218, 218, 218, 0.5);
    padding: 16px;
    box-sizing: border-box;
    margin-bottom: 16px;
  }
}

.flex-dea {
  display: flex;
  align-items: center;
}

.mr12 {
  margin-right: 12px;
}
</style>
