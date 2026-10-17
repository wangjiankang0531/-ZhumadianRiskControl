// Observed reference navigation plus Zhumadian requirement mapping. No source business records.
export const modules=Object.freeze([
  {
    "id": "risk",
    "name": "安全风险管控",
    "group": "安全管理",
    "icon": "shield",
    "description": "安全风险单元、检查内容、排查清单与排查计划",
    "topic": "portrait",
    "category": "all",
    "columns": [
      "风险单元",
      "风险等级",
      "管控部门",
      "责任人",
      "检查频次"
    ],
    "flow": [
      "辨识风险",
      "评估分级",
      "落实措施",
      "定期检查"
    ]
  },
  {
    "id": "hidden-danger",
    "name": "重点问题 · 跟踪台账",
    "group": "安全管理",
    "icon": "search",
    "description": "重大、超期、外溢等问题的关注、反馈、跟踪复查与归档",
    "topic": "portrait",
    "category": "hidden-danger",
    "columns": [
      "隐患描述",
      "位置",
      "来源",
      "排查日期",
      "隐患级别",
      "整改部门",
      "期限",
      "状态"
    ],
    "flow": [
      "重点问题登记",
      "企业反馈查看",
      "园区跟踪",
      "现场复查",
      "园区归档"
    ]
  },
  {
    "id": "inspection",
    "name": "智能巡检",
    "group": "安全管理",
    "icon": "route",
    "description": "巡检点位、任务计划、异常记录与巡检台账",
    "topic": "monitoring",
    "category": "all",
    "columns": [
      "任务名称",
      "巡检区域",
      "执行人",
      "计划时间",
      "任务状态"
    ],
    "flow": [
      "编制计划",
      "分配任务",
      "现场巡检",
      "异常上报",
      "结果审核"
    ]
  },
  {
    "id": "special-work",
    "name": "特殊作业",
    "group": "安全管理",
    "icon": "work",
    "description": "特殊作业票、作业区域与安全措施关联",
    "topic": "portrait",
    "category": "special-work",
    "columns": [
      "作业票编号",
      "作业类型",
      "作业位置",
      "负责人",
      "起止时间",
      "状态"
    ],
    "flow": [
      "作业申请",
      "风险分析",
      "安全措施确认",
      "审批许可",
      "作业监护",
      "完工验收"
    ]
  },
  {
    "id": "major-hazard",
    "name": "重大危险源",
    "group": "监测预警",
    "icon": "warning",
    "description": "危险源分布、分级档案与监测点位关联",
    "topic": "monitoring",
    "category": "major-hazard",
    "columns": [
      "危险源名称",
      "所属企业",
      "危险源级别",
      "位置",
      "监测状态"
    ],
    "flow": [
      "档案登记",
      "分级辨识",
      "监测关联",
      "异常预警",
      "处置复核"
    ]
  },
  {
    "id": "monitoring",
    "name": "监测与消防",
    "group": "监测预警",
    "icon": "pulse",
    "description": "监测预警、消防设施与视频资源的空间展示",
    "topic": "monitoring",
    "category": "all",
    "columns": [
      "点位名称",
      "设备类别",
      "所属企业",
      "采集时间",
      "状态"
    ],
    "flow": [
      "点位建档",
      "数据采集",
      "阈值预警",
      "确认处置",
      "恢复记录"
    ]
  },
  {
    "id": "events",
    "name": "应急事件与响应",
    "group": "敏捷应急",
    "icon": "emergency",
    "description": "事件上报、研判、响应、处置及总结归档",
    "topic": "emergency",
    "category": "all",
    "columns": [
      "事件编号",
      "事件名称",
      "事件类型",
      "上报时间",
      "事件级别",
      "响应状态",
      "研判结果"
    ],
    "flow": [
      "事件上报",
      "接报研判",
      "响应启动",
      "协同处置",
      "结束归档"
    ]
  },
  {
    "id": "resources",
    "name": "应急资源与预案",
    "group": "敏捷应急",
    "icon": "layers",
    "description": "应急资源、预案及值班信息的统一入口",
    "topic": "emergency",
    "category": "all",
    "columns": [
      "资源名称",
      "资源类别",
      "位置",
      "责任部门",
      "可用状态"
    ],
    "flow": [
      "资源建档",
      "定期核验",
      "预案关联",
      "调配记录",
      "补充归位"
    ]
  },
  {
    "id": "closed",
    "name": "封闭管理",
    "group": "园区运营",
    "icon": "gate",
    "description": "卡口、停车场、道路和人员车辆的空间目录",
    "topic": "closed",
    "category": "all",
    "columns": [
      "对象名称",
      "对象类别",
      "所属区域",
      "采集时间",
      "状态"
    ],
    "flow": [
      "通行申请",
      "资质核验",
      "准入放行",
      "在园跟踪",
      "离园归档"
    ]
  },
  {
    "id": "energy",
    "name": "能源管理",
    "group": "园区运营",
    "icon": "energy",
    "description": "水、电、气、热与污水设施的空间目录",
    "topic": "energy",
    "category": "all",
    "columns": [
      "设施名称",
      "能源类别",
      "所属企业",
      "采集时间",
      "运行状态"
    ],
    "flow": [
      "设施建档",
      "计量接入",
      "能耗分析",
      "异常处理",
      "结果复核"
    ]
  }
]);
export function findModule(id){return modules.find(item=>item.id===id)??null;}
export function sceneLink(item){const q=new URLSearchParams({topic:item.topic});if(item.category!=='all')q.set('category',item.category);return '/?'+q.toString();}
