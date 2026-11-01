<template>
  <div class="title">流程审核</div>
  <el-form class="audit-form" ref="ruleFormRef" :model="ruleForm" :rules="rules" size="default" label-position="top">
    <el-form-item label="操作" prop="auditType">
      <el-radio-group v-model="ruleForm.auditType" @click="getBranchOptions()">
        <el-radio v-for="(item, index) in auditTypeList" :key="index" :value="item.label">{{ item.label }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="退回节点" v-if="ruleForm.auditType === '退回'">
      <el-select v-model="rejectStep" placeholder="请选择退回节点" :clearable="false" :disabled="isDisabledRejectStep">
        <el-option v-for="item in rejectList1" :label="item.nodeName" :value="item.id" :key="item.id"></el-option>
      </el-select>
    </el-form-item>

    <!-- {{approversProperties.auditBtnText}} -->
    <el-form-item
      label="分支选择"
      prop="branchList"
      v-if="ruleForm.auditType == approversProperties.auditBtnText && branchOptions != null && branchOptions.length > 1"
    >
      <el-select
        v-model="ruleForm.branchList"
        multiple
        placeholder="请选择分支"
        @change="getIsShowUser(null)"
        style="width: 100%"
      >
        <el-option v-for="item in branchOptions" :key="item.nodeId" :label="item.nodeName" :value="item.nodeId" />
      </el-select>
    </el-form-item>
    <el-form-item label="加签类型" prop="freeApproverType" v-if="ruleForm.auditType == '加签'">
      <el-radio-group v-model="ruleForm.freeApproverType">
        <el-radio value="1">审批前</el-radio>
        <el-radio value="2">审批后</el-radio>
      </el-radio-group>
      <div>
        {{
          ruleForm.freeApproverType == "1"
            ? "加签后，流程先经过加签审批人，再由我审批"
            : "审批后加签，即表示同意该申请并增加审批人员"
        }}
      </div>
    </el-form-item>

    <el-form-item
      :label="ruleForm.auditType + '人员'"
      prop="userName"
      v-if="['转审', '委派', '抄送', '普通加签', '加签'].includes(ruleForm.auditType) || isShowUser"
    >
      <el-input
        v-model="ruleForm.userName"
        :placeholder="`请选择${ruleForm.auditType}人员`"
        clearable
        @click="openSession()"
        @clear="handleClear"
      />
    </el-form-item>
    <el-form-item label="处理意见" prop="handleOpinion" v-if="ruleForm.auditType != '暂存'">
      <el-input
        v-model="ruleForm.handleOpinion"
        placeholder="请输入处理意见"
        type="textarea"
        :autosize="{ minRows: 4, maxRows: 6 }"
      />

      <!-- <div class="offen-lang" style="background: #ebebeb; width: 100%">
        <el-dropdown trigger="click" v-if="commonPhrasesList && commonPhrasesList.length > 0">
          <span class="el-dropdown-link" style="height: 30px; line-height: 30px; text-align: center; width: 95px">
            常用意见<el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="item in commonPhrasesList" :key="item?.id" @click="commonPhrases(item)">{{
                item.commonWordsText
              }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-link type="primary" :underline="false" @click="handleCommonPhrasesEdit">常用意见维护</el-link>
      </div> -->
    </el-form-item>
    <!-- <el-form-item :label="['转审', '委派', '抄送', '普通加签', '加签'].includes(ruleForm.auditType) ? ruleForm.auditType + '附件' : '审批附件'"
      prop="handleOpinion" v-if="ruleForm.auditType != '暂存'">
      <el-upload v-model:file-list="fileList" class="upload-demo"
        action="https://run.mocky.io/v3/9d059bf9-4660-45f2-925d-ce80ad6c4d15" multiple :on-preview="handlePreview"
        :on-remove="handleRemove" :before-remove="beforeRemove" :limit="3" :on-exceed="handleExceed">
        <el-button type="primary">Click to upload</el-button>
        <template #tip>
          <div class="el-upload__tip">
            jpg/png files with a size less than 500KB.
          </div>
        </template>
</el-upload>
</el-form-item> -->
    <el-form-item>
      <el-button type="primary" :loading="isSubmit" :disabled="isSubmit" @click="submitForm(ruleFormRef)"> {{ outcomeUncertain ? "核对提交结果" : "提交" }} </el-button>
      <el-button @click="resetForm(ruleFormRef)">取消</el-button>
    </el-form-item>
  </el-form>
  <!-- <el-descriptions v-if="isOpen" :column="1" direction="vertical" class="audit-detail">
    <el-descriptions-item label="当前处理人">{{ processor.current }}</el-descriptions-item>
    <el-descriptions-item label="已处理人">{{ processor.processedBy }}</el-descriptions-item>
  </el-descriptions>
  <div class="audit-more" @click="isOpen = !isOpen">
    <el-icon v-if="!isOpen">
      <ArrowDown />
    </el-icon>
    <el-icon v-else>
      <ArrowUp />
    </el-icon>
    {{ !isOpen ? "展开" : "收起" }}审核选项
  </div> -->
  <userSelect ref="userSelectRef" @checkData="checkData" />
</template>

<script lang="ts" setup>
import { ArrowDown, ArrowUp } from "@element-plus/icons-vue";
import userSelect from "../../user-select/index.vue";

import { reactive, ref, computed, watch, onMounted } from "vue";
import {
  getCommonPhrases,
  getBranchList,
  rejectList,
  withdRaw,
  audit,
  transfer,
  saveAudit,
  reject,
  freeApprover,
  invoke,
  multiAdd,
  taskCancel
} from "@/api/workFlow";
import { useRoute } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useDialog } from "../../hooks/useDialog.ts";

defineOptions({
  name: "AuditForm"
});
const isOpen = ref(false);
interface RuleForm {
  userName: string;
  auditType: string;
  handleOpinion: string;
  freeApproverUserId?: string | number;
  freeApproverType?: string;
  branchList: string[];
}

const props = defineProps({
  type: {
    type: String
  },
  approversProperties: {
    type: Object,
    default: () => ({})
  },
  status: {
    type: [String, Number]
  },
  formData: {
    type: Object,
    default: () => ({})
  },
  id: {
    type: String
  },
  flowId: {
    type: String
  },
  flowTaskNodeList: {
    type: Array,
    default: () => []
  },
  flowTaskOperatorRecordList: {
    type: Array,
    default: () => []
  },
  reconcileOutcome: { type: Function },
  isEnablePrepositionCancel: {
    type: Boolean,
    default: false
  }
});

onMounted(async () => {
  getCommonPhrases1();
  getRejectList();
});

const commonPhrasesList = ref<any[]>([]);
function commonPhrases(val) {
  ruleForm.handleOpinion = val.commonWordsText;
}

const getCommonPhrases1 = async () => {
  const res = await getCommonPhrases();
  commonPhrasesList.value = res.list;
};

const handleCommonPhrasesEdit = () => {
  useDialog(
    "components/workflow/components/commonPhrases.vue",
    {},
    {
      save: () => {
        getCommonPhrases1();
      }
    }
  );
};

const branchType = ref("1");
function getBranchOptions() {
  if (
    ruleForm.auditType === props.approversProperties.auditBtnText &&
    (branchOptions.value === undefined || branchOptions.value === null || branchOptions.value.length === 0)
  ) {
    let params = {
      flowId: flowId,
      id: id,
      formData: {
        flowId,
        id: id,
        ...props.formData
      }
    };
    getBranchList(id as string, params).then((res: any) => {
      if (res.list != null && res.list.length > 0) {
        branchOptions.value = res.list;
      } else {
        branchOptions.value = [];
      }

      branchType.value = res.type;
      if (branchOptions.value.length === 1) {
        getIsShowUser([branchOptions.value[0].nodeId]);
      }
    });
  }
}
const isShowUser = ref(false);
const branchNodeId = ref("");
function getIsShowUser(branchList) {
  if (branchList === undefined || branchList === null || branchList.length === 0) {
    branchList = ruleForm.branchList;
  }
  if (branchList !== undefined && branchList != null && branchList.length > 0) {
    let flag = false;
    for (let index = 0; index < branchList.length; index++) {
      const item = branchList[index];
      branchOptions.value.find((branch: any) => {
        if (branch.nodeId === item) {
          if (branch.isCandidates) {
            branchNodeId.value = branch.nodeId;
            flag = true;
            return;
          }
        }
      });
      if (flag) {
        break;
      }
    }
    isShowUser.value = flag;
  }
}
const route = useRoute();

const ruleFormRef = ref<FormInstance>();
const ruleForm = reactive<RuleForm>({
  userName: "",
  auditType: "",
  handleOpinion: "",
  freeApproverUserId: "",
  freeApproverType: "1",
  branchList: []
});
const branchOptions = ref<any[]>([]);

const rules = reactive<FormRules<RuleForm>>({
  userName: [{ required: true, message: "请选择人员", trigger: "blur" }],
  auditType: [
    {
      required: true,
      message: "请选择操作类型",
      trigger: "change"
    }
  ],
  branchList: [{ required: true, message: "请选择人员", trigger: "change" }]
  // handleOpinion: [
  //   { required: true, message: '请输入处理意见', trigger: 'blur' },
  // ],
});

const emit = defineEmits(["submit", "cancel", "prepositionCancel"]);

const id = props.id ?? route.query.id;
const flowId = props.flowId ?? route.query.flowId;

const rejectList1 = ref<any[]>([]);
const rejectStep = ref("");
const isDisabledRejectStep = ref(true);

// 获取退回节点list
const getRejectList = async () => {
  if (!id || props.type != "待办事宜") return;
  // 查询需退回的节点
  const res = await rejectList(id as string);
  const list = res.list || [];
  const flowTaskRecordList = props.flowTaskOperatorRecordList;

  // 如果list 长度大于 1 表示自选审批节点 设置可选择退回节点 等于 1 为 上级审批节点或者流程发起节点 不可选择
  if (list.length && list.length === 1) {
    rejectStep.value = list[0].id;
    rejectList1.value = list;
  } else if (list.length && list.length > 1) {
    rejectStep.value = list[0].id;
    // 设置退回节点可选择
    isDisabledRejectStep.value = false;
    // 获取当前所在节点
    const nowNode = flowTaskRecordList.find((item: any) => item.handleStatus === 18) || ({} as any);
    // 获取已经过的节点并去重
    const nodeCodeList = [
      ...new Set(flowTaskRecordList.filter((item: any) => item.nodeCode !== nowNode.nodeCode).map((item: any) => item.nodeCode))
    ];
    // 设置 退回的 选项options
    rejectList1.value = list.filter(item => nodeCodeList.includes(item.id));
  }
};

const getProcessor = (arr, type) => {
  let str = "";
  if (type == "当前处理人") {
    const list = arr.map((item: any) => item.userName);
    str = [...new Set(list)].filter(item => item != null).join("、");
  }
  if (type == "已处理人") {
    const list = arr.filter((item: any) => item.type != 2).map((item: any) => item.userName);
    str = [...new Set(list)].filter(item => item != null).join("、");
  }
  return str;
};

const processor = computed(() => {
  const list = props.flowTaskOperatorRecordList.filter((item: any) => item.handleStatus == 18);
  return {
    current: getProcessor(list, "当前处理人"),
    processedBy: getProcessor(props.flowTaskNodeList, "已处理人")
  };
});

const isSubmit = ref(false);
const outcomeUncertain = ref(false);
const reconcileUncertainOutcome = async () => {
  outcomeUncertain.value = true;
  try {
    if (typeof props.reconcileOutcome !== "function") throw new Error("FLOW_STATE_UNCONFIRMED");
    const mayRetry = await props.reconcileOutcome();
    if (mayRetry !== true && mayRetry !== false) throw new Error("FLOW_STATE_UNCONFIRMED");
    outcomeUncertain.value = false;
    if (mayRetry) ElMessage.error("提交失败，请重试");
    else ElMessage.info("流程状态已更新，请查看最新待办和审批记录");
  } catch {
    ElMessage.warning("暂时无法确认提交结果，请先核对流程状态");
  } finally {
    isSubmit.value = false;
  }
};


// 提交
const submitForm = async (formEl: FormInstance | undefined) => {
  if (!formEl || isSubmit.value) return;
  isSubmit.value = true;
  if (outcomeUncertain.value) {
    await reconcileUncertainOutcome();
    return;
  }
  try {
    const valid = await formEl.validate().catch(() => false);
    if (valid) {
      if (ruleForm.handleOpinion === undefined || ruleForm.handleOpinion === null || ruleForm.handleOpinion === "") {
        ruleForm.handleOpinion = ruleForm.auditType;
      }
      let params = JSON.parse(JSON.stringify(ruleForm));
      if (ruleForm.auditType == props.approversProperties.auditBtnText) {
        if (isShowUser.value) {
          params.id = id;
          params.formData = {
            flowId,
            ...props.formData
          };
          params.branchList = ruleForm.branchList;
          params.handleOpinion = ruleForm.handleOpinion;
          params.candidateType = branchType.value;
          params.rejectType = 1;
          params.flowId = flowId;
          params.copyIds = "";
          params.fileList = [];
          params.countersignOver = true;
          params.candidateList = { [branchNodeId.value]: [ruleForm.freeApproverUserId] };
        } else {
          params.id = id;
          params.formData = {
            flowId,
            ...props.formData
          };
          params.fileList = [];
          params.countersignOver = true;
          params.flowId = flowId;
          params.candidateType = 3;
          params.rejectType = 1;
        }
      }
      if (ruleForm.auditType == "退回") {
        // const res = await rejectList(id as string)
        params.flowId = flowId;
        params.id = id;
        params.candidateType = branchType.value; // "1"
        params.rejectType = props.approversProperties.rejectType; // '1'
        params.rejectStep = rejectStep.value;
      }

      if (ruleForm.auditType == "暂存") {
        params.flowId = flowId;
        params.id = id;
        delete params.handleOpinion;
      }

      if (ruleForm.auditType == "加签") {
        params.formData = {
          flowId,
          ...props.formData
        };
      } else {
        delete params.freeApproverType;
      }

      if ([props.approversProperties.auditBtnText, "暂存", "退回", "终止"].includes(ruleForm.auditType)) {
        delete params.freeApproverUserId;
      }

      delete params.userName;
      delete params.auditType;

      params.auditType = ruleForm.auditType;
      if (props.isEnablePrepositionCancel) {
        emit("prepositionCancel", params);
      } else {
        submitPort(params);
      }
    } else {
      isSubmit.value = false;
    }
  } catch (error: any) {
    isSubmit.value = false;
    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");
  }
};

const submitPort = async params => {
  const obj = auditTypeList.value.find(item => item.label == ruleForm.auditType);
  console.log(params, "paramsparamsparamsparams");
  let id = params.id;
  if (route.query.id != undefined && route.query.id != null && route.query.id != "") {
    id = route.query.id;
  }
  if (!id || typeof obj?.api !== "function") {
    isSubmit.value = false;
    return;
  }
  try {
    await obj.api(id as string, params);
    ElMessage.success(ruleForm.auditType + "成功");
    isSubmit.value = false;
    emit("submit", params);
  } catch (error: any) {
    // Preserve the draft until the original service confirms whether this operation is still pending.
    await reconcileUncertainOutcome();
  } finally {
    isSubmit.value = false;
  }
};
const prepositionCancelReceipt = params => {
  submitPort(params);
};

const closeLoading = () => {
  isSubmit.value = false;
};

defineExpose({
  prepositionCancelReceipt,
  closeLoading,
  isSubmit
});

// 取消
const resetForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  formEl.resetFields();
  emit("cancel");
};

