<template>
  <div class="info-title">基础信息</div>
  <MyForm ref="formRef" :field="field" :columns="columns">
    <!-- 姓名 -->
    <template #personId>
      <el-select v-model="field.personId" placeholder="请选择" filterable clearable @change="personChange">
        <el-option v-for="item in userList" :key="item.id" :label="item.realName" :value="item.id"></el-option>
      </el-select>
    </template>
  </MyForm>
</template>

<script setup lang="tsx">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import MyForm from "@/components/Form/index.vue";
import { ColumnProps } from "@/components/Form/interface";
import { save, updateById, getById } from "@/api/dutyManage/dutyPersonnel";
import { useDict } from "@/hooks/useDict";
import { useOrgTree } from "@/hooks/useOrgTree";
import { getDepartmentIdByUserList } from "@/api/system/org";
import { findObjectById } from "@/utils";

const { jobTitle } = useDict("safetycode", ["jobTitle"]);
const { sex } = useDict("system", ["sex"]);

const { orgTree } = useOrgTree();

const userList = ref<any[]>([]);

const field = ref<any>({});
const columns = ref<ColumnProps[]>([
  {
    label: "部门",
    prop: "personDeptId",
    render: () => {
      return (
        <el-tree-select
          v-model={field.value.personDeptId}
          data={orgTree.value}
          check-strictly={true}
          clearable={true}
          filterable={true}
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
    },
    required: true
  },
  {
    label: "姓名",
    prop: "personId",
    required: true
  },
  {
    el: "radio",
    label: "性别",
    prop: "gender",
    enumData: sex,
    required: true
  },
  {
    el: "input",
    label: "年龄",
    prop: "age",
    rules: [
      "bigInt",
      {
        max: 3,
        message: "不能超过三位数",
        trigger: "blur"
      }
    ]
  },
  {
    el: "input",
    label: "联系电话",
    rules: ["phone"],
    prop: "phoneNumber"
  },
  {
    el: "select",
    label: "职务",
    prop: "jobTitle",
    enumData: jobTitle
  }
]);

// 部门变化时，获取部门下的用户列表
const checkDepartmentChange = async id => {
  const res: any = await getDepartmentIdByUserList(id);
  userList.value = res.data;
};

const personChange = val => {
  const user = userList.value.find(item => item.id == val);
  field.value.gender = user?.gender;
  field.value.phoneNumber = user?.mobilePhone;
};

const formRef = ref<InstanceType<typeof MyForm> | null>(null);

const handleSubmit = async () => {
  const api = route.query.type == "edit" ? updateById : save;
  const message = route.query.type == "edit" ? "编辑成功！" : "新增成功！";
  const valid = await formRef.value!.validate();
  const params = JSON.parse(JSON.stringify(field.value));
  params.name = userList.value.find(item => item.id == params.personId)?.realName;
  params.personDept = findObjectById(orgTree.value, params.personDeptId)?.fullName; // 责任单位名称
  if (!valid) return;
  let response: any;
  try {
    response = await api(params);
  } catch {
    return;
  }
  if (response?.code !== 0 || response?.data !== true) {
    ElMessage.error("操作未完成，请保留当前内容，核对值班记录状态后重试。");
    return;
  }
  ElMessage.success(message);
  router.push({
    path: "/dutyManage/dutyPersonnel"
  });
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  if (route.query.type == "edit" && route.query.id) {
    const res: any = await getById({ id: route.query.id });
    field.value = res.data;
    res.data.age && (res.data.age = res.data.age.toString());
    if (!res.data.personDeptId) return;
    await checkDepartmentChange(res.data.personDeptId);
  }
});

defineExpose({
  submit: handleSubmit
});
</script>

<style scoped lang="scss"></style>
