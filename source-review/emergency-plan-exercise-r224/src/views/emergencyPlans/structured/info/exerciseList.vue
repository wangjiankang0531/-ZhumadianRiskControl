<template>
  <el-dialog v-model="dialogVisible" width="60%" title="演练记录">
    <div class="table-box no-card">
      <ProTable
        v-if="dialogVisible"
        ref="proTable"
        height="400px"
        :tool-button="false"
        :columns="columns"
        :request-api="getTableList"
        :search-col="4"
      >
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd" :icon="Plus">新增</el-button>
        </template>
        <template #operation="scope">
          <el-button type="primary" link @click="handleDetail(scope.row)">查看</el-button>
        </template>
      </ProTable>
    </div>
    <!-- <template #footer>
      <el-button type="primary" @click="handleCheck">确定</el-button>
      <el-button @click="dialogVisible = false">取消</el-button>
    </template> -->
  </el-dialog>
  <ExerciseDialog
    v-if="isChildModalVisible"
    :emergency-plan-id="emergencyPlanId"
    @close="closeChildModal"
    @add="submitChildModal"
  />
  <ExerciseDetailDialog v-if="isChildDetailModalVisible" @close="closeChildDetailModal" v-model:data="detailData" />
</template>

<script setup lang="tsx">
import { ref, onBeforeUnmount } from "vue";
import { OriginalExerciseListUsers } from "@/components/Detail/OriginalExerciseListUsers";
import { Plus } from "@element-plus/icons-vue";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage } from "@/api/emergencyPlans/exercise";

// import { ElMessage } from "element-plus";
import { useOrgTree } from "@/hooks/useOrgTree";

import { useDict } from "@/hooks/useDict";
import ExerciseDialog from "../components/exerciseDialog.vue";
import ExerciseDetailDialog from "../components/exerciseDetailDialog.vue";
import { getUserListByDepartmentId } from "@/api/emergencyPlans/exercise";

const { orgTree } = useOrgTree();
const dialogVisible = ref(false);
const emergencyPlanId = ref<any>(""); //exerciseTypeData

const { exerciseTypeData } = useDict("safetycode", ["exerciseTypeData"]);

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 表格配置项
const columns: ColumnProps[] = [
  {
    prop: "exerciseLocation",
    label: "演练地点",
    search: {
      el: "input",
      order: 1
    }
  },
  {
    prop: "organizeDepartment",
    label: "组织部门",
    enum: orgTree,
    fieldNames: {
      label: "fullName",
      value: "id"
    },
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
              value: "id"
            }}
          />
        );
      },
      order: 3
    }
  },
  { prop: "commanderChief", label: "总指挥" },
  { prop: "exerciseTime", label: "演练时间" },
  {
    prop: "exerciseType",
    label: "演练类别",
    enum: exerciseTypeData,
    search: {
      el: "select",
      order: 2
    }
  },
  {
    prop: "participants",
    label: "参加部门及人员",
    render: scope => {
      if (scope.row.participants) {
        let codes = scope.row.participants.split(",");
        return codes
          .map(code => {
            return userList.value.find(i => i.id == code)?.realName || code;
          })
          ?.join(",");
      }
      return "--";
    }
  },
  { prop: "operation", label: "操作", fixed: "right", width: 120 }
];
const getTableList = async params => {
  let newParams = JSON.parse(JSON.stringify(params));
  newParams.emergencyPlanId = emergencyPlanId.value;
  const response = await getPage(newParams);
  void listUsers.load(response?.data?.records);
  return response;
};
const emit = defineEmits<{
  check: [val: any];
}>();

// const handleCheck = async () => {
//   const message = "新增成功！";
//   let params = {
//     emergencyPlanId: emergencyPlanId.value,
//     emergencyExerciseEntityList: proTable.value?.tableData
//   };
//   await saveList(params);
//   ElMessage.success(message);
//   dialogVisible.value = false;
// };

const isChildModalVisible = ref(false);
const isChildDetailModalVisible = ref(false);

const handleAdd = () => {
  isChildModalVisible.value = true;
  // console.log(exerciseDialogRef.value);
};
const detailData = ref<any>({});
const handleDetail = row => {
  isChildDetailModalVisible.value = true;
  detailData.value = row;
  // console.log(row);
};
const closeChildModal = () => {
  isChildModalVisible.value = false;
};
const submitChildModal = () => {
  closeChildModal();
  proTable.value?.getTableList();
};

const closeChildDetailModal = () => {
  isChildDetailModalVisible.value = false;
};

const userList = ref<any>([]);
const listUsers = new OriginalExerciseListUsers(getUserListByDepartmentId, users => { userList.value = users; });
onBeforeUnmount(() => listUsers.dispose());
// 接收父组件传过来的参数
const acceptParams = async data => {
  dialogVisible.value = true;
  emergencyPlanId.value = data;
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
