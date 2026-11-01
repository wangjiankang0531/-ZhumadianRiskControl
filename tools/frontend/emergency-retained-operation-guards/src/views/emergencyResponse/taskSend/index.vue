<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd">新增</el-button>
          <!-- <el-button type="primary" @click="handleDown">导出列表</el-button>
          <el-button type="primary">Excel导入</el-button>
          <el-button type="primary">下载模板</el-button> -->
        </template>
        <template #operation="scope">
          <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
          <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="primary" link v-if="scope.row.taskStatus!='1'" @click="handleJudge(scope.row)">处置</el-button>
          <el-button type="primary" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </ProTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById, exportExcel } from "@/api/emergencyResponse/taskSend";
import { useHandleData } from "@/hooks/useHandleData";
import { useDownload } from "@/hooks/useDownload";
import { useDict } from "@/hooks/useDict";
import { ElMessageBox } from "element-plus";

const { specialHomework } = useDict("safetycode", ["specialHomework"]);

const proTable = ref<ProTableInstance>();

const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "eventNumber",
    label: "事件编号",
    align: "left"
  },
  {
    prop: "eventName",
    label: "事件名称",
    align: "left",
  },
  {
    prop: "taskName",
    label: "任务名称",
    align: "left",
    search: {
      el: "input"
    },
  },
  {
    prop: "taskContent",
    label: "任务内容",
    align: "left",
  },
  {
    prop: "executorDept",
    label: "责任部门",
    align: "left",
  },{
    prop: "executor",
    label: "执行人",
    align: "left",
  },{
    prop: "acceptanceDept",
    label: "验收部门",
    align: "left",
  },{
    prop: "dispatchTime",
    label: "下发时间",
    align: "left",
  },{
    prop: "taskStatus",
    label: "任务状态",
    enum: [
      { label: "已处置", value: "1" },
      { label: "待处置", value: "0" },
      { label: "处置中", value: "2" }
    ],
    search: {
      el: "select"
    },
    tag: true
  },
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyResponse/taskSend/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyResponse/taskSend/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleJudge = row => {
  router.push({
    path: "/emergencyResponse/taskSend/detail",
    query: {
      id: row.id,
      judge:'1'
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyResponse/taskSend/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value!.getTableList();
};

const handleDown = () => {
  ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() =>
    useDownload(exportExcel, "任务列表", proTable.value?.searchParam)
  );
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
