<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd">新增</el-button>
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
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById } from "@/api/dutyManage/dutyPersonnel";
import { useHandleData } from "@/hooks/useHandleData";
import { useDict } from "@/hooks/useDict";
import { useOrgTree } from "@/hooks/useOrgTree";

const { orgTree } = useOrgTree();
const { jobTitle } = useDict("safetycode", ["jobTitle"]);
const { sex } = useDict("system", ["sex"]);

const proTable = ref<ProTableInstance>();
const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "name",
    label: "姓名",
    search: {
      el: "input"
    }
  },
  {
    prop: "gender",
    label: "性别",
    enum: sex
  },
  {
    prop: "age",
    label: "年龄"
  },
  {
    prop: "phoneNumber",
    label: "联系方式"
  },
  {
    prop: "jobTitle",
    label: "职务",
    enum: jobTitle,
    search: {
      el: "select"
    },
    tag: true
  },
  // {
  //   prop: "personDept",
  //   label: "部门",
  //   search: {
  //     el: "select"
  //   },
  // },
  {
    prop: "personDept",
    label: "部门",
    search: {
      key: "personDeptId",
      render: ({ searchParam }) => {
        return (
          <el-tree-select
            v-model={searchParam.personDeptId}
            data={orgTree.value}
            check-strictly={true}
            clearable={true}
            filterable={true}
            props={{
              label: "fullName",
              value: "id"
            }}
          />
        );
      },
      order: 1
    }
  },
  { prop: "operation", label: "操作", fixed: "right", width: 180 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/dutyManage/dutyPersonnel/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/dutyManage/dutyPersonnel/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/dutyManage/dutyPersonnel/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value!.getTableList();
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
