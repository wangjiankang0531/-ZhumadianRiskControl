<template>
  <el-alert v-if="view.errors.length" :title="view.errors[0]" type="error" :closable="false" show-icon />
  <el-form v-else :label-width="view.labelWidth" :label-position="view.labelPosition" class="original-online-form">
    <el-row :gutter="16">
      <el-col v-for="field in view.fields" :key="field.key" :xs="24" :sm="field.span">
        <el-form-item :label="field.showLabel ? field.label : ''" :label-width="field.showLabel ? undefined : 0"
          :required="field.required && field.writable" :error="validation.find(item => item.key === field.key)?.message">
          <el-input :model-value="field.value" :type="field.type" :readonly="!field.writable" :disabled="!field.writable"
            :maxlength="field.maxlength" :minlength="field.minlength" :placeholder="field.writable ? field.placeholder : ''"
            :show-word-limit="field.writable && field.showWordLimit" :data-online-field="field.key"
            @update:model-value="value => update(field, value)" />
        </el-form-item>
      </el-col>
    </el-row>
    <el-empty v-if="!view.fields.length" description="此审批表单没有可显示字段" :image-size="64" />
  </el-form>
</template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { originalOnlineFormView, updateOriginalOnlineField, originalOnlineFieldErrors, type OnlineFormField } from "./OriginalWorkflowOnlineFormModelR470";
const props = defineProps<{
  propertyJson: string | object;
  formData: Record<string, unknown>;
  formOperates: unknown[];
  editable?: boolean;
}>();
const emit = defineEmits<{ (event: "update:formData", data: Record<string, unknown>): void }>();
const validation = ref<{ key: string; message: string }[]>([]);
const view = computed(() => originalOnlineFormView(props.propertyJson, props.formData, props.formOperates, props.editable ? "edit" : "view"));
watch(() => [props.propertyJson, props.formData, props.formOperates, props.editable], () => { validation.value = []; });
function update(field: OnlineFormField, value: string | number) {
  if (!field.writable) return;
  emit("update:formData", updateOriginalOnlineField(props.formData, field, value));
}
function validate() {
  validation.value = originalOnlineFieldErrors(view.value.fields);
  return view.value.errors.length === 0 && validation.value.length === 0;
}
defineExpose({ validate });
</script>
<style scoped>
.original-online-form { width: 100%; min-width: 0; }
.original-online-form :deep(.el-input), .original-online-form :deep(.el-textarea) { width: 100%; }
</style>
