<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns">
    <template #dutyPersonnelId>
      <el-select v-model="field.dutyPersonnelId" filterable clearable multiple>
        <el-option v-for="item in userList" :key="item.id" :label="item.name" :value="item.personId" />
      </el-select>
    </template>
    <template #eventId>
      <div class="flx-align-center" style="width: 100%">
        <el-input :input-style="{ cursor: 'pointer' }" readonly :value="field.eventName" placeholder="请选择" @click="openDialog">
          <template #suffix>
            <el-icon v-if="field.programmeId" style="cursor: pointer" @click="eventListRef?.clear()">
              <CircleClose />
            </el-icon>
          </template>
        </el-input>
      </div>
    </template>
  </MyForm>
  <EventList ref="eventListRef" @check="eventListCheck" />
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById } from "@/api/dutyManage/dutyLog";
import { getPersonList } from "@/api/dutyManage/dutyPersonnel";
import EventList from "../components/eventList.vue";

const route = useRoute();
const router = useRouter();

const getUserList = async val => {
  const res: any = await getPersonList({ date: val });
  userList.value = res.data.filter(item => !!item.personId);
};

const field = ref<any>({
  dutyPersonnelId: []
});

const columns = ref<ColumnProps[]>([
  {
    el: "date-picker",
    label: "值班日期",
    prop: "dutyDate",
    attrs: {
      valueFormat: "YYYY-MM-DD"
    },
    callback: val => {
      if (!val) {
        field.value.dutyPersonnelId = [];
        userList.value = [];
        return;
      }
      getUserList(val);
    },
    required: true
  },
  { label: "值班人员", prop: "dutyPersonnelId", required: true },
  {
    el: "input",
    label: "日志内容",
    prop: "logContent",
    attrs: {
      type: "textarea",
      maxlength: 200,
      showWordLimit: true,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    },
    required: true,
    span: 3
  },
  { label: "重要事件", prop: "eventId" },
  {
    el: "input",
    label: "问题",
    prop: "problems",
    attrs: {
      type: "textarea",
      maxlength: 200,
      showWordLimit: true,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    },
    span: 3
  },
  {
    el: "input",
    label: "处理情况",
    prop: "handlingSituation",
    attrs: {
      type: "textarea",
      maxlength: 200,
      showWordLimit: true,
      autosize: {
        minRows: 4,
        maxRows: 6
      }
    },
    span: 3
  }
]);

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid = await formRef.value!.validate();
  if (!valid) return;

  const dutyPersonnelId = field.value.dutyPersonnelId;
  const selectedPeople = dutyPersonnelId.map(el => userList.value.find(item => item.personId == el));
  if (selectedPeople.some(item => !item)) {
    ElMessage.warning("值班人员信息尚未加载完成，请等待加载或重新选择人员后提交。");
    return;
  }

  let response: any;
  try {
    response = await api({
      ...field.value,
      dutyPersonnelName:
        dutyPersonnelId.length > 0
          ? selectedPeople.map(item => item.name).join(",")
          : undefined,
      dutyPersonnelId: dutyPersonnelId.length > 0 ? dutyPersonnelId.join(",") : undefined
    });
  } catch {
    return;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("操作未完成，请保留当前内容，核对值班记录状态后重试。");
    return;
  }
  ElMessage.success(message);
  router.push({
    path: "/dutyManage/dutyLog"
  });
};

const userList = ref<any>([]);

const eventListRef = ref<InstanceType<typeof EventList> | null>(null);
const openDialog = () => {
  eventListRef.value!.acceptParams(field.value.eventId);
};

const eventListCheck = (data: any) => {
  field.value.eventId = data.id;
  field.value.eventName = data.eventName;
};

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    const res = await getById({ id: route.query.id });
    field.value = res.data;
    if (field.value.dutyPersonnelId) {
      field.value.dutyPersonnelId = field.value.dutyPersonnelId.split(",");
    } else {
      field.value.dutyPersonnelId = [];
    }
    field.value.dutyDate && (await getUserList(field.value.dutyDate));
    return;
  }
  field.value = {
    dutyPersonnelId: []
  };
});

defineExpose({
  submit: handleSubmit
});
</script>

<style scoped lang="scss"></style>
