<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
        <template #operation="scope">
          <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
          <el-button
            type="primary"
            :disabled="!['1', '2'].includes(scope.row.researchStatus)"
            link
            @click="handleDisposalReport(scope.row)"
          >
            处置
          </el-button>
          <el-button
            type="primary"
            :disabled="!['1', '2'].includes(scope.row.researchStatus)"
            link
            @click="handleClose(scope.row)"
          >
            完成
          </el-button>
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
import { getPage /*report*/, closeRecord } from "@/api/emergencyResponse/response";
import { useDict } from "@/hooks/useDict";
import EventReportDialog from "./components/DisposalDialog.vue";
import { save } from "@/api/emergencyResponse/disposal";
import { useHandleData } from "@/hooks/useHandleData";

const { eventType, eventLevel, researchStatus } = useDict("safetycode", ["eventType", "eventLevel", "researchStatus"]);

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
  {
    prop: "researchStatus",
    label: "状态",
    enum: researchStatus,
    tag: true,
    search: {
      el: "select",
      props: {
        filterable: true
      }
    }
  },
  {
    prop: "researchResult",
    label: "研判结果",
    align: "left"
  },
  { prop: "operation", label: "操作", fixed: "right", align: "left", width: 150 }
];

const router = useRouter();

const handleDetail = row => {
  router.push({
    path: "/emergencyResponse/disposal/detail",
    query: {
      id: row.id
    }
  });
};

const eventReportDialog = ref<InstanceType<typeof EventReportDialog> | null>(null);

const handleDisposalReport = row => {
  console.log(row);
  eventReportDialog.value?.acceptParams({
    title: "处置信息",
    row: { eventId: row.id },
    api: save,
    getTableList: proTable.value?.getTableList
  });
};

const handleClose = async row => {
  if (!(await useHandleData(closeRecord, { id: row.id }, "完成"))) return;
  proTable.value!.getTableList();
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
