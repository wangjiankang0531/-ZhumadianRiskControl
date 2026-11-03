<template>
  <el-dialog
    v-model="isVisible"
    width="68%"
    title="演练记录详情"
    :before-close="closeDialog"
    style="margin-top: 80px; height: 700px; padding: 24px"
  >
    <el-scrollbar height="560px">
      <div class="info-title">基础信息</div>
      <el-alert v-if="detailView.error" :title="detailView.error" type="error" :closable="false">
        <el-button link type="primary" @click="reloadDetail">重试</el-button>
      </el-alert>
      <div v-if="detailView.loading" role="status">正在加载详情…</div>
      <el-alert v-if="detailView.namesUnavailable" title="部分人员名称未取得，暂显示编号。" type="info" :closable="false" />
      <MyDetail v-if="detailView.data" :field="field" :columns="columns" />
    </el-scrollbar>

    <template #footer>
      <el-button @click="closeDialog">取消</el-button>
    </template>
  </el-dialog>
</template>
<script setup lang="tsx">
import { ref, watch, onBeforeUnmount, defineEmits, defineProps } from "vue";
import MyDetail from "@/components/Detail/index.vue";
import { EmergencyReadonlyDetail, emptyDetailView } from "@/components/Detail/OriginalEmergencyReadonlyDetail";
import { ColumnProps } from "@/components/Detail/interface";
import { getById } from "@/api/emergencyPlans/exercise";
import { useOrgTree } from "@/hooks/useOrgTree";
import { filterEnum } from "@/utils";
import { useDict } from "@/hooks/useDict";
import { getUserListByDepartmentId } from "@/api/emergencyPlans/exercise";
const { exerciseTypeData } = useDict("safetycode", ["exerciseTypeData"]);

const { orgTree } = useOrgTree();
const isVisible = ref(true);
const emit = defineEmits(["close"]);

const proxy = import.meta.env.VITE_API_URL + "/serv";

const userList = ref<any>([]);


const closeDialog = () => {
  emit("close");
};

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
});

const detailView = ref(emptyDetailView());
const field = ref<any>({});
const columns = ref<ColumnProps[]>([
  {
    label: "演练地点",
    prop: "exerciseLocation"
  },
  {
    label: "组织部门",
    prop: "organizeDepartment",
    render: () => (
      <el-input value={filterEnum(field.value.organizeDepartment, orgTree.value, { label: "fullName", value: "id" })} />
    )
  },
  {
    label: "总指挥",
    prop: "commanderChief"
  },
  {
    label: "演练时间",
    prop: "exerciseTime",
    attrs: {
      type: "datetime",
      valueFormat: "YYYY-MM-DD HH:mm:ss"
    }
  },
  {
    label: "演练类别",
    prop: "exerciseType",
    enumData: exerciseTypeData
  },
  {
    label: "配合单位",
    prop: "cooperatingUnit",
    render: () => (
      <el-input modelValue={filterEnum(field.value.cooperatingUnit, orgTree.value, { label: "fullName", value: "id" })} />
    )
  },
  {
    prop: "participants",
    label: "参加部门及人员",
    render: () => {
      if (field.value.participants) {
        let codes = field.value.participants.split(",");
        const value = codes
          .map(code => {
            return userList.value.find(i => i.id == code)?.realName || code;
          })
          ?.join(",");
        return <el-input modelValue={value} />;
      } else {
        return <el-input modelValue="--" />;
      }
    },
    // render: () => <CheckPerson v-model={field.value.personIds} />,
    span: 3
  },
  {
    prop: "exerciseDevice",
    label: "演练设备及器材",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    prop: "exerciseDescribe",
    label: "演练内容及过程描述",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    prop: "exerciseSpecialSituation",
    label: "演练过程中特殊处理情况",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },
  {
    prop: "problemsAndmeasures",
    label: "问题及改进措施",
    attrs: {
      type: "textarea",
      maxlength: 225,
      showWordLimit: true,
      autosize: {
        minRows: 3,
        maxRows: 5
      }
    },
    span: 3
  },

  {
    prop: "url",
    label: "附件",
    render: () => {
      if (!field.value.fileList?.length) return "--";
      return (
        <div>
          {field.value.fileList.map(item => {
            return (
              <el-link type="primary" underline={false} href={proxy + item.fileUrl} target="_blank">
                <div>{item.fileName}</div>
              </el-link>
            );
          })}
        </div>
      );
    }
  }
]);
const detailLoader = new EmergencyReadonlyDetail("exercise", getById, value => {
  detailView.value = value;
  field.value = value.data ?? {};
  userList.value = value.users;
}, getUserListByDepartmentId);
const reloadDetail = () => detailLoader.load(props.data?.id);
watch(() => props.data?.id, reloadDetail, { immediate: true });
onBeforeUnmount(() => detailLoader.dispose());
</script>
<style scoped lang="scss">
.info-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 20px;
}

:deep(.el-upload) {
  display: none;
}
:deep(.el-upload__tip) {
  display: none;
}
:deep(.el-upload-list) {
  margin: 0;
}
:deep(.el-upload-list__item-status-label) {
  display: none !important;
}
:deep(.el-upload-list__item .el-icon--close) {
  display: none !important;
}
</style>
