<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
        <!--:data="data"-->
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd" :icon="Plus">新增</el-button>
        </template>
        <template #operation="scope">
          <el-button type="primary" link @click="exerciseDialog(scope.row)">演练记录</el-button>
          <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
          <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="primary" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </ProTable>
    </div>
    <ExerciseList ref="exerciseListRef" @check="exerciseListAdd" />
  </div>
</template>

<script setup lang="tsx">
import { ref } from "vue";
import { Plus } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById } from "@/api/emergencyPlans/structured";
import { useHandleData } from "@/hooks/useHandleData";
import { useDict } from "@/hooks/useDict";
import { useOrgTree } from "@/hooks/useOrgTree";
import ExerciseList from "./info/exerciseList.vue";

const { orgTree } = useOrgTree();
const { emergencyPlanType, eventType } = useDict("safetycode", ["emergencyPlanType", "eventType"]);
const proTable = ref<ProTableInstance>();
const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "emergencyPlanName",
    label: "应急预案名称",
    search: {
      el: "input"
    }
  },
  {
    prop: "emergencyPlanType",
    label: "应急预案类型",
    enum: emergencyPlanType,
    search: {
      el: "select"
    },
    tag: true
  },
  {
    prop: "accidentType",
    label: "事故类型",
    enum: eventType,
    tag: true
  },
  {
    prop: "commanderName",
    label: "指挥长"
  },
  {
    prop: "commanderPhone",
    label: "指挥长电话"
  },
  {
    prop: "isFilings",
    label: "是否备案",
    enum: [
      { label: "是", value: "1" },
      { label: "否", value: "0" }
    ],
    tag: true
  },
  {
    prop: "createDept",
    label: "所属部门",
    enum: orgTree,
    fieldNames: {
      label: "fullName",
      value: "id"
    },
    search: {
      render: ({ searchParam }) => {
        return (
          <el-tree-select
            v-model={searchParam.createDept}
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
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyPlans/structured/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyPlans/structured/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyPlans/structured/detail",
    query: {
      id: row.id
    }
  });
};
const exerciseListRef = ref<InstanceType<typeof ExerciseList> | null>(null);
const exerciseDialog = row => {
  exerciseListRef.value!.acceptParams(row.id);
  // console.log(row);
};

const exerciseListAdd = () => {
  console.log("exerciseListAdd");
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
