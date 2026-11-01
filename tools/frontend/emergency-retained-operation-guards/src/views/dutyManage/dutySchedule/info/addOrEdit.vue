<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns">
    <template #dutyTime>
      <el-time-picker
        v-model="timePickervalue"
        is-range
        range-separator="-"
        start-placeholder="开始时间"
        end-placeholder="结束时间"
      />
    </template>
  </MyForm>
  <div class="duty-list-choose">
    <div>选择值班成员</div>
    <el-button class="list-choose-btn" type="primary" @click="selectPerson">选择值班成员</el-button>
    <ProTable :columns="tableColumns" :data="listData" height="300" :pagination="false">
      <template #operation="scope">
        <el-button type="danger" link @click="handleDel(scope.$index)">删除</el-button>
      </template>
    </ProTable>
  </div>
  <PersonList ref="personListRef" @check="personListCheck" />
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import ProTable from "@/components/ProTable/index.vue";
import type { ColumnProps as TableColumnProps } from "@/components/ProTable/interface";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById, removeById } from "@/api/dutyManage/dutySchedule";
import { getList } from "@/api/dutyManage/dutyPersonnel";
import PersonList from "./personList.vue";
import { useDict } from "@/hooks/useDict";
// import { useOrgTree } from "@/hooks/useOrgTree";

const { jobTitle } = useDict("safetycode", ["jobTitle"]); //, dutyTimeRang
const { sex } = useDict("system", ["sex"]);

// const { orgTree } = useOrgTree();
const timePickervalue = ref<[Date, Date]>([
  new Date(2016, 9, 10, 8, 0), // 8:00
  new Date(2016, 9, 10, 12, 0) // 12:00
]);
const field = ref<any>({});

const personListRef = ref<InstanceType<typeof PersonList> | null>(null);
const selectPerson = () => {
  personListRef.value!.acceptParams();
};

const personListCheck = (data: any) => {
  let obj = listData.value.find(item => item.id == data.id);
  if (obj === undefined) {
    listData.value.push(data);
  }
};

const columns = ref<ColumnProps[]>([
  {
    el: "date-picker",
    prop: "dutyDate",
    label: "值班日期",
    attrs: {
      valueFormat: "YYYY-MM-DD"
    },
    required: true
  },
  {
    // el: "select",
    label: "值班时间",
    prop: "dutyTime"
    // enumData: dutyTimeRang
  },
  {
    el: "input",
    label: "值班地点",
    prop: "dutyLocation"
  },
  {
    el: "select",
    label: "值班长",
    prop: "dutyHeadId",
    fieldNames: {
      label: "name",
      value: "id"
    },
    attrs: {
      filterable: true
    }
  },
  {
    el: "input",
    label: "联系电话",
    prop: "phoneNumber",
    rules: ["phone"]
  }
]);

const tableColumns: TableColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "name",
    label: "姓名"
  },
  {
    prop: "gender",
    label: "性别",
    enum: sex
  },
  {
    prop: "age",
    label: "年龄"
  },
  {
    prop: "phoneNumber",
    label: "联系方式"
  },
  {
    prop: "jobTitle",
    label: "职务",
    enum: jobTitle,
    tag: true
  },
  {
    prop: "personDept",
    label: "部门"
  },
  {
    label: "操作",
    prop: "operation",
    width: 100
  }
];

const listData = ref<any>([]);

const handleDel = (index: number) => {
  ElMessageBox.confirm("确定删除该值班人员吗？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    listData.value.splice(index, 1);
  });
};

const formRef = ref<InstanceType<typeof MyForm> | null>(null);
const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid = await formRef.value!.validate();
  if (!valid) return;
  field.value.dutyPersonnelIds = listData.value.map(item => item.id).join(",");
  // if (field.value.dutyTime == "1") {
  //   field.value.start = field.value.dutyDate + " 12:00:00";
  //   field.value.end = field.value.dutyDate + " 18:00:00";
  // } else {
  //   field.value.start = field.value.dutyDate + " 08:00:00";
  //   field.value.end = field.value.dutyDate + " 12:00:00";
  // }
  if (timePickervalue.value && timePickervalue.value.length > 1) {
    //     console.log(timePickervalue.value,timePickervalue.value[0].toLocaleTimeString('zh-CN', {
    //   hour: '2-digit',
    //   minute: '2-digit',
    //   hour12: false
    // }),router);
    field.value.start =
      field.value.dutyDate +
      " " +
      timePickervalue.value[0].toLocaleTimeString("zh-CN", {
        hour: "2-digit", // 强制两位数字
        minute: "2-digit",
        second: "2-digit",
        hour12: false
      });
    field.value.end =
      field.value.dutyDate +
      " " +
      timePickervalue.value[1].toLocaleTimeString("zh-CN", {
        hour: "2-digit", // 强制两位数字
        minute: "2-digit",
        second: "2-digit",
        hour12: false
      });
  }
  let response: any;
  try {
    response = await api(field.value);
  } catch {
    return;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("操作未完成，请保留当前内容，核对值班记录状态后重试。");
    return;
  }
  ElMessage.success(message);
  router.push({
    path: "/dutyManage/dutySchedule"
  });
};

const handleRemove = () => {
  ElMessageBox.confirm("是否删除？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    let response: any;
    try {
      response = await removeById({ id: route.query.id });
    } catch {
      return;
    }
    if (response?.code !== 0 || response?.data !== true) {
      ElMessage.error("操作未完成，请保留当前内容，核对值班记录状态后重试。");
      return;
    }
    ElMessage.success("删除成功！");
    router.push({
      path: "/dutyManage/dutySchedule"
    });
  }, () => {});
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    const res: any = await getById({ id: route.query.id });
    field.value = res.data.dutySchedule ?? {};
    // 转换为 timePickervalue 需要的格式
    timePickervalue.value = [
      new Date(field.value.start), // 对应 09:00:00
      new Date(field.value.end) // 对应 21:00:00
    ];
    listData.value = res.data.dutyPersonnelList ?? [];
  }
  const persons = await getList();
  columns.value.find(item => item.prop == "dutyHeadId")!.enumData = persons.data as any[];
});

defineExpose({
  submit: handleSubmit,
  remove: handleRemove
});
</script>

<style scoped lang="scss">
.duty-list-choose {
  :deep(.card) {
    border: none;
    padding: 20px 0px;
    border-radius: 0;
    box-shadow: none;
  }
}
.list-choose-btn {
  margin-top: 10px;
}
</style>
