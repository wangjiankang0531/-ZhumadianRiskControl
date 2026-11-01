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
import { useRouter } from "vue-router";
import { Download } from "@element-plus/icons-vue";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById, exportExcel } from "@/api/emergencyResources/emergencyExperts";
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
    search: {
      el: "input"
    }
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
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyResources/emergencyExperts/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyResources/emergencyExperts/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyResources/emergencyExperts/detail",
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
  ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() =>
    useDownload(exportExcel, "应急专家" + Date.now(), proTable.value?.searchParam)
  );
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
