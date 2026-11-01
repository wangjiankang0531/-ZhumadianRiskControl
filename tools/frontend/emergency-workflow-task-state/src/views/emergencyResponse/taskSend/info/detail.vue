<!-- 可读等价实现；本轮产物来自限定发布文件转换，不宣称由此文件全量构建。 -->
<template>
  <div class="info-title">基础信息</div>
  <MyDetail :field="field" :columns="columns1" />
  <div v-if="!props.workflowTaskId && route.query.judge" class="info-title">处置信息</div>
  <MyForm v-if="!props.workflowTaskId && route.query.judge" ref="form1Ref" :field="fieldJudge" :columns="columns2" />
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyDetail from "@/components/Detail/index.vue";
import { ColumnProps } from "@/components/Detail/interface";
import { updateById, getById } from "@/api/emergencyResponse/taskSend";
// import { useDict } from "@/hooks/useDict";
import { ColumnProps as EditColumnProps } from "@/components/Form/interface";
import MyForm from "@/components/Form/index.vue";

// const { specialHomework } = useDict("safetycode", ["specialHomework"]);

const proxy = import.meta.env.VITE_API_URL + "/serv";

const field = ref<any>({});
const columns1 = ref<ColumnProps[]>([
  {
    prop: "eventNumber",
    label: "事件编号"
  },
  {
    prop: "eventName",
    label: "事件名称"
  },
  {
    prop: "taskName",
    label: "任务名称"
  },
  {
    prop: "taskContent",
    label: "任务内容"
  },
  {
    prop: "executorDept",
    label: "责任部门"
  },
  {
    prop: "executor",
    label: "执行人"
  },
  {
    prop: "acceptanceDept",
    label: "验收部门"
  },
  {
    prop: "dispatchTime",
    label: "下发时间"
  },
  {
    prop: "taskStatus",
    label: "任务状态",
    enumData: [
      { label: "已处置", value: "1" },
      { label: "待处置", value: "0" },
      { label: "处置中", value: "2" }
    ]
  },
  {
    prop: "disposeTime",
    label: "处置时间"
  },
  {
    prop: "feedbackInfo",
    label: "反馈信息"
  },
  {
    prop: "evaluationSum",
    label: "评估总结"
  },
  {
    prop: "uploadUrl",
    label: "附件信息",
    render: () => {
      if (!field.value.uploadUrl) return "--";
      return field.value.uploadUrl.split(";").map(item => {
        return (
          <el-link type="primary" underline={false} href={proxy + item} target="_blank">
            {item.split("/").pop()}
          </el-link>
        );
      });
    }
  }
]);

const form1Ref = ref<InstanceType<typeof MyForm> | null>(null);
const fieldJudge = ref<any>({ taskStatus: "1" });
const columns2 = ref<EditColumnProps[]>([
  {
    el: "date-picker",
    prop: "disposeTime",
    label: "处置时间",
    attrs: { valueFormat: "YYYY-MM-DD HH:mm:ss", type: "datetime" },
    required: true
    // span: 1
  },
  {
    el: "input",
    label: "反馈信息",
    prop: "feedbackInfo",
    required: true,
    attrs: {
      type: "textarea",
      maxlength: 100,
      showWordLimit: true,
      autosize: {
        minRows: 3
      }
    },
    span: 3
  },
  {
    el: "input",
    label: "评估总结",
    prop: "evaluationSum",
    required: true,
    attrs: {
      type: "textarea",
      maxlength: 100,
      showWordLimit: true,
      autosize: {
        minRows: 3
        // maxRows: 3
      }
    },
    span: 3
  }
]);

const props = defineProps({ workflowTaskId: { type: String, default: "" } });
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  const query = props.workflowTaskId
    ? { flowId: props.workflowTaskId }
    : route.query.id ? { id: route.query.id } : null;
  if (!query) return;
  const res = await getById(query);
  field.value = res.data;
});

const submitting = ref(false);
const handleSubmit = async () => {
  if (submitting.value) return false;
  submitting.value = true;
  try {
    fieldJudge.value.id = route.query.id;
    if (!(await form1Ref.value!.validate())) return false;
    await updateById(fieldJudge.value);
    ElMessage.success("操作成功！");
    await router.push({ path: "/emergencyResponse/taskSend" });
    return true;
  } catch (error: any) {
    // Preserve existing server errors; show a fallback for failures without a response.
    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");
    return false;
  } finally {
    submitting.value = false;
  }
};

defineExpose({
  submitting,
  submit: handleSubmit
});
</script>
