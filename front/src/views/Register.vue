<template>
  <div class="register-page">
    <van-nav-bar
      title="用户注册"
      left-arrow
      @click-left="onClickLeft"
      fixed
    />
    
    <div class="register-container">
      <div class="register-logo">
        <van-image
          width="80"
          height="80"
          src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
          round
        />
        <h2>用户注册</h2>
      </div>
      
      <div class="register-tips">
        <van-icon name="info-circle" color="#1989fa" />
        <p>注册功能暂时不可用，请联系管理员获取账号</p>
      </div>
      
      <div class="login-link">
        已有账号？<span @click="goToLogin">去登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useUserStore } from '../store/user';

const router = useRouter();
const userStore = useUserStore();

const onClickLeft = () => {
  router.back();
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.register-container {
  padding-top: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.register-logo {
  margin: 40px 0;
  text-align: center;
}

.register-logo h2 {
  margin-top: 16px;
  color: #323233;
  font-size: 22px;
}

.register-tips {
  width: 90%;
  padding: 20px;
  background-color: #f0f9ff;
  border-radius: 8px;
  text-align: center;
  margin: 20px 0;
  border: 1px solid #e6f7ff;
}

.register-tips p {
  margin: 10px 0 0 0;
  color: #666;
  font-size: 16px;
}

.login-link {
  text-align: center;
  margin-top: 40px;
  color: #969799;
  font-size: 14px;
}

.login-link span {
  color: #1989fa;
}
</style>