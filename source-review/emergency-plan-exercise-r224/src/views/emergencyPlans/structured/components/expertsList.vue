<template>
  <div class="table-box no-card">
    <ProTable :columns="columns" :data="tableData" height="300" :pagination="false">
      <template #tableHeader v-if="!isView">
        <el-button type="primary" @click="handleAdd">新增应急专家</el-button>
      </template>
      <template #operation="scope">
        <el-button type="primary" link @click="handleDelete(scope.$index)">删除</el-button>
      </template>
    </ProTable>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="900" destroy-on-close>
      <div class="no-card">
        <ProTable
          ref="proTable"
          height="400px"
          :tool-button="false"
          :columns="columns1"
          :request-api="getTableList"
          :search-col="2"
        />
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedRow" @click="handleCheck">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx">
import { computed, ref, defineEmits, defineProps } from "vue";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage } from "@/api/emergencyResources/emergencyExperts";
import { useDict } from "@/hooks/useDict";
import { ElMessageBox, ElMessage } from "element-plus";

const { inspectionCategory } = useDict("safetycode", ["inspectionCategory"]);
const getTableList = params => {
  let newParams = JSON.parse(JSON.stringify(params));
  return getPage(newParams);
};
// ProTable 实例
const proTable = ref<ProTableInstance>();
const selectedRow = computed(() => proTable.value?.tableData.find(item => item && item.id == proTable.value?.radio));
const handleCheck = () => {
  const nowRow = selectedRow.value;
  if (!nowRow) { ElMessage.warning("请先选择当前列表中的一条记录。"); return; }
  emit("check", nowRow);
  dialogVisible.value = false;
};
const props = defineProps({
  list: {
    type: Array,
    default: () => []
  },
  isView: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["update:list", "check", "delete"]);

const tableData = computed<Array<any>>({
  get() {
    return props.list;
  },
  set(val) {
    emit("update:list", val);
  }
});

const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "expertName",
    label: "专家姓名"
  },
  {
    prop: "expertPhone",
    label: "专家电话"
  },
  {
    prop: "expertField",
    label: "专家领域",
    enum: inspectionCategory
  },
  {
    prop: "expertEducation",
    label: "专家学历"
  },
  {
    prop: "expertMajor",
    label: "专家专业"
  },
  {
    prop: "workingYears",
    label: "工作年限"
  },
  {
    prop: "operation",
    label: "操作",
    fixed: "right",
    isShow: !props.isView,
    width: 120
  }
];
const columns1: ColumnProps[] = [
  { type: "radio", label: "单选", width: 80 },
  {
    prop: "expertName",
    label: "专家姓名",
    search: {
      el: "input"
    }
  },
  {
    prop: "expertPhone",
    label: "专家电话"
  },
  {
    prop: "expertField",
    label: "专家领域",
    enum: inspectionCategory
  }
];
const dialogVisible = ref(false);
const dialogTitle = ref("");

const handleAdd = () => {
  dialogTitle.value = "新增";
  dialogVisible.value = true;
};

const handleDelete = (index: number) => {
  ElMessageBox.confirm("确认删除？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消"
  }).then(() => {
    emit("delete", index);
  });
};
</script>

<style lang="scss" scoped></style>
