<template>
  <el-dialog v-model="dialogVisible" width="60%" title="信息选择">
    <div class="no-card">
      <ProTable
        ref="proTable"
        height="450px"
        :tool-button="false"
        :columns="columns"
        :request-api="getTableList"
        :search-col="2"
      />
    </div>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleCheck">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage /*removeById, exportExcel*/ } from "@/api/emergencyResponse/response";
import { ElMessage } from "element-plus";
// const { eventType,eventLevel,reportType } = useDict("safetycode", ["eventType","eventLevel","reportType"]);

const dialogVisible = ref(false);

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 表格配置项
const columns: ColumnProps[] = [
  { type: "radio", label: "单选", width: 80 },
  {
    prop: "eventNumber",
    label: "事件编号",
    align: "left"
  },
  {
    prop: "eventName",
    label: "事件名称",
    align: "left",
    search: {
      el: "input"
    }
  },
  {
    prop: "eventContent",
    label: "事件内容",
    align: "left",
    search: {
      el: "input"
    }
  }
  // {
  //   prop: "eventType",
  //   label: "事件类型",
  //   enum: eventType,
  //   search: {
  //     el: "select"
  //   },
  //   tag: true
  // }
];
const getTableList = params => {
  let newParams = JSON.parse(JSON.stringify(params));
  newParams.researchStatus = "1";
  return getPage(newParams);
};
const emit = defineEmits<{
  check: [val: any];
}>();

const handleCheck = () => {
  const nowRow = proTable.value?.tableData.find(item => item.id == proTable.value?.radio);
  // const { id, name, phoneNumber,jobTitle,gender,age,personDept } = nowRow;
  if (!nowRow) {
    ElMessage.warning("请先选择一条事件信息");
    return;
  }
  emit("check", nowRow);
  dialogVisible.value = false;
};

// 接收父组件传过来的参数
const acceptParams = async () => {
  dialogVisible.value = true;
  // nextTick(() => (proTable.value!.radio = val));
};

defineExpose({
  acceptParams
});
</script>

<style lang="scss" scoped>
.title {
  font-family: DIN;
  font-size: 16px;
  font-weight: 600;
  color: initial;
}
.card {
  border-radius: 0;
}
</style>
