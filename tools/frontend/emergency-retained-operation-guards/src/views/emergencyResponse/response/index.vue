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
          <el-button type="primary" v-if="scope.row.researchStatus == '0'" link @click="handleJudge(scope.row)">研判</el-button>
          <!-- <el-button type="primary" link @click="handleEventReport(scope.row)">信息报送</el-button> -->
          <el-button type="primary" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </ProTable>
    </div>
    <EventReportDialog ref="eventReportDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById /*exportExcel,*/ /*report*/ } from "@/api/emergencyResponse/response";
import { useHandleData } from "@/hooks/useHandleData";
// import { useDownload } from "@/hooks/useDownload";
import { useDict } from "@/hooks/useDict";
// import { ElMessageBox } from "element-plus";
import EventReportDialog from "./components/EventReportDialog.vue";

const { eventType, eventLevel, /*reportType*/ researchStatus } = useDict("safetycode", [
  "eventType",
  "eventLevel",
  // reportType,
  "researchStatus"
]);

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
  },
  {
    prop: "eventType",
    label: "事件类型",
    enum: eventType,
    search: {
      el: "select"
    },
    tag: true
  },
  {
    prop: "reportTime",
    label: "上报时间"
  },
  {
    prop: "reporterName",
    label: "上报人"
  },
  {
    prop: "eventLevel",
    label: "事件级别",
    enum: eventLevel,
    tag: true
  },
  // {
  //   prop: "reportType",
  //   label: "上报类型",
  //   enum: reportType,
  //   tag: true
  // },
  {
    prop: "researchStatus",
    label: "状态",
    enum: researchStatus,
    search: {
      el: "select",
      props: {
        filterable: true
      }
    },
    tag: true
  },
  {
    prop: "researchResult",
    label: "研判结果",
    align: "left"
  },
  { prop: "operation", label: "操作", fixed: "right", align: "left", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyResponse/response/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyResponse/response/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleJudge = row => {
  router.push({
    path: "/emergencyResponse/response/detail",
    query: {
      id: row.id,
      judge: "1"
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyResponse/response/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value!.getTableList();
};

// const handleDown = () => {
//   ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() =>
//     useDownload(exportExcel, "应急响应", proTable.value?.searchParam)
//   );
// };

const eventReportDialog = ref<InstanceType<typeof EventReportDialog> | null>(null);

// const handleEventReport = row => {
//   console.log(row);
//   eventReportDialog.value?.acceptParams({
//     title: "信息报送",
//     row: { id: row.id },
//     api: report,
//     getTableList: proTable.value?.getTableList
//   });
// };
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
