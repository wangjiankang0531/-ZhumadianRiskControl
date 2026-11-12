<template>
  <div class="background-pattern"></div>
  <header>
    <div class="header-content">
      <div class="title">天津南港危化品智慧物流综合服务中心</div>
      <div class="sys-link" v-if="nav_link">
        <span @click="handleTo({ path: nav_link.path })">{{ nav_link.fullName }}</span>
      </div>
      <div class="user" v-if="userStore?.info?.userName">
        <span>{{ userStore.info.userName }} ，欢迎登录 </span>
        <img @click="handleLogout" src="@/assets/images/nav/logout.png" alt="" />
      </div>
    </div>
  </header>

  <main class="main-content">
    <div class="card-container">
      <!-- 系统导航卡片 -->
      <div class="card-item">
        <div class="card-header">
          <div class="card-icon">
            <img src="@/assets/images/nav/nav_1.png" alt="" />
          </div>
          <h2 class="card-title">系统导航</h2>
        </div>
        <div class="card-body">
          <div class="menu-item" v-for="(item, index) in nav_list1" :key="index" @click="handleTo(item)">
            <div class="menu-item_label">{{ item.fullName }}</div>
            <img class="menu-item_icon_1" src="@/assets/images/nav/icon_right1.png" alt="" />
            <img class="menu-item_icon_2" src="@/assets/images/nav/icon_right2.png" alt="" />
          </div>
        </div>
      </div>

      <!-- 快捷链接卡片 -->
      <div class="card-item">
        <div class="card-header">
          <div class="card-icon">
            <img src="@/assets/images/nav/nav_2.png" alt="" />
          </div>
          <h2 class="card-title">快捷链接</h2>
        </div>
        <div class="card-body is-center">
          <div class="menu-item" v-for="(item, index) in nav_list2" :key="index" @click="handleTo(item)">
            <div class="menu-item_label">{{ item.fullName }}</div>
            <img class="menu-item_icon_1" src="@/assets/images/nav/icon_right1.png" alt="" />
            <img class="menu-item_icon_2" src="@/assets/images/nav/icon_right2.png" alt="" />
          </div>
        </div>
      </div>

      <!-- 移动端扫码卡片 -->
      <div class="card-item">
        <div class="card-header">
          <div class="card-icon">
            <img src="@/assets/images/nav/nav_3.png" alt="" />
          </div>
          <h2 class="card-title">浏览器扫码</h2>
        </div>
        <div class="card-body">
          <div class="qr-code">
            <!-- 使用示例二维码图片 -->
            <img src="/qrcode.png" alt="移动端二维码，扫码可访问相关服务" />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, unref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/store/modules/user";
import { logout } from "@/utils/common";
import { ElMessageBox } from "element-plus/es";
import { getToken } from "@/utils/token-util";
import { getUserInfo } from "@/api/layout";

const { t } = useI18n();
const sceneRouter = useRouter();
const { currentRoute } = sceneRouter;

const userStore = useUserStore();

const token = getToken()?.replace("bearer ", "");

interface MenuItem {
  id: string;
  fullName: string;
  enCode: string;
  parentId: string;
  icon: string | null;
  hasChildren: boolean;
  urlAddress: string | null;
  path: string | null;
  visible: string;
  linkTarget: string;
  children: MenuItem[] | null;
  type?: number;
  propertyJson: string;
  sortCode: number;
  systemId: string;
}

const nav_list1 = computed<MenuItem[]>(() => {
  return menuList.value.find(item => item.enCode == "xtdh")?.children ?? [];
});

const nav_list2 = computed<MenuItem[]>(() => {
  return menuList.value.find(item => item.enCode == "kjlj")?.children ?? [];
});

const nav_link = computed<MenuItem | null>(() => menuList.value.find(item => item.enCode == "syslink") ?? null);

const handleLogout = () => {
  // 退出登录
  ElMessageBox.confirm(t("layout.logout.message"), t("layout.logout.title"), { type: "warning", draggable: true }).then(() => {
    logout(false, unref(currentRoute).fullPath);
    userStore.$reset();
  });
};

