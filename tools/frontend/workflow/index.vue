<template>
  <div class="ele-page">
    <div class="table-box">
      <SearchForm v-model="searchParam" @search="handleSearchSubmit" @reset="handleWorkReset" />
      <WorkList :data="data" :loading="loading" :type="props.type" @to="handleTo" @close="handleWorkSearch" />
      <Pagination
        v-show="data.length > 0"
        :pageable="pageable"
        :handle-current-change="handleCurrentChange"
        :handle-size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { flowLaunch, flowBefore1, flowBefore2, flowMonitor } from "@/api/workFlow";
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/modules/user";

import SearchForm from "./components/searchForm.vue";
import Pagination from "./components/pagination.vue";
import WorkList from "./components/list.vue";
import dayjs from "dayjs";

defineOptions({
  name: "WorkFlow"
});

type Props = {
  type: "我发起的" | "待办事宜" | "我已处理" | "流程监控";
  to: string;
  flowCategory?: string;
  listParameters?: string;
  fixedParameters?: any;
};

const props = defineProps<Props>();

// 查询条件
const searchParam = ref({});
const userStore = useUserStore();

// 列表数据
const data = ref<any>([]);

// 加载
const loading = ref(false);

// 查询
const handleWorkSearch = async () => {
  const params = {
    ...searchParam.value,
    ...pageable.value,
    sort: "desc",
    flowCategory: props.flowCategory
  };

  const newParams = JSON.parse(JSON.stringify(params));
  newParams.startTime = newParams.date && newParams.date[0];
  newParams.endTime = newParams.date
    ? dayjs(newParams.date[1]).hour(23).minute(59).second(59).millisecond(0).valueOf()
    : undefined; // 可选，设置毫秒为0,

  delete newParams.date;
  delete newParams.total;
  delete newParams.region;

  const fn = {
    我发起的: flowLaunch,
    待办事宜: flowBefore1,
    我已处理: flowBefore2,
    流程监控: flowMonitor
  };

  try {
    loading.value = true;
    // 原 SDK 的“我发起的”固定为当前用户，选人条件与该范围取交集。
    if (props.type === "我发起的" && newParams.creatorUserId) {
      if (!userStore.info?.userId) await userStore.fetchUserInfo();
      const currentUserId = userStore.info?.userId;
      if (!currentUserId) throw Error("CURRENT_WORKFLOW_USER_REQUIRED");
      if (String(newParams.creatorUserId) !== String(currentUserId)) {
        data.value = [];
        pageable.value = { ...pageable.value, currentPage: 1, total: 0 };
        return;
      }
    }
    const api = fn[props.type];
    const res: any = await api(newParams);
    console.log(res, "/jnpf/jnpf/jnpf");
    data.value = res.list;
    pageable.value = res.pagination;
  } finally {
    loading.value = false;
  }
};

// 新条件从第一页开始；分页操作继续保留当前条件。
const handleSearchSubmit = () => {
  pageable.value.currentPage = 1;
  return handleWorkSearch();
};

// 重置
const handleWorkReset = () => {
  pageable.value.currentPage = 1;
  searchParam.value = {};
  handleWorkSearch();
};

// 分页
const pageable = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
});

// 分页改变
const handleCurrentChange = (currentPage: number) => {
  pageable.value.currentPage = currentPage;
  handleWorkSearch();
};

// 分页条数改变
const handleSizeChange = (pageSize: number) => {
  pageable.value.pageSize = pageSize;
  handleWorkSearch();
};

// 跳转
const router = useRouter();
const handleTo = (params: any) => {
  let listParameters = {};
  if (props.listParameters !== undefined && props.listParameters !== null && props.listParameters !== "") {
    listParameters = Object.fromEntries(Object.entries(params).filter(item => props.listParameters?.includes(item[0])));
  }

  const query = {
    flowId: params.flowId,
    id: params.id,
    type: props.type,
    ...props.fixedParameters,
    ...listParameters
  };
  // console.log("listParameters:",props.listParameters)
  // console.log("params:",Object.fromEntries(Object.entries(params).filter(item => props.listParameters.includes(item[0]))))
  // console.log("query:", query)
  console.log(props.to, "1234");
  router.push({ path: props.to, query });
};

handleWorkSearch();

defineExpose({
  handleWorkSearch
});
</script>

<style lang="scss" scoped>
.ele-page {
  height: 100%;
}
</style>
