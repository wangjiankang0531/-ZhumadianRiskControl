<template>
  <div class="map-container card" ref="mapRef"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import { Vector as VectorSource } from "ol/source";
import XYZ from "ol/source/XYZ";
import { fromLonLat, toLonLat } from "ol/proj";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import Style from "ol/style/Style";
import Icon from "ol/style/Icon";
import Text from "ol/style/Text";
import Fill from "ol/style/Fill";
import Stroke from "ol/style/Stroke";

import markImg from "./mark.png";

type Props = {
  isView?: boolean;
  markerTitle?: string;
};

const props = withDefaults(defineProps<Props>(), {
  isView: false,
  markerTitle: "坐标"
});

const emit = defineEmits(["clickMarker"]);

// 地图容器引用
const mapRef = ref(null);
// 地图实例
let map: any;
// 当前选中的点位
const currentPoint = ref();
// 矢量图层数据源
const vectorSource = new VectorSource();

// 初始化地图
const initMap = () => {
  // 创建地图图层
  const tileLayer = new TileLayer({
    source: new XYZ({
      url: window.origin + (import.meta.env.PROD ? "/zhumadian/map/" : "/map/") + "{z}/{x}/{y}.png"
    })
  });

  // 创建矢量图层用于显示点位
  const vectorLayer = new VectorLayer({
    source: vectorSource,
    style: createPointStyle
  });

  // 创建地图实例
  map = new Map({
    target: mapRef.value!,
    layers: [tileLayer, vectorLayer],
    view: new View({
      center: fromLonLat([117.53, 38.6789]),
      zoom: 17.5,
      minZoom: 16, // 最小缩放级别
      maxZoom: 23 // 最大缩放级别
    })
  });

  // 添加地图点击事件监听
  map.on("singleclick", event => {
    if (props.isView) return;
    const lonLat = toLonLat(event.coordinate);
    const [lng, lat] = lonLat;
    clearPoint();
    addPoint(props.markerTitle, lng, lat);
    emit("clickMarker", { lng, lat });
  });
};

// 创建点位样式（包含图标和文字）
const createPointStyle = feature => {
  const name = feature.get("name");
  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      src: markImg,
      width: 20,
      height: 20
    }),
    text: new Text({
      text: name,
      font: "12px Arial",
      offsetY: -25,
      fill: new Fill({ color: "#333" }),
      stroke: new Stroke({ color: "#fff", width: 2 }),
      backgroundFill: new Fill({ color: "rgba(255, 255, 255, 0.8)" }),
      padding: [3, 3, 3, 3]
    })
  });
};

// 添加点位
const addPoint = (name, lng, lat) => {
  const pointFeature = new Feature({
    geometry: new Point(fromLonLat([lng, lat])),
    name: name
  });

  currentPoint.value = { name, lng, lat, feature: pointFeature };
  vectorSource.addFeature(pointFeature);
};

// 清除点位
const clearPoint = () => {
  if (currentPoint.value) {
    vectorSource.removeFeature(currentPoint.value.feature);
    currentPoint.value = null;
  }
};

const setMarker = obj => {
  const { name, lng, lat } = obj;
  addPoint(name ?? props.markerTitle, lng, lat);
};

// 设置地图中心点的函数
const setMapCenter = coordinates => {
  // 转换经纬度坐标为地图投影坐标
  let { lng, lat } = coordinates;
  // 设置地图中心点并动画过渡
  map.getView().animate({
    center: fromLonLat([lng, lat]),
    duration: 1000 // 动画持续时间（毫秒）
  });
};

onMounted(() => {
  initMap();
});

onUnmounted(() => {
  if (map) {
    map.setTarget(null);
    map = null;
  }
});

defineExpose({
  setMarker,
  setMapCenter,
  clearPoint
});
</script>

<style scoped lang="scss">
/* 基础布局 */
.map-container {
  margin-right: 50px;
  display: flex;
  flex-direction: column;
  height: 500px;
}
</style>
