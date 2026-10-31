<template>
  <div class="card task-list">
    <div class="task-header">
      <div class="task-header_title">巡检任务清单</div>
      <div class="task-header_more" @click="togo">
        查看全部<el-icon><ArrowRight /></el-icon>
      </div>
    </div>
    <div class="table-box">
      <el-table :data="data">
        <el-table-column label="巡检计划名称" prop="planName" min-width="112" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.inspectionTasks.planName }}
          </template>
        </el-table-column>
        <el-table-column label="巡检状态" prop="inspectionStatus" width="80">
          <template #default="scope">
            <span v-if="scope.row.inspectionTasks.inspectionStatus == '0'" class="status warning">未巡检</span>
            <span v-if="scope.row.inspectionTasks.inspectionStatus == '1'" class="status green">已巡检</span>
            <span v-if="scope.row.inspectionTasks.inspectionStatus == '2'" class="status primary">已过期</span>
          </template>
        </el-table-column>
        <el-table-column label="巡检日期" prop="inspectionDateStart" min-width="168">
          <template #default="scope">
            <span v-if="!scope.row.inspectionDateStart">--</span>
            <span v-else>{{ scope.row.inspectionDateStart }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { getTaskList } from "@/api/intelligentInspection/task";
import { useUserStore } from "@/store/modules/user";

const userStore = useUserStore();

const data = ref<any>([]);
const getTableList = async () => {
  const res = await getTaskList({
    current: 1,
    size: 10,
    createDept: userStore.info?.departmentId
  });
  data.value = res.data.records;
};

getTableList();
const router = useRouter();
const togo = () => {
  router.push({
    path: "/intelligentInspection/task"
  });
};
</script>

<style scoped lang="scss">
.task-list {
  margin-top: 20px;
  .task-header {
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    &_title {
      font-size: 16px;
      font-weight: 600;
    }
    &_more {
      display: flex;
      align-items: center;
      font-size: 12px;
      color: #999;
      cursor: pointer;
      margin-left: 5px;
    }
  }
  .status {
    display: inline-flex;
    align-items: center;
    &::before {
      content: "";
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      margin-right: 5px;
    }
    &.primary {
      color: var(--el-color-primary);
      &::before {
        background-color: var(--el-color-primary);
      }
    }
    &.warning {
      color: var(--el-color-warning);
      &::before {
        background-color: var(--el-color-warning);
      }
    }
    &.green {
      color: var(--el-color-success);
      &::before {
        background-color: var(--el-color-success);
      }
    }
  }
  .table-box {
    min-width: 0;
    :deep(.el-table__header .cell) { white-space: nowrap; }
    height: 345px;
  }
}
</style>
