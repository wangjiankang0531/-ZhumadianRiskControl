<template>
  <div class="ele-page">
    <div class="table-box">
      <SearchForm
        :search-param="searchParam"
        :columns="columns"
        :search-col="{ xs: 1, sm: 2, md: 2, lg: 3, xl: 4 }"
        :search="handleSearch"
        :reset="handleReset"
      />
      <el-alert v-if="loadError" type="error" :closable="false" show-icon
        title="统计加载失败，以下仍为上次成功结果，请重新查询。" role="alert" />
      <div class="statistics-view" v-loading="loading" :aria-busy="loading">
        <el-scrollbar>
          <div class="view-item item-layout" style="height: 280px">
            <div class="layout-i card" style="margin-right: 12px">
              <div class="view-item-title">风险等级统计</div>
              <v-chart ref="levelChartRef" :option="levelChartOption" style="height: 226px" />
            </div>
            <div class="layout-i card">
              <div class="view-item-title">地理位置统计</div>
              <v-chart ref="locationAreaChartRef" :option="locationChartOption" style="height: 226px" />
            </div>
          </div>
          <div class="view-item item-layout" style="height: 280px">
            <div class="layout-i card" style="margin-right: 12px">
              <div class="view-item-title">状态统计</div>
              <v-chart ref="statusChartRef" :option="statusChartOption" style="height: 226px" />
            </div>
            <div class="layout-i card">
              <div class="view-item-title">危险物质类型统计</div>
              <v-chart ref="materialTypeChartRef" :option="materialTypeChartOption" style="height: 226px" />
            </div>
          </div>
          <div class="view-item card" style="height: 290px">
            <div class="view-item-title">评估日期统计</div>
            <v-chart ref="timeChartRef" :option="timeChartOption" style="height: 236px" />
          </div>
        </el-scrollbar>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onBeforeUnmount } from "vue";
import { getAnalysis1, getAnalysis2, getAnalysis3, getAnalysis4, getAnalysis5 } from "@/api/majorHazard";
import { use } from "echarts/core";
import type { EChartsCoreOption } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { GridComponent, TooltipComponent, LegendComponent, GraphicComponent } from "echarts/components";
import { LineChart, BarChart, PieChart } from "echarts/charts";
import VChart from "vue-echarts";
import { useEcharts } from "@/utils/use-echarts";
import SearchForm from "@/components/SearchForm/index.vue";
import type { ColumnProps } from "@/components/ProTable/interface";

use([CanvasRenderer, LineChart, BarChart, PieChart, GridComponent, GraphicComponent, LegendComponent, TooltipComponent]);
const searchParam = ref({});
const columns: ColumnProps[] = [
  {
    prop: "time",
    label: "时间查询",
    search: {
      el: "date-picker",
      props: {
        type: "daterange",
        valueFormat: "YYYY-MM-DD"
      }
    }
  }
];

const levelChartRef = ref<InstanceType<typeof VChart> | null>(null);
const locationChartRef = ref<InstanceType<typeof VChart> | null>(null);
const statusChartRef = ref<InstanceType<typeof VChart> | null>(null);
const materialTypeChartRef = ref<InstanceType<typeof VChart> | null>(null);
const timeChartRef = ref<InstanceType<typeof VChart> | null>(null);

useEcharts([levelChartRef, locationChartRef, statusChartRef, materialTypeChartRef, timeChartRef]);

const levelChartOption: EChartsCoreOption = reactive({});
const locationChartOption: EChartsCoreOption = reactive({});
const statusChartOption: EChartsCoreOption = reactive({});
const materialTypeChartOption: EChartsCoreOption = reactive({});
const timeChartOption: EChartsCoreOption = reactive({});

const data1 = ref<any>();
const data2 = ref<any>();
const data3 = ref<any>();
const data4 = ref<any>();
const data5 = ref<any>();

const loading = ref(false);
const loadError = ref(false);
let latestRequest = 0;
onBeforeUnmount(() => { latestRequest++; });

