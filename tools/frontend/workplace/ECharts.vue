<template>
  <div id="echarts" ref="chartRef" :style="echartsStyle" />
</template>

<script setup lang="ts" name="ECharts">
import { ref, onMounted, onBeforeUnmount, watch, computed, markRaw, nextTick, onActivated } from "vue";
import type { EChartsType, ECElementEvent } from "echarts/core";
import echarts, { ECOption } from "@/components/ECharts/config";
import { useDebounceFn } from "@vueuse/core";

interface Props {
  option: ECOption;
  renderer?: "canvas" | "svg";
  resize?: boolean;
  theme?: Object | string;
  width?: number | string;
  height?: number | string;
  onClick?: (event: ECElementEvent) => any;
}
const props = withDefaults(defineProps<Props>(), { renderer: "canvas", resize: true });
const cssSize = (value?: number | string) =>
  typeof value === "number" ? value + "px" : value?.trim() || "100%";
const echartsStyle = computed(() => ({ height: cssSize(props.height), width: cssSize(props.width) }));
const chartRef = ref<HTMLDivElement | HTMLCanvasElement>();
const chartInstance = ref<EChartsType>();
let alive = true;
let observer: ResizeObserver | undefined;

const draw = () => {
  if (alive && chartInstance.value && !chartInstance.value.isDisposed())
    chartInstance.value.setOption(props.option, { notMerge: true });
};
const handleClick = (event: ECElementEvent) => props.onClick && props.onClick(event);
const usableContainer = () => chartRef.value && chartRef.value.clientWidth > 0 && chartRef.value.clientHeight > 0;
const init = () => {
  if (!alive || !usableContainer()) return;
  chartInstance.value = echarts.getInstanceByDom(chartRef.value!);
  if (!chartInstance.value) {
    chartInstance.value = markRaw(echarts.init(chartRef.value!, props.theme, { renderer: props.renderer }));
    chartInstance.value.on("click", handleClick);
    draw();
  }
};
const resize = () => {
  if (!alive || !props.resize || !usableContainer()) return;
  if (!chartInstance.value || chartInstance.value.isDisposed()) init();
  chartInstance.value?.resize({ animation: { duration: 300 } });
};
const debouncedResize = useDebounceFn(resize, 80, { maxWait: 240 });
watch(props, () => { draw(); debouncedResize(); });
onMounted(async () => {
  await nextTick();
  if (!alive) return;
  init();
  if (typeof ResizeObserver !== "undefined" && chartRef.value) {
    observer = new ResizeObserver(() => debouncedResize());
    observer.observe(chartRef.value);
  }
  window.addEventListener("resize", debouncedResize);
});
onActivated(() => { init(); debouncedResize(); });
onBeforeUnmount(() => {
  alive = false;
  observer?.disconnect();
  window.removeEventListener("resize", debouncedResize);
  chartInstance.value?.dispose();
});
defineExpose({ getInstance: () => chartInstance.value, resize, draw });
</script>
