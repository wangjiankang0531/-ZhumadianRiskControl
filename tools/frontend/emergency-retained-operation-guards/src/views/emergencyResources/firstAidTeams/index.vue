<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
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

<script setup lang="tsx">
import { ref } from "vue";
import { Download } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById, exportExcel } from "@/api/emergencyResources/firstAidTeams";
import { useHandleData } from "@/hooks/useHandleData";
import { useOrgTree } from "@/hooks/useOrgTree";
import { ElMessageBox } from "element-plus";
import { useDownload } from "@/hooks/useDownload";

const { orgTree } = useOrgTree();

const proTable = ref<ProTableInstance>();

const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "teamName",
    label: "队伍名称"
  },
  {
    prop: "teamType",
    label: "队伍类型"
  },
  {
    prop: "leaderName",
    label: "负责人名称"
  },
  {
    prop: "leaderPhone",
    label: "负责人电话"
  },
  {
    prop: "department",
    label: "所属部门",
    search: {
      render: ({ searchParam }) => {
        return (
          <el-tree-select
            v-model={searchParam.department}
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
      },
      order: 1
    }
  },
  {
    prop: "teamLocation",
    label: "队伍位置"
  },
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyResources/firstAidTeams/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyResources/firstAidTeams/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyResources/firstAidTeams/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value?.getTableList();
};

// 导出数据
const handleDown = () => {
  ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() =>
    useDownload(exportExcel, "应急队伍" + Date.now(), proTable.value?.searchParam)
  );
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
