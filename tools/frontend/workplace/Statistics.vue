<template>
  <div class="statistics card">
    <div class="statistics-item" v-for="(item, index) in data" :key="index">
      <div class="statistics-item_title">
        <img v-if="index == 0" src="@/assets/images/workplace/statistics-1.svg" />
        <img v-if="index == 1" src="@/assets/images/workplace/statistics-2.svg" />
        <img v-if="index == 2" src="@/assets/images/workplace/statistics-3.svg" />
        <img v-if="index == 3" src="@/assets/images/workplace/statistics-4.svg" />
        <span>{{ item.title }}</span>
      </div>
      <div class="statistics-item_content">
        <div class="statistics-item_content_data" v-for="(el, i) in item.data" :key="i">
          <div class="statistics-item_content_data_top">
            <div class="num" v-if="index != 2" :class="{ text: !el.num }">
              {{ el.num == 0 ? "本月为空" : el.num ? el.num : "上月为空" }}
            </div>
            <div v-else class="num">{{ el.num }}</div>
            <div class="unit" v-if="!!el.num || index == 2">{{ el.unit }}</div>
          </div>
          <div class="statistics-item_content_data_bottom" :class="{ down: i == 2 && index == 0 && el.num < 0 }">
            {{ el.desc }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { getStatistics1, getStatistics2, getStatistics3, getStatistics4 } from "@/api/workplace/index";

const data = ref([
  {
    title: "巡检统计",
    data: [
      { num: 0, unit: "个", desc: "总计" },
      { num: 0, unit: "个", desc: "巡检问题数" },
      { num: 0, unit: "%", desc: "环比" }
    ]
  },
  {
    title: "隐患数量统计",
    data: [
      { num: 0, unit: "个", desc: "总计" },
      { num: 0, unit: "个", desc: "本月新增" },
      { num: 0, unit: "%", desc: "环比" }
    ]
  },
  {
    title: "隐患整改统计",
    data: [
      { num: 0, unit: "个", desc: "未整改总计" },
      { num: 0, unit: "个", desc: "整改中" },
      { num: 0, unit: "个", desc: "审批中" }
    ]
  },
  {
    title: "事件统计",
    data: [
      { num: 0, unit: "个", desc: "事件总计" },
      { num: 0, unit: "个", desc: "本月新增" },
      { num: 0, unit: "%", desc: "环比" }
    ]
  }
]);
const getDate = async () => {
  let params = {};
  const res1: any = await getStatistics1(params);
  const res2: any = await getStatistics2(params);
  const res3: any = await getStatistics3(params);
  const res4: any = await getStatistics4(params);
  data.value![0].data[0].num = res1.data.totalNumber;
  data.value![0].data[1].num = res1.data.currentNumber;
  data.value![0].data[2].num = res1.data.qoqNumber;

  data.value![1].data[0].num = res2.totalHiddenDanger;
  data.value![1].data[1].num = res2.lastWeekTotal;
  data.value![1].data[2].num = res2.monthOnMonthRatio;

  data.value![2].data[0].num = res3.pendingRectificationCount;
  data.value![2].data[1].num = res3.rectifyingCount;
  data.value![2].data[2].num = res3.inApprovalCount;

  data.value![3].data[0].num = res4.data.totalNumber;
  data.value![3].data[1].num = res4.data.currentNumber;
  data.value![3].data[2].num = res4.data.qoqNumber;
};
getDate();
</script>

<style scoped lang="scss">
.statistics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr));
  gap: 16px;
  &-item {
    min-width: 0;
    container-type: inline-size;
    &_title {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      img { width: 15px; height: 15px; margin-right: 8px; }
      span { font-size: 16px; overflow-wrap: anywhere; }
    }
    &_content {
      display: grid;
      padding: 12px;
      box-sizing: border-box;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      background-color: #f6f7f9;
      border-radius: 5px;
      &_data {
        min-width: 0;
        &_top {
          min-height: 38px;
          display: flex;
          flex-wrap: wrap;
          align-items: baseline;
          column-gap: 3px;
          .num {
            max-width: 100%;
            font-size: 18px;
            font-size: clamp(16px, 6.5cqw, 24px);
            line-height: 1.4;
            overflow-wrap: anywhere;
            &.text {
              font-size: 14px;
              font-size: clamp(14px, 5cqw, 18px);
              font-weight: 500;
            }
          }
          .unit { font-size: 12px; color: var(--el-text-color-regular); }
        }
        &_bottom {
          line-height: 1.4;
          overflow-wrap: anywhere;
          &.down {
            display: flex;
            align-items: center;
            &::after {
              content: "";
              flex: 0 0 auto;
              margin-left: 6px;
              border-left: 5px solid transparent;
              border-right: 5px solid transparent;
              border-top: 7px solid red;
            }
          }
        }
        &:nth-child(2) .num { color: #377bcd; }
      }
    }
    &:first-child .statistics-item_content_data:nth-child(2) .num { color: #f94f7b; }
    &:nth-child(3) .statistics-item_content_data:nth-child(3) .num { color: #f5a767; }
  }
}
</style>