// 选择用户
const userSelectRef = ref();
const openSession = () => {
  userSelectRef.value.acceptParams();
};
const checkData = (data: any) => {
  ruleForm.userName = data?.length > 0 ? data[0].fullName : "";
  ruleForm.freeApproverUserId = data?.length > 0 ? data[0].id : "";
};

const handleClear = () => {
  ruleForm.userName = "";
  ruleForm.freeApproverUserId = "";
  userSelectRef.value.selectedData = [];
};

type AuditType = {
  label: string;
  api: (id: string, params: any) => Promise<any>;
};

const auditTypeList = ref<AuditType[]>([]);
watch(
  () => [props.type, props.approversProperties],
  () => {
    const list: AuditType[] = [];
    const properties = props.approversProperties;
    if (props.type == "我发起的") {
      if (props.status == 1 && (properties.hasRevokeBtn || properties.hasRevokeBtn === undefined)) {
        list.push({ label: "撤回", api: withdRaw });
      }
    }
    if (props.type == "待办事宜") {
      if (properties.hasAuditBtn) list.push({ label: props.approversProperties.auditBtnText, api: audit });
      if (properties.hasTransferBtn) list.push({ label: "转审", api: transfer });
      // if (properties.hasSaveBtn) list.push({ label: "暂存", api: saveAudit });
      if (properties.hasRejectBtn) list.push({ label: "退回", api: reject });
      if (properties.hasFreeApproverBtn) list.push({ label: "加签", api: freeApprover });
      // if (properties.hasInvokeBtn) list.push({ label: "委派", api: invoke });
      // if (properties.hasCopyBtn) list.push({ label: "抄送", api: cc });
      // if (properties.hasMultiAddBtn) list.push({ label: "普通加签", api: multiAdd });
      // if (properties.hasTerminationBtn) list.push({ label: "终止", api: taskCancel });
    }
    if (list.length > 0) {
      ruleForm.auditType = list[0].label;
      if (ruleForm.auditType === props.approversProperties.auditBtnText) {
        getBranchOptions();
      }
    }
    auditTypeList.value = list;
  },
  {
    immediate: true
  }
);
</script>

<style lang="scss" scoped>
.title {
  font-size: 16px;
  font-weight: 500;
  color: #333333;
  line-height: 22px;
  margin-bottom: 16px;
}

.audit-more {
  text-align: center;
  font-size: 14px;
  font-weight: 400;
  color: #333333;
  line-height: 20px;
  margin-top: 16px;
  cursor: pointer;
}

.audit-form,
.audit-detail {
  :deep(.el-form-item__label) {
    font-size: 14px;
    font-weight: 500;
    color: #333333;
  }

  :deep(.el-input__wrapper) {
    box-shadow: none;
  }

  :deep(.el-textarea__inner) {
    box-shadow: none;
  }
}

:deep(.el-radio) {
  border-radius: 16px;
  border: 1px solid #cccccc;
  width: 102px;
  padding-left: 16px;
  margin-bottom: 12px;
  margin-right: 8px;
  box-sizing: border-box;

  &:nth-child(4n) {
    margin-right: 0;
  }

  &.is-checked {
    background: #eef3ff;
    border-radius: 16px;
    border: 1px solid #165dff;
  }
}

.offen-lang {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .el-link {
    text-decoration: none;
    margin: 0 10px;
  }
}
</style>
