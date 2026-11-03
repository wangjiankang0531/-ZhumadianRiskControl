<template>
  <el-upload ref="uploadRef" v-model:file-list="displayFiles" action="#" multiple :disabled="disabled"
    :limit="fileLimit" :http-request="uploadFileRequest" :before-upload="beforeUpload"
    :before-remove="beforeRemove" :on-remove="removed" :on-change="changed"
    :on-exceed="handleExceed" :on-success="succeeded" :on-error="failed" :accept="fileType.join(',')">
    <el-button type="primary" :disabled="disabled">点击上传</el-button>
    <template #tip><div class="el-upload__tip">请上传文件，全部上传完成后再提交</div></template>
  </el-upload>
  <div v-for="failure in failures" :key="failure.uid" role="alert" class="el-upload__tip">
    {{ failure.name }} 上传失败。请先移除失败项；如需保留该附件，再重新选择上传。
    <el-button link type="danger" :disabled="disabled" @click="discardFailure(failure.uid)">移除失败项</el-button>
  </div>
</template>
<script lang="ts" setup>
import { computed, onBeforeUnmount, ref, toRaw, watch } from "vue";
import { uploadFile } from "@/api/upload";
import { ElMessageBox, ElNotification } from "element-plus";
import type { UploadInstance, UploadProps, UploadRequestHandler, UploadUserFile } from "element-plus";
import { AttachmentUploadState, attachmentUrl, confirmedUpload } from "./OriginalAttachmentUploadState";
const fileList = defineModel<UploadUserFile[]>("fileList", { default: () => [] });
type Props = { fileType?: string[]; fileSize?: number; fileLimit?: number; disabled?: boolean };
const props = withDefaults(defineProps<Props>(), {
  fileType: () => ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint", "application/pdf", "application/vnd.kingsoft.wps",
    "application/vnd.kingsoft.et", "application/vnd.kingsoft.dps", "image/png", "image/jpeg", "image/jpg", "image/gif"],
  fileSize: 100, fileLimit: 5, disabled: false
});
const uploadRef = ref<UploadInstance>();
const displayFiles = ref<UploadUserFile[]>([]);
const version = ref(0);
const state = new AttachmentUploadState(() => version.value++);
const controllers = new Map<number, AbortController>();
const failures = computed(() => { void version.value; return state.failures; });
let published: UploadUserFile[] | null = null;
function abortAll() { for (const controller of controllers.values()) controller.abort(); controllers.clear(); }
watch(() => fileList.value, incoming => {
  if (published && toRaw(incoming) === published) return;
  abortAll(); state.reset();
  displayFiles.value = (incoming ?? []).map(file => ({ ...file, status: "success" }));
}, { immediate: true });
function publish() {
  if (state.disposed) return;
  published = displayFiles.value.filter(file => file.status === "success" && attachmentUrl(file.url))
    .map(({ raw, response, percentage, status, ...file }: any) => file);
  fileList.value = published;
}
const changed: UploadProps["onChange"] = (file, files) => {
  if (state.disposed) return;
  displayFiles.value = files;
  if (file.status === "ready") state.select(file.uid, file.name);
  publish();
};
const uploadFileRequest: UploadRequestHandler = async options => {
  if (props.disabled || state.disposed) throw Error("ATTACHMENT_UPLOAD_DISABLED");
  const uid = options.file.uid, token = state.begin(uid, options.file.name), controller = new AbortController();
  controllers.set(uid, controller);
  try {
    const data = new FormData(); data.append("file", options.file);
    const url = confirmedUpload(await uploadFile(data, controller.signal));
    if (!state.finish(uid, token, true)) throw Error("ATTACHMENT_UPLOAD_NO_LONGER_SELECTED");
    return { url };
  } catch (error) { state.finish(uid, token, false); throw error; }
  finally { if (controllers.get(uid) === controller) controllers.delete(uid); }
};
const succeeded: UploadProps["onSuccess"] = (response, file) => {
  if (state.disposed) return;
  if (!attachmentUrl(response?.url)) return;
  file.url = response.url; publish();
  ElNotification({ title: "温馨提示", message: "附件上传成功！", type: "success" });
};
const failed: UploadProps["onError"] = () => {
  if (!state.disposed) ElNotification({ title: "温馨提示", message: "附件上传未完成，请重新上传或移除失败项。", type: "error" });
};
const beforeUpload: UploadProps["beforeUpload"] = file => {
  if (props.disabled || state.disposed) return false;
  if (!props.fileType.includes(file.type)) {
    ElNotification({ title: "温馨提示", message: "请选择支持的文档或图片格式。", type: "warning" }); return false;
  }
  if (file.size / 1024 / 1024 >= props.fileSize) {
    ElNotification({ title: "温馨提示", message: `上传文件大小不能超过 ${props.fileSize}MB！`, type: "warning" }); return false;
  }
  return true;
};
const beforeRemove: UploadProps["beforeRemove"] = async file => {
  if (props.disabled) return false;
  if (file.status !== "success") return true;
  try { await ElMessageBox.confirm(`确定删除 ${file.name} ?`); return true; } catch { return false; }
};
const removed: UploadProps["onRemove"] = (file, files) => {
  controllers.get(file.uid)?.abort(); controllers.delete(file.uid); state.remove(file.uid);
  displayFiles.value = files; publish();
};
function discardFailure(uid: number) { if (!props.disabled) state.remove(uid); }
function handleExceed() { ElNotification({ title: "温馨提示", message: `最多只能上传${props.fileLimit}个文件！`, type: "warning" }); }
function ensureReady(): boolean {
  if (state.disposed) return false;
  if (state.busy || displayFiles.value.some(file => file.status === "ready" || file.status === "uploading")) {
    ElNotification({ title: "温馨提示", message: "附件正在上传，请等待全部完成后再提交。", type: "warning" }); return false;
  }
  if (state.failures.length || displayFiles.value.some(file => file.status !== "success" || !attachmentUrl(file.url))) {
    ElNotification({ title: "温馨提示", message: "附件尚未上传成功，请重传或移除失败项后再提交。", type: "warning" }); return false;
  }
  publish(); return true;
}
onBeforeUnmount(() => { state.dispose(); abortAll(); });
defineExpose({ ensureReady });
</script>
