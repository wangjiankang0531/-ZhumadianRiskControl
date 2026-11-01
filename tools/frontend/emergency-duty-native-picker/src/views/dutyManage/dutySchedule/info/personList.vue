<template>
  <el-dialog v-model="dialogVisible" width="40%" title="选择值班人员">
    <div class="table-box no-card">
      <ProTable
        ref="proTable"
        height="400px"
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
import { getPage } from "@/api/dutyManage/dutyPersonnel";
import { ElMessage } from "element-plus";

const dialogVisible = ref(false);

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 表格配置项
const columns: ColumnProps[] = [
  { type: "radio", label: "单选", width: 80 },
  { prop: "name", label: "姓名", search: { el: "input" } },
  { prop: "phoneNumber", label: "联系电话" }
];
const getTableList = params => {
  let newParams = JSON.parse(JSON.stringify(params));
  return getPage(newParams);
};
const emit = defineEmits<{
  check: [val: any];
}>();

const handleCheck = () => {
  const nowRow = proTable.value?.tableData.find(item => item.id == proTable.value?.radio);
  if (!nowRow) {
    ElMessage.warning("请选择值班人员");
    return;
  }
  const { id, name, phoneNumber, jobTitle, gender, age, personDept } = nowRow;
  emit("check", { id, name, phoneNumber, jobTitle, gender, age, personDept });
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