const getDate = async (params) => {
  const requestId = ++latestRequest;
  loading.value = true;
  loadError.value = false;
  try {
  const [res1, res2, res3, res4, res5] = await Promise.all([
    getAnalysis1(params), getAnalysis2(params), getAnalysis3(params),
    getAnalysis4(params), getAnalysis5(params)
  ]);
  if (requestId !== latestRequest) return;
  data1.value = res1.data ? res1.data : [];
  data2.value = { names: res2.data?.names ?? [], values: res2.data?.values ?? [] };
  data3.value = res3.data ? res3.data : [];
  data4.value = res4.data ? res4.data : [];
  data5.value = { names: res5.data?.names ?? [], values: res5.data?.values ?? [] };

  Object.assign(levelChartOption, {
    tooltip: {
      trigger: "item"
    },
    legend: {
      orient: "vertical",
      right: "22%",
      top: "middle"
    },
    graphic: {
      type: "text",
      left: "33%",
      top: "center",
      style: {
        text:
          String(data1.value.reduce((sum, item) => sum + item.value, 0)).replace(/(\d)(?=(?:\d{6})+$)/g, "$1.") + "\n\n" + "总数",
        textAlign: "center",
        fill: "#333",
        width: 30,
        height: 30,
        fontSize: 14
      }
    },
    series: [
      {
        type: "pie",
        radius: ["65%", "85%"],
        left: "-30%",
        itemStyle: {
          borderRadius: 3
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: data1
      }
    ]
  });
  Object.assign(locationChartOption, {
    grid: {
      bottom: 20,
      left: 40,
      top: 20
    },
    xAxis: {
      type: "category",
      data: data2.value.names
    },
    yAxis: {
      type: "value"
    },
    series: [
      {
        data: data2.value.values,
        type: "bar",
        barWidth: 24,
        color: "#0061FF",
        itemStyle: {
          normal: {
            borderRadius: [5, 5, 0, 0] // 只影响顶部和底部
          }
        }
      }
    ]
  });
  Object.assign(statusChartOption, {
    tooltip: {
      trigger: "item"
    },
    legend: {
      orient: "vertical",
      right: "22%",
      top: "middle"
    },
    graphic: {
      type: "text",
      left: "33%",
      top: "center",
      style: {
        text:
          String(data3.value.reduce((sum, item) => sum + item.value, 0)).replace(/(\d)(?=(?:\d{6})+$)/g, "$1.") + "\n\n" + "总数",
        textAlign: "center",
        fill: "#333",
        width: 30,
        height: 30,
        fontSize: 14
      }
    },
    series: [
      {
        type: "pie",
        radius: ["65%", "85%"],
        left: "-30%",
        itemStyle: {
          borderRadius: 3
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: data3
      }
    ]
  });
  Object.assign(materialTypeChartOption, {
    tooltip: {
      trigger: "item"
    },
    legend: {
      orient: "vertical",
      right: "22%",
      top: "middle"
    },
    graphic: {
      type: "text",
      left: "33%",
      top: "center",
      style: {
        text:
          String(data4.value.reduce((sum, item) => sum + item.value, 0)).replace(/(\d)(?=(?:\d{6})+$)/g, "$1.") + "\n\n" + "总数",
        textAlign: "center",
        fill: "#333",
        width: 30,
        height: 30,
        fontSize: 14
      }
    },
    series: [
      {
        type: "pie",
        radius: ["65%", "85%"],
        left: "-30%",
        itemStyle: {
          borderRadius: 3
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: data4
      }
    ]
  });
  Object.assign(timeChartOption, {
    title: {
      text: ""
    },
    tooltip: {
      trigger: "axis"
    },
    grid: {
      left: "1%",
      right: "1%",
      bottom: "1%",
      top: "6%",
      containLabel: true
    },
    toolbox: {
      feature: {
        saveAsImage: {}
      }
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: data5.value.names
    },
    yAxis: {
      type: "value"
    },
    series: [
      {
        name: "数量",
        type: "line",
        color: "#0061FF",
        data: data5.value.values
      }
    ]
  });
  } catch {
    if (requestId === latestRequest) loadError.value = true;
  } finally {
    if (requestId === latestRequest) loading.value = false;
  }
};
getDate({});
const handleSearch = () => {
  let newParams = JSON.parse(JSON.stringify(searchParam.value));
  newParams.time && (newParams.startTime = newParams.time[0]);
  newParams.time && (newParams.endTime = newParams.time[1]);
  delete newParams.time;
  getDate(newParams);
};
const handleReset = () => {
  searchParam.value = {};
  getDate({});
};
</script>
<style scoped lang="scss">
.ele-page {
  overflow: hidden;
}
.table-box {
  height: 100%;
  .statistics-view {
    overflow: hidden;
    flex: 1;
    margin-top: 2px;
    .view-item {
      margin-top: 12px;
    }
    .item-layout {
      display: flex;
      flex-direction: row;
      .layout-i {
        width: 50%;
        height: 100%;
      }
    }
    .view-item-title {
      font-weight: 700;
      font-size: 16px;
      color: #333333;
    }
    .card {
      padding: 12px;
    }
  }
  .statistics-view :first-child {
    margin-top: 0px;
  }
}
</style>
