<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getTableList">
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd">新增</el-button>
          <el-button type="primary" :icon="Download" @click="handleDown">导出列表</el-button>
        </template>
        <template #operation="scope">
          <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
          <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="primary" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </ProTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Download } from "@element-plus/icons-vue";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById, exportExcel } from "@/api/dutyManage/dutyLog";
import { useHandleData } from "@/hooks/useHandleData";
import { ElMessageBox } from "element-plus";
import { useDownload } from "@/hooks/useDownload";

const proTable = ref<ProTableInstance>();
const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "dutyDate",
    label: "值班时间",
    search: {
      el: "date-picker",
      props: {
        type: "daterange",
        valueFormat: "YYYY-MM-DD"
      }
    }
  },
  {
    prop: "dutyPersonnelName",
    label: "值班人员",
    search: {
      el: "input"
    }
  },
  {
    prop: "logContent",
    label: "日志内容",
    search: {
      el: "input"
    }
  },
  {
    prop: "eventName",
    label: "重要事件"
  },
  {
    prop: "problems",
    label: "问题"
  },
  // {
  //   prop: "checkRange",
  //   label: "排查项目(范围)",
  //   search: {
  //     el: "input"
  //   },
  //   align: "left",
  //   minWidth: 200
  // },
  {
    prop: "handlingSituation",
    label: "处理情况"
  },
  // {
  //   prop: "createDept",
  //   label: "创建人"
  // },
  // {
  //   prop: "createdAt",
  //   label: "创建时间"
  // },
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/dutyManage/dutyLog/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/dutyManage/dutyLog/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/dutyManage/dutyLog/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value!.getTableList();
};

// 导出数据
const handleDown = () => {
  ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() => {
    const newParams = JSON.parse(JSON.stringify(proTable.value?.searchParam || {}));
    newParams.dutyDate && (newParams.dutyDateStart = newParams.dutyDate[0]);
    newParams.dutyDate && (newParams.dutyDateEnd = newParams.dutyDate[1]);
    delete newParams.dutyDate;
    useDownload(exportExcel, "值班日志" + Date.now(), newParams);
  });
};

const getTableList = (params: any) => {
  const newParams = JSON.parse(JSON.stringify(params));
  newParams.dutyDate && (newParams.dutyDateStart = newParams.dutyDate[0]);
  newParams.dutyDate && (newParams.dutyDateEnd = newParams.dutyDate[1]);
  delete newParams.dutyDate;
  return getPage(newParams);
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
