<template>
  <div class="ele-page">
    <div class="table-box">
      <ProTable ref="proTable" :columns="columns" :request-api="getPage">
        <template #tableHeader>
          <el-button type="primary" @click="handleAdd">新增</el-button>
          <el-button type="primary" :icon="Download" @click="handleDown">导出列表</el-button>
          <el-button type="primary" :icon="Upload" @click="handleImport">Excel导入</el-button>
          <el-button type="primary" :icon="Download" @click="handleTemp">下载模板</el-button>
        </template>
        <template #operation="scope">
          <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
          <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="primary" link @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </ProTable>
    </div>
    <ImportExcel ref="importExcelRef" />
  </div>
</template>

<script setup lang="tsx">
import { ref } from "vue";
import { Download, Upload } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getPage, removeById, exportExcel, downloadTemplate, importExcel } from "@/api/emergencyResources/materials";
import { useHandleData } from "@/hooks/useHandleData";
import { useOrgTree } from "@/hooks/useOrgTree";
import { useDownload } from "@/hooks/useDownload";
import { ElMessageBox } from "element-plus";
import ImportExcel from "@/components/ImportExcel/OriginalMaterialExcelImport.vue";

const { orgTree } = useOrgTree();

const proTable = ref<ProTableInstance>();

const columns: ColumnProps[] = [
  {
    type: "index",
    label: "序号",
    width: 80
  },
  {
    prop: "materialName",
    label: "物资名称",
    search: {
      el: "input"
    }
  },
  {
    prop: "materialType",
    label: "物资类型"
  },
  {
    prop: "materialModel",
    label: "物资型号"
  },
  {
    prop: "materialQuantity",
    label: "物资数量"
  },
  {
    prop: "unit",
    label: "单位"
  },
  {
    prop: "department",
    label: "所属部门",
    search: {
      render: ({ searchParam }) => {
        return (
          <el-tree-select
            v-model={searchParam.department}
            data={orgTree.value}
            check-strictly={true}
            clearable={true}
            filterable={true}
            props={{
              label: "fullName",
              value: "fullName"
            }}
          />
        );
      },
      order: 1
    }
  },
  {
    prop: "storageLocation",
    label: "存放地点"
  },
  { prop: "operation", label: "操作", fixed: "right", width: 240 }
];

const router = useRouter();

const handleAdd = () => {
  router.push({
    path: "/emergencyResources/materials/add",
    query: {
      type: "add"
    }
  });
};

const handleEdit = row => {
  router.push({
    path: "/emergencyResources/materials/edit",
    query: {
      type: "edit",
      id: row.id
    }
  });
};

const handleDetail = row => {
  router.push({
    path: "/emergencyResources/materials/detail",
    query: {
      id: row.id
    }
  });
};

const handleDelete = async (row: any) => {
  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;
  proTable.value!.getTableList();
};

// 导出数据
const handleDown = () => {
  ElMessageBox.confirm("确认导出数据?", "温馨提示", { type: "warning" }).then(() =>
    useDownload(exportExcel, "应急物资" + Date.now(), proTable.value?.searchParam)
  );
};

// 下载模板
const handleTemp = () => {
  ElMessageBox.confirm("确认下载模板?", "温馨提示", { type: "warning" }).then(() => {
    useDownload(downloadTemplate, `应急物资模板`);
  });
};

const importExcelRef = ref<InstanceType<typeof ImportExcel> | null>(null);

// 导入数据
const handleImport = () => {
  const params = {
    title: "应急物资",
    importApi: importExcel,
    fileSuffix: ".xlsx",
    getTableList: proTable.value?.getTableList
  };
  importExcelRef.value!.acceptParams(params);
};
</script>

<style scoped lang="scss">
.table-box {
  height: 100%;
}
</style>
