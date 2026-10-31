import type { ECOption } from "@/components/ECharts/config";

export function buildEventReportOption(rawData: unknown): ECOption {
  const data = (Array.isArray(rawData) ? rawData : []).map(row => {
    const record = row && typeof row === "object" ? row : {};
    const value = Number(record.value);
    return { name: String(record.name ?? "").trim(), value: Number.isFinite(value) && value >= 0 ? value : 0 };
  }).filter(row => row.name.length > 0);
  const total = data.reduce((sum, row) => sum + row.value, 0);
  const wide = {
    title: { left: "30%", top: "40%" },
    legend: { orient: "vertical", left: "58%", right: 6, top: "center", bottom: "auto", width: "40%", height: "85%" },
    series: [{ center: ["30%", "50%"], radius: ["52%", "70%"] }]
  };
  return {
    baseOption: {
      title: {
        text: String(total), subtext: "事件总数", textAlign: "center", padding: 0,
        textStyle: { fontSize: Math.min(26, Math.max(10, Math.floor(85 / String(total).length))), fontWeight: "bold" },
        subtextStyle: { fontSize: 12 }, ...wide.title
      },
      tooltip: { trigger: "item", formatter: "{a} <br/>{b}: {c}件({d}%)" },
      color: ["#385efd", "#56c928", "#fb7c1a", "#579cfd", "#fbc34b"],
      legend: {
        ...wide.legend, type: "scroll", data: data.map(row => row.name),
        itemWidth: 10, itemHeight: 10, itemGap: 10, pageIconSize: 9,
        textStyle: { fontSize: 12 },
        tooltip: { show: true },
        formatter(name: string) {
          const value = data.find(row => row.name === name)?.value || 0;
          const label = Array.from(name).length > 6 ? Array.from(name).slice(0, 6).join("") + "…" : name;
          return label + "  " + (total > 0 ? value / total * 100 : 0).toFixed(2) + "%";
        }
      },
      series: [{
        name: "事件上报统计", type: "pie", ...wide.series[0], stillShowZeroSum: false,
        itemStyle: { borderColor: "#fff", borderWidth: 4 },
        label: { show: false }, data
      }]
    },
    media: [
      { query: { maxWidth: 420 }, option: {
        title: { left: "50%", top: "30%" },
        legend: { orient: "horizontal", left: 8, right: 8, top: "auto", bottom: 4, width: "auto", height: 28 },
        series: [{ center: ["50%", "40%"], radius: ["35%", "50%"] }]
      }},
      { option: wide }
    ]
  } as ECOption;
}