const deploymentHomePath = (value, code) => {
  if (code === "syslink") return "/zhumadian/admin/";

  if (typeof value !== "string") return value;
  const legacy = "/tianjinrisk";
  const deployed = "/zhumadian";
  const delimiter = value.search(/[?#]/);
  const path = delimiter < 0 ? value : value.slice(0, delimiter);
  if (path === legacy || path.startsWith(legacy + "/")) {
    return deployed + value.slice(legacy.length);
  }
  return value;
};

const handleTo = item => {
  if (!item.path) return;
  if (item.enCode == "mjyjzh") {
    void sceneRouter.push("/sceneViewer");
    return;
  }
  window.open(deploymentHomePath(item.path, item.enCode), "_blank");
};

const menuList = ref<MenuItem[]>([]);

onMounted(async () => {
  const res: any = await getUserInfo("home");
  menuList.value = res.data.menuList;
});
</script>

<style lang="scss" scoped>
// 变量定义
$primary-color: #0a2463;
$secondary-color: #1e3a8a;
$accent-color: #3b82f6;
$light-accent: #93c5fd;
$text-color: #ffffff;
$card-bg: #011939;
$border-radius: 8px;
$shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
$transition: all 0.3s ease;

// 基础样式
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

// 背景装饰
.background-pattern {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url("@/assets/images/nav/background.png");
  background-size: 100% 100%;
  z-index: -1;
}

// 头部样式
header {
  background-image: url("@/assets/images/nav/header.png");
  background-size: 100% 100%;
  position: relative;
  overflow: hidden;
  .header-content {
    display: flex;
    height: 60px;
    justify-content: center;
    align-items: center;
    margin: 0 auto;
  }
  .title {
    font-family: YouSheBiaoTiHei;
    font-size: 30px;
    color: $text-color;
  }
  .user {
    position: absolute;
    right: 40px;
    top: 40px;
    color: #fff;
    font-size: 16px;
    display: flex;
    align-items: center;
    color: #c3d1dc;
    img {
      width: 15px;
      height: 15px;
      margin-left: 10px;
      cursor: pointer;
    }
  }
  .sys-link {
    position: absolute;
    right: 40px;
    top: 6px;
    color: #c3d1dc;
    text-decoration: none;
    margin-left: 10px;
    cursor: pointer;
    &:hover {
      color: $accent-color;
    }
  }
}

// 主体内容样式
.main-content {
  margin: 0 auto;
  padding: 40px;
}

.card-container {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 5rem;
  margin-top: 15rem;
}

.card-item {
  min-width: 0;
  background: $card-bg;
  border-radius: $border-radius;
  padding: 20px;
  box-shadow: $shadow;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(59, 130, 246, 0.3);
  transition: $transition;

  &:hover {
    &:hover {
      box-shadow: 0 0 30px #0456a8 inset;
      .card-title::after {
        display: block;
      }
    }
  }
  .card-header {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 24px;
    .card-icon {
      left: 50%;
      top: -80px;
      transform: translateX(-50%);
      position: absolute;
      width: 300px;
      height: 140px;
      img {
        width: 100%;
      }
    }
  }
  .card-title {
    margin-top: 80px;
    position: relative;
    font-size: 32px;
    color: #fff;
    font-family: YouSheBiaoTiHei;
    font-weight: normal;
    &::after {
      display: none;
      position: absolute;
      content: "";
      left: 50%;
      top: 5%;
      transform: translateX(-50%);
      width: 200px;
      height: 100px;
      background-image: url("@/assets/images/nav/title_line.png");
      background-size: 100% 100%;
    }
  }

  .card-body {
    margin-top: 45px;
    .menu-item {
      height: 70px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: #0c3774;
      padding: 0 20px;
      margin-bottom: 20px;
      border-radius: 5px;
      border: 1px solid transparent;
      cursor: pointer;
      .menu-item_label {
        color: #abbfda;
        font-size: 18px;
        white-space: nowrap;
      }
      .menu-item_icon_1 {
        width: 27px;
        height: 21px;
      }
      .menu-item_icon_2 {
        display: none;
        height: 18px;
      }
      &:hover {
        box-shadow: 0 0 30px #0456a8 inset;
        border-color: #0456a8;
        background-color: transparent;
        .menu-item_label {
          color: #3489e4;
          font-size: 20px;
        }
        .menu-item_icon_1 {
          display: none;
        }
        .menu-item_icon_2 {
          display: block;
        }
      }
    }
    &.is-center {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      grid-template-rows: repeat(3, 1fr);
      grid-column-gap: 20px;
    }
  }
}

// 二维码样式
.qr-code {
  background: white;
  padding: 10px;
  border-radius: 4px;
  display: inline-block;
  margin: 15px auto;
  position: relative;
  left: 50%;
  transform: translateX(-50%);

  img {
    width: 200px;
    display: block;
  }
}

@media (min-width: 5824px) {
  header {
    .header-content {
      position: relative;
      height: 200px;
      width: 100%;
      .title {
        font-size: 100px;
      }
      .user {
        right: 180px;
        top: 120px;
        font-size: 48px;

        img {
          width: 40px;
          height: 40px;
          margin-left: 50px;
        }
      }
    }
  }

  .main-content {
    margin-top: 400px;
  }

  .card-item {
    padding: 80px;
    .card-header {
      margin-bottom: 80px;
      .card-icon {
        top: -240px;
        width: 600px;
        height: 440px;
      }
      .card-title {
        margin-top: 160px;
        font-size: 90px;
        &::after {
          width: 400px;
          height: 280px;
        }
      }
    }
    .card-body {
      margin-top: 140px;
      .menu-item {
        height: 180px;
        padding: 0 60px;
        margin-bottom: 80px;
        border-radius: 15px;
        border: 3px solid transparent;
        .menu-item_label {
          font-size: 50px;
        }
        .menu-item_icon_1 {
          width: 87px;
          height: 81px;
        }
        .menu-item_icon_2 {
          height: 60px;
        }
        &:hover {
          box-shadow: 0 0 120px #0456a8 inset;
          .menu-item_label {
            font-size: 65px;
          }
        }
      }
      &.is-center {
        grid-column-gap: 100px;
      }
    }
  }
  .qr-code {
    padding: 35px;
    border-radius: 10px;
    img {
      width: 600px;
    }
  }
}

@media (min-width: 1920px) {
  .main-content {
    width: 80%;
  }
}

// 响应式设计
@media (max-width: 1024px) {
  .card-container {
    grid-template-columns: repeat(2, 1fr);
  }

  .card:last-child {
    grid-column: span 2;
    max-width: 500px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .card-container {
    grid-template-columns: 1fr;
  }

  .card-body.is-center {
    grid-template-columns: 1fr !important;
  }

  .card:last-child {
    grid-column: span 1;
    max-width: none;
  }

  .logo {
    font-size: 1.2rem;
  }

  main {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .card {
    padding: 1rem;
  }

  .card-title {
    font-size: 1rem;
  }

  .btn {
    padding: 0.6rem;
    font-size: 0.9rem;
  }
}
</style>
