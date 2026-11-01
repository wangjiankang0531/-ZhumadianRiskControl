<!-- 等价审阅稿；实际产物来自限定204发布文件转换，并非全量源码重建。 -->
<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns1">
    <template #uploadUrl>
      <UploadFiles v-model:fileList="fileList" />
    </template>
  </MyForm>
  <List ref="listRef" @check="listCheck" />
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
// import UploadImg from "@/components/Upload/Img.vue";
import { save, updateById, getById } from "@/api/emergencyResponse/taskSend";
// import { useDict } from "@/hooks/useDict";
import { useOrgTree } from "@/hooks/useOrgTree";
import UploadFiles from "@/components/Upload/Files.vue";
const { orgTree } = useOrgTree();
import List from "./list.vue";

const listRef = ref<InstanceType<typeof List> | null>(null);
const listCheck = (data: any) => {
  field.value.eventNumber = data.eventNumber;
  field.value.eventName = data.eventName;
  field.value.infoId = data.id;
};

const fileList = ref<any>([]);

// const { specialHomework } = useDict("safetycode", ["specialHomework"]);
const handleClick = () => {
  listRef.value!.acceptParams();
};

const field = ref<any>({});

const columns1 = ref<ColumnProps[]>([
  {
    el: "input",
    prop: "eventNumber",
    label: "事件编号",
    required: true,
    render: () => {
      return <el-input v-model={field.value.eventNumber} placeholder="请输入" readonly onClick={handleClick} />;
    }
  },
  {
    el: "input",
    prop: "eventName",
    label: "事件名称",
    required: true,
    attrs: { disabled: true }
  },
  {
    el: "input",
    prop: "taskName",
    label: "任务名称",
    required: true
  },
  {
    el: "input",
    prop: "taskContent",
    label: "任务内容",
    required: true
  },

  // {
  //   el: "input",
  //   prop: "executorDept",
  //   label: "责任部门",
  // },
  {
    prop: "executorDept",
    label: "责任部门",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.executorDept}
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
    prop: "executor",
    label: "执行人"
  },
  // {
  //   el: "input",
  //   prop: "acceptanceDept",
  //   label: "验收部门",
  // },
  {
    prop: "acceptanceDept",
    label: "验收部门",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.acceptanceDept}
          data={orgTree.value}
          check-strictly={true}
          props={{
            label: "fullName",
            value: "fullName"
          }}
        />
      );
    }
  },
  {
    el: "date-picker",
    prop: "dispatchTime",
    label: "下发时间",
    attrs: { valueFormat: "YYYY-MM-DD HH:mm:ss", type: "datetime" }
  },
  // {
  //   el: "select",
  //   prop: "taskStatus",
  //   label: "任务状态",
  //   enumData:[
  //     { label: "已处置", value: "1" },
  //     { label: "待处置", value: "0" }
  //   ]
  // },
  {
    prop: "uploadUrl",
    label: "附件信息"
  }
]);

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

const submitting = ref(false);
const handleSubmit = async () => {
  if (submitting.value) return false;
  submitting.value = true;
  try {
    const api = route.query.type == "edit" ? updateById : save;
    const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
    if (!(await formRef.value!.validate())) return false;
    const uploadUrl = fileList.value.map(item => item.url).join(";");
    const result = await api({ ...field.value, uploadUrl });
    if (result.data !== true) {
      ElMessage.error("任务未保存，请刷新核对后重试");
      return false;
    }
    ElMessage.success(message);
    await router.push({ path: "/emergencyResponse/taskSend" });
    return true;
  } catch (error: any) {
    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");
    return false;
  } finally {
    submitting.value = false;
  }
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    const res: any = await getById({ id: route.query.id });
    field.value = res.data;

    fileList.value = res.data.uploadUrl
      ? res.data.uploadUrl.split(";").map((item: string, index: number) => ({
          uid: index,
          name: item.split("/").pop(),
          url: item
        }))
      : [];
  }
});

defineExpose({
  submitting,
  submit: handleSubmit
});
</script>
