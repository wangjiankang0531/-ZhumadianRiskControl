<template>
  <div class="card chart">
    <div class="chart_top">
      <div class="chart_title">事件上报统计</div>
      <el-radio-group size="small" v-model="radio" @change="handleChange">
        <el-radio-button type="primary" label="全部" value="全部" />
        <el-radio-button type="primary" label="年" value="年" />
        <el-radio-button type="primary" label="月" value="月" />
        <el-radio-button type="primary" label="日" value="日" />
      </el-radio-group>
    </div>
    <div class="chart_content">
      <ECharts :option="option"></ECharts>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ECharts from "@/components/ECharts/index.vue";
import { ECOption } from "@/components/ECharts/config";
import { getAnalysis3 } from "@/api/workplace/index";
import dayjs from "dayjs";
import { buildEventReportOption } from "./event-report-layout";

const radio = ref("全部");

const option = ref<ECOption>({});

let requestSequence = 0;
const getData = async () => {
  const requestId = ++requestSequence;
  let startTime;
  let endTime;
  switch (radio.value) {
    case "年":
      startTime = dayjs().subtract(1, "year").format("YYYY-MM-DD") + " 00:00:00";
      endTime = dayjs().format("YYYY-MM-DD") + " 23:59:59";
      break;
    case "月":
      startTime = dayjs().subtract(1, "month").format("YYYY-MM-DD") + " 00:00:00";
      endTime = dayjs().format("YYYY-MM-DD") + " 23:59:59";
      break;
    case "日":
      startTime = dayjs().subtract(1, "day").format("YYYY-MM-DD") + " 00:00:00";
      endTime = dayjs().format("YYYY-MM-DD") + " 23:59:59";
      break;
    default:
      startTime = undefined;
      endTime = undefined;
  }

  const res: any = await getAnalysis3({ startTime, endTime });
  if (requestId !== requestSequence) return;
  option.value = buildEventReportOption(res.data);
};

const handleChange = () => getData();

getData();
</script>

<style scoped lang="scss">
.chart {
  &_top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  &_title {
    font-size: 16px;
    font-weight: 600;
  }
  &_content {
    width: 100%;
    height: 260px;
  }
}
</style>
