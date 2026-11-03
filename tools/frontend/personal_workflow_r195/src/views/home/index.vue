<template>
  <div class="ele-page card">
    <nav class="workflow-shortcuts" aria-label="个人审批入口">
      <el-button type="primary" data-workflow-route="/workflow/flowTodo" @click="router.push({ path: '/workflow/flowTodo' })">待办事宜</el-button>
      <el-button data-workflow-route="/workflow/completedMatters" @click="router.push({ path: '/workflow/completedMatters' })">已办事宜</el-button>
      <el-button data-workflow-route="/workflow/startWithMeTwo" @click="router.push({ path: '/workflow/startWithMeTwo' })">我发起的</el-button>
    </nav>
    <img class="home-bg" src="@/assets/images/welcome.png" alt="welcome" />
  </div>
</template>

<script setup name="home" lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>

<style scoped lang="scss">
.ele-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  margin: 16px;
  .home-bg {
    width: 70%;
    max-width: 1200px;
    margin-bottom: 20px;
  }
}
.workflow-shortcuts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin: 0 16px 16px;
}
</style>
