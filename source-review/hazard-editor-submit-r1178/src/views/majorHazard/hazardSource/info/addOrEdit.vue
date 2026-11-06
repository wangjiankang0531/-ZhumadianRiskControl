<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns">
    <template #personId>
      <el-select v-model="field.personId" filterable clearable>
        <el-option v-for="item in userList" :key="item.id" :label="item.realName" :value="item.id"></el-option>
      </el-select>
    </template>
    <!-- 经纬度 -->
    <template #coordinate>
      <div class="flx-align-center" style="width: 100%">
        <el-input
          :input-style="{ cursor: 'pointer' }"
          readonly
          :value="field.coordinate"
          placeholder="请选择"
          @click="openMapDialog"
        />
      </div>
    </template>
  </MyForm>
  <MapPoint ref="mapPointRef" />
  <div class="info-title">附件信息</div>
  <List v-model:data="fileList" />
</template>

<script setup lang="tsx">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import MapPoint from "@/components/MapPoint/index.vue";
import { save, updateById, getById } from "@/api/majorHazard";
import { useOrgTree } from "@/hooks/useOrgTree";
import { useDict } from "@/hooks/useDict";
import { getDepartmentIdByUserList } from "@/api/system/org";
import { findObjectById } from "@/utils";
import List from "../components/List/index.vue";

const { orgTree } = useOrgTree();

const { hazardousSourcesRiskLevel, functionArea } = useDict("safetycode", ["hazardousSourcesRiskLevel", "functionArea"]);

const field = ref<any>({});

const fileList = ref<any>([]);
const submitting = ref(false);
const writeCommitted = ref(false);
const detailReady = ref(true);
let viewActive = true;
onBeforeUnmount(() => { viewActive = false; });

const userList = ref<any[]>([]);

const columns = ref<ColumnProps[]>([
  {
    el: "input",
    prop: "sourceCode",
    label: "危险源编码",
    required: true
  },
  {
    el: "input",
    prop: "sourceName",
    label: "危险源名称",
    required: true
  },
  {
    el: "select",
    prop: "location",
    label: "区域",
    enumData: functionArea,
    attrs: {
      filterable: true
    },
    required: true
  },
  {
    el: "input",
    prop: "materialType",
    label: "危险物质类型",
    required: true
  },
  {
    el: "input",
    prop: "criticalAmount",
    label: "临界量（吨）",
    rules: ["number"],
    required: true
  },
  {
    el: "input",
    prop: "currentAmount",
    label: "当前存量（吨）",
    rules: ["number"],
    required: true
  },
  {
    el: "input",
    prop: "status",
    label: "状态"
  },
  {
    el: "select",
    prop: "riskLevel",
    label: "风险等级",
    enumData: hazardousSourcesRiskLevel,
    required: true
  },
  {
    el: "input",
    prop: "assessmentMethod",
    label: "评估方法"
  },
  {
    el: "input",
    prop: "consequence",
    label: "可能后果"
  },
  {
    el: "input",
    prop: "probability",
    label: "发生概率"
  },
  {
    el: "date-picker",
    prop: "assessmentTime",
    label: "评估日期",
    attrs: {
      valueFormat: "YYYY-MM-DD"
    }
  },
  {
    el: "date-picker",
    prop: "inTime",
    label: "入库时间",
    attrs: {
      valueFormat: "YYYY-MM-DD"
    }
  },
  {
    el: "date-picker",
    prop: "outTime",
    label: "出库时间",
    attrs: {
      valueFormat: "YYYY-MM-DD"
    }
  },
  { el: "input", prop: "description", label: "描述说明" },
  {
    prop: "departmentId",
    label: "责任部门",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.departmentId}
          data={orgTree.value}
          check-strictly={true}
          filterable={true}
          clearable={true}
          props={{
            label: "fullName",
            value: "id"
          }}
          onChange={(val: any) => {
            field.value.personId = undefined;
            if (!val) {
              userList.value = [];
              return;
            }
            checkDepartmentChange(val);
          }}
        />
      );
    }
  },
  { prop: "personId", label: "责任人" },
  {
    prop: "coordinate",
    label: "坐标信息"
  }
]);

// 部门变化时，获取部门下的用户列表
const checkDepartmentChange = async id => {
  const res: any = await getDepartmentIdByUserList(id);
  userList.value = res.data;
};

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

const handleSubmit = async () => {
  if (submitting.value || writeCommitted.value) return false;
  if (route.query.type === "edit" && (!detailReady.value || !field.value.id)) {
    if (viewActive) ElMessage.error("详情未取得，请返回列表刷新后重试。");
    return false;
  }
  submitting.value = true;
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  try {
    const valid = await formRef.value!.validate();
    if (!valid || !viewActive) return false;
    const params = JSON.parse(JSON.stringify(field.value));
    params.department = findObjectById(orgTree.value, params.departmentId)?.fullName;
    params.person = userList.value.find(item => item.id == params.personId)?.realName;
    const response: any = await api({ hazardSource: params, baseFileList: fileList.value });
    if (response?.code !== 0 || response?.data !== true) {
      if (viewActive) ElMessage.error("保存未完成，请保留当前内容并重试。");
      return false;
    }
    writeCommitted.value = true;
    if (viewActive) {
      ElMessage.success(message);
      await router.push({ path: "/majorHazard/hazardSource" });
    }
    return true;
  } catch {
    if (viewActive) {
      if (writeCommitted.value) ElMessage.warning("保存已完成，请返回列表核对。");
      else ElMessage.error("保存未完成，请保留当前内容并重试。");
    }
    return writeCommitted.value;
  } finally {
    submitting.value = false;
  }
};

const router = useRouter();
const route = useRoute();

// 经纬度选择
const mapPointRef = ref<InstanceType<typeof MapPoint> | null>(null);

const openMapDialog = () => {
  const params = {
    title: "坐标信息",
    isView: false,
    callback: val => (field.value.coordinate = val)
  };
  mapPointRef.value!.acceptParams(params, field.value.coordinate);
};

onMounted(async () => {
  if (route.query.type !== "edit") return;
  detailReady.value = false;
  try {
    const res: any = await getById({ id: route.query.id });
    const record = res?.data?.hazardSource;
    if (!viewActive) return;
    if (res?.code !== 0 || !record || !record.id || String(record.id) !== String(route.query.id)) {
      ElMessage.error("详情未取得，请返回列表刷新后重试。");
      return;
    }
    field.value = record;
    field.value.departmentId && (await checkDepartmentChange(field.value.departmentId));
    if (!viewActive) return;
    fileList.value = res.data.baseFileList ?? [];
    detailReady.value = true;
  } catch {
    if (viewActive) ElMessage.error("详情未取得，请返回列表刷新后重试。");
  }
});

defineExpose({
  submit: handleSubmit,
  submitting,
  writeCommitted,
  detailReady
});
</script>
