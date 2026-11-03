<template>
  <el-dialog
    v-model="isVisible"
    width="68%"
    title="新增演练记录"
    :before-close="closeDialog"
    style="margin-top: 80px; padding: 24px"
  >
    <el-scrollbar height="600px">
      <div class="info-title">基础信息</div>
      <MyForm ref="formRef" :field="field" :columns="columns" />
    </el-scrollbar>

    <template #footer>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
      <el-button @click="closeDialog">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="tsx">
import { ref } from "vue";
import UploadFiles from "@/components/Upload/Files.vue";
import MyForm from "@/components/Form/index.vue";
import { ElMessage } from "element-plus";
import { ColumnProps } from "@/components/Form/interface";
import CheckPerson from "./CheckPerson/index.vue";
import { useDict } from "@/hooks/useDict";
import { save } from "@/api/emergencyPlans/exercise";

import { useOrgTree } from "@/hooks/useOrgTree";
const { orgTree } = useOrgTree();

const { exerciseTypeData } = useDict("safetycode", ["exerciseTypeData"]);
const field = ref<any>({});
const isVisible = ref(true);

const props = defineProps({
  emergencyPlanId: String
});

const emit = defineEmits(["close", "add"]);
const closeDialog = () => {
  emit("close");
};

const formRef = ref<InstanceType<typeof MyForm> | null>(null);
const handleSubmit = async () => {
  if (attachmentSubmitting.value || !attachmentRef.value?.ensureReady()) return false;
  attachmentSubmitting.value = true;
  try {
  const valid = await formRef.value!.validate();
  if (!valid) return;
  if (!attachmentRef.value?.ensureReady()) return false;

  const params = {
    ...field.value,
    emergencyPlanId: props.emergencyPlanId,
    fileList: fileList.value.map(item => ({ fileName: item.name, fileUrl: item.url })),
    participants: (field.value.personIds ?? []).join(",")
  };
  let response: any;
  try {
    response = await save(params);
  } catch {
    return false;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("操作未完成，请保留当前内容，核对事件、处置或演练记录状态后重试。");
    return false;
  }
  ElMessage.success("新增成功");
  emit("add");
  } finally { attachmentSubmitting.value = false; }
};
// const orgId = ref("");
const attachmentRef = ref<InstanceType<typeof UploadFiles> | null>(null);
const attachmentSubmitting = ref(false);
const fileList = ref<any>([]);
const columns = ref<ColumnProps[]>([
  {
    el: "input",
    label: "演练地点",
    prop: "exerciseLocation",
    required: true
  },
  {
    el: "select",
    label: "组织部门",
    prop: "organizeDepartment",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.organizeDepartment}
          data={orgTree.value}
          check-strictly={true}
          clearable={true}
          filterable={true}
          props={{
            label: "fullName",
            value: "id"
          }}
        />
      );
    }
  },
  {
    el: "input",
    label: "总指挥",
    prop: "commanderChief"
  },
  {
    el: "date-picker",
    label: "演练时间",
    prop: "exerciseTime",
    attrs: {
      type: "date",
      valueFormat: "YYYY-MM-DD" //THH:mm:ss
    }
  },
  {
    el: "select",
    label: "演练类别",
    prop: "exerciseType",
    enumData: exerciseTypeData
  },
  {
    el: "select",
    label: "配合单位",
    prop: "cooperatingUnit",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.cooperatingUnit}
          data={orgTree.value}
          check-strictly={true}
          clearable={true}
          filterable={true}
          props={{
            label: "fullName",
            value: "id"
          }}
        />
      );
    }
  },
  {
    prop: "personIds",
    label: "参加部门及人员",
    render: () => (
      <CheckPerson
        v-model={field.value.personIds}
        orgId={
          field.value.organizeDepartment && field.value.cooperatingUnit
            ? field.value.organizeDepartment + "," + field.value.cooperatingUnit
            : field.value.organizeDepartment
              ? field.value.organizeDepartment
              : field.value.cooperatingUnit
                ? field.value.cooperatingUnit
                : ""
        }
        isView={false}
      />
    ),
    span: 3
  },
  {
    el: "input",
    prop: "exerciseDevice",
    label: "演练设备及器材",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    el: "input",
    prop: "exerciseDescribe",
    label: "演练内容及过程描述",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    el: "input",
    prop: "exerciseSpecialSituation",
    label: "演练过程中特殊处理情况",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    el: "input",
    prop: "problemsAndmeasures",
    label: "问题及改进措施",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },

  {
    prop: "url",
    label: "附件",
    render: () => <UploadFiles ref={attachmentRef} v-model:fileList={fileList.value} disabled={attachmentSubmitting.value} />
  }
]);
</script>
<style scoped lang="scss">
:deep(.el-upload__tip) {
  display: inline-block;
  margin-left: 16px;
  color: #86909c;
}
</style>
