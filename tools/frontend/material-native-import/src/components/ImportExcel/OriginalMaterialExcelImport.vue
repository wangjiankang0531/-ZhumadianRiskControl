<template>
  <el-dialog v-model="dialogVisible" :title="`批量添加${parameter.title}`" :destroy-on-close="true" :before-close="beforeClose" width="580px" draggable>
    <el-form class="drawer-multiColumn-form" label-width="100px">
      <!-- <el-form-item label="模板下载 :">
        <el-button type="primary" :icon="Download" @click="downloadTemp"> 点击下载 </el-button>
      </el-form-item> -->
      <el-form-item label="文件上传 :">
        <el-upload
          action="#"
          class="upload"
          :drag="true"
          :limit="excelLimit"
          :multiple="true"
          :show-file-list="true"
          :http-request="uploadExcel"
          :before-upload="beforeExcelUpload"
          :on-exceed="handleExceed"
          :accept="parameter.fileType!.join(',')"
        >
          <slot name="empty">
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          </slot>
          <template #tip>
            <slot name="tip">
              <div class="el-upload__tip">请上传 .xls , .xlsx 标准格式文件，文件最大为 {{ parameter.fileSize }}M</div>
            </slot>
          </template>
        </el-upload>
      </el-form-item>
      <!-- <el-form-item label="数据覆盖 :">
        <el-switch v-model="isCover" />
      </el-form-item> -->
    </el-form>
  </el-dialog>
</template>

<script setup lang="ts" name="ImportExcel">
import { ref, onBeforeUnmount } from "vue";
// import { useDownload } from "@/hooks/useDownload";
// import { Download } from "@element-plus/icons-vue";
import { ElNotification, UploadRequestOptions, UploadRawFile } from "element-plus";

export interface ExcelParameterProps {
  title: string; // 标题
  fileSize?: number; // 上传文件的大小
  fileType?: File.ExcelMimeType[]; // 上传文件的类型
  tempApi?: (params: any) => Promise<any>; // 下载模板的Api
  importApi?: (params: any) => Promise<any>; // 批量导入的Api
  getTableList?: () => void; // 获取表格数据的Api
}

// 是否覆盖数据
// const isCover = ref(false);
// 最大文件上传数
const excelLimit = ref(1);
// dialog状态
const dialogVisible = ref(false);
// 父组件传过来的参数
const parameter = ref<ExcelParameterProps>({
  title: "",
  fileSize: 100,
  fileType: ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
});

// 接收父组件参数
let dialogEpoch = 0;
let requestSerial = 0;
let currentRequest = 0;
let mounted = true;
const pendingRequests = new Map<number, number>();
onBeforeUnmount(() => {
  mounted = false;
  dialogEpoch++;
});
const beforeClose = (done: () => void) => {
  if (Array.from(pendingRequests.values()).includes(dialogEpoch)) {
    ElNotification({ title: "温馨提示", message: "导入请求仍在处理，关闭窗口不会撤回已提交的请求。", type: "info" });
  }
  dialogEpoch++;
  currentRequest = 0;
  done();
};
const acceptParams = (params: ExcelParameterProps) => {
  dialogEpoch++;
  currentRequest = 0;
  parameter.value = { ...parameter.value, ...params };
  dialogVisible.value = true;
};

// Excel 导入模板下载
// const downloadTemp = () => {
//   if (!parameter.value.tempApi) return;
//   useDownload(parameter.value.tempApi, `${parameter.value.title}模板`);
// };

// 文件上传
const uploadExcel = async (param: UploadRequestOptions) => {
  const target = { ...parameter.value };
  const epoch = dialogEpoch;
  const request = ++requestSerial;
  currentRequest = request;
  pendingRequests.set(request, epoch);
  const isCurrent = () => mounted && epoch === dialogEpoch && request === currentRequest;
  const excelFormData = new FormData();
  excelFormData.append("file", param.file);
  try {
    const response: any = await target.importApi!(excelFormData);
    const confirmed = response == null || response === "" ||
      (typeof response === "object" && response.code === 0 && response.data !== false);
    if (!confirmed) throw new Error("物资导入未确认成功。");
    if (mounted) target.getTableList && target.getTableList();
    if (isCurrent()) {
      dialogVisible.value = false;
      dialogEpoch++;
      excelUploadSuccess(target.title);
    }
    return response;
  } catch (error) {
    if (isCurrent()) excelUploadError(target.title);
    throw error;
  } finally {
    pendingRequests.delete(request);
  }
};

/**
 * @description 文件上传之前判断
 * @param file 上传的文件
 * */
const beforeExcelUpload = (file: UploadRawFile) => {
  const isExcel = parameter.value.fileType!.includes(file.type as File.ExcelMimeType);
  const fileSize = file.size / 1024 / 1024 < parameter.value.fileSize!;
  if (!isExcel)
    ElNotification({
      title: "温馨提示",
      message: "上传文件只能是 xls / xlsx 格式！",
      type: "warning"
    });
  if (!fileSize)
    setTimeout(() => {
      ElNotification({
        title: "温馨提示",
        message: `上传文件大小不能超过 ${parameter.value.fileSize}MB！`,
        type: "warning"
      });
    }, 0);
  return isExcel && fileSize;
};

// 文件数超出提示
const handleExceed = () => {
  ElNotification({
    title: "温馨提示",
    message: "最多只能上传一个文件！",
    type: "warning"
  });
};

// 上传错误提示
const excelUploadError = (title: string) => {
  ElNotification({
    title: "温馨提示",
    message: `批量添加${title}未确认完成，请先核对导入结果，再决定是否重新上传。`,
    type: "error"
  });
};

// 上传成功提示
const excelUploadSuccess = (title: string) => {
  ElNotification({
    title: "温馨提示",
    message: `批量添加${title}成功！`,
    type: "success"
  });
};

defineExpose({
  acceptParams
});
</script>
<style lang="scss" scoped>
@import "./index";
</style>
