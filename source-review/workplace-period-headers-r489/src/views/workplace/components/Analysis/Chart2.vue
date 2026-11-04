<template>
  <div class="card chart">
    <div class="chart_top">
      <div class="chart_title">隐患级别数量统计</div>
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
import type { ECOption } from "@/components/ECharts/config";
import { getAnalysis2 } from "@/api/workplace/index";
import dayjs from "dayjs";

const radio = ref("全部");

const option = ref<ECOption>({});

const getData = async () => {
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

  const res: any = await getAnalysis2({ startTime, endTime });
  const total = res.reduce((prev: any, cur: any) => prev + cur.value, 0);
  option.value = {
    title: {
      text: total + "",
      subtext: "隐患总数",
      textStyle: {
        fontSize: 30,
        fontWeight: "bold"
      },
      subtextStyle: {
        fontSize: 14,
        padding: [5, 0]
      },
      textAlign: "center",
      left: "49%",
      top: "42%"
    },
    tooltip: {
      trigger: "item",
      formatter: "{a} <br/>{b}: {c}处 ({d}%)"
    },
    color: ["#0064ff", "#00cc00"],
    series: [
      {
        name: "巡检点异常类型统计",
        type: "pie",
        radius: ["70%", "58%"],
        center: ["50%", "50%"],
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 4
        },
        label: {
          color: "#333",
          lineHeight: 18,
          formatter: params => `{a|${params.value} / ${params.percent}%}\n {b|${params.name}}`,
          rich: {
            a: {
              color: "#272727",
              fontSize: 14,
              lineHeight: 20,
              fontWeight: "bold"
            },
            b: {
              color: "#979797"
            }
          }
        },
        data: res
      }
    ]
  };
};

const handleChange = () => getData();

getData();
</script>

<style scoped lang="scss">
.chart {
  min-width: 0;
  container-type: inline-size;
  &_top {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
    min-width: 0;
    > .el-radio-group {
      flex: 0 0 auto;
      max-width: 100%;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-left: auto;
    }
  }
  &_title {
    flex: 1 1 160px;
    min-width: 0;
    font-size: 16px;
    font-weight: 600;
    line-height: 24px;
    overflow-wrap: anywhere;
  }
  &_content {
    position: relative;
    width: 100%;
    height: 260px;
    margin-top: 12px;
  }
}
@container (max-width: 180px) {
  .chart_top > .el-radio-group {
    width: 100%;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart_top :deep(.el-radio-button__inner) {
    width: 100%;
    box-sizing: border-box;
    padding-inline: 6px;
  }
}
</style>
