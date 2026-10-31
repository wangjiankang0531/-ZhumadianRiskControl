<template>
  <div>
    <SearchForm
      :search-param="searchParam"
      :columns="columns"
      :search-col="{ xs: 1, sm: 2, md: 2, lg: 3, xl: 4 }"
      :search="handleSearch"
      :reset="handleReset"
    ></SearchForm>
    <!-- <el-form :inline="true" :model="searchParam" size="default" status-icon>
      <el-row :gutter="16">
        <el-col :span="7" :cols="2">
          <el-form-item label="关键词" prop="keyword">
            <el-input v-model="searchParam.keyword" placeholder="请输入关键词" />
          </el-form-item>
        </el-col>
        <el-col :span="7" :cols="2">
          <el-form-item label="日期" prop="region">
            <el-date-picker
              v-model="searchParam.date"
              type="daterange"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="x"
            />
          </el-form-item>
        </el-col>
        <el-col :span="7" :cols="2">
          <el-form-item label="发起人员" prop="count">
            <el-select v-model="searchParam.region" @click.native="openSession()"></el-select>
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item>
            <el-button type="primary" @click="handleSearch"> 搜索 </el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form> -->
    <UserSelect ref="userSelectRef" @check-data="checkData" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import SearchForm from "@/components/SearchForm/index.vue";
import type { ColumnProps } from "@/components/ProTable/interface";

import UserSelect from "../../user-select/index.vue";

type Props = {
  modelValue: any;
};

const emit = defineEmits(["update:modelValue", "search", "reset"]);

const searchParam = computed({
  get() {
    return props.modelValue;
  },
  set(val) {
    emit("update:modelValue", val);
  }
});

const columns: ColumnProps[] = [
  {
    prop: "keyword",
    label: "关键词",
    search: {
      el: "input"
    }
  },
  {
    prop: "date",
    label: "日期",
    search: {
      el: "date-picker",
      props: {
        type: "daterange",
        valueFormat: "x"
      }
    }
  },
  {
    prop: "region",
    label: "发起人员",
    search: {
      el: "select",
      props: {
        placeholder: "请选择发起人员",
        onClick: () => openSession(),
        onClear: () => clearInitiator()
      }
    }
  }
];

const props = defineProps<Props>();

const userSelectRef = ref();
const openSession = () => {
  userSelectRef.value.acceptParams();
};
const clearInitiator = () => {
  delete searchParam.value.region;
  delete searchParam.value.creatorUserId;
};
const checkData = (data: any) => {
  const selected = Array.isArray(data) ? data[0] : undefined;
  if (selected?.id !== undefined && selected?.id !== null && String(selected.id).trim()) {
    searchParam.value.region = selected.fullName || String(selected.id);
    searchParam.value.creatorUserId = String(selected.id);
  } else {
    clearInitiator();
  }
};

const handleSearch = () => {
  emit("search");
};
const handleReset = () => {
  emit("reset");
};
</script>

<style lang="scss" scoped></style>
