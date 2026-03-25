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
      
      <div class="register-form">
        <van-cell-group inset>
          <van-field
            v-model="form.username"
            placeholder="请输入用户名"
            :rules="usernameRules"
            required
            left-icon="user-o"
            @blur="validateUsername"
          />
          
          <van-field
            v-model="form.email"
            placeholder="请输入邮箱地址"
            :rules="emailRules"
            required
            type="email"
            left-icon="envelop-o"
            @blur="validateEmail"
          />
          
          <van-field
            v-model="form.telephone"
            placeholder="请输入手机号码（选填）"
            type="tel"
            left-icon="phone"
            maxlength="11"
          />
          
          <van-field
            v-model="form.password"
            placeholder="请输入密码（6-20位）"
            :rules="passwordRules"
            required
            type="password"
            left-icon="lock"
            @blur="validatePassword"
          />
          
          <van-field
            v-model="form.confirm_password"
            placeholder="请确认密码"
            :rules="confirmPasswordRules"
            required
            type="password"
            left-icon="lock"
            @blur="validateConfirmPassword"
          />
        </van-cell-group>
        
        <div class="register-btn-container">
          <van-button
            type="primary"
            block
            :loading="loading"
            @click="handleRegister"
          >
            {{ loading ? '注册中...' : '注册' }}
          </van-button>
        </div>
      </div>
      
      <div class="login-link">
        已有账号？<span @click="goToLogin">去登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { showToast, showDialog } from 'vant';
import { useUserStore } from '../store/user';

const router = useRouter();
const userStore = useUserStore();

const loading = ref(false);

const form = reactive({
  username: '',
  email: '',
  telephone: '',
  password: '',
  confirm_password: ''
});

const usernameRules = [
  { required: true, message: '请输入用户名' }
];

const emailRules = [
  { required: true, message: '请输入邮箱地址' },
  { pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, message: '请输入正确的邮箱地址' }
];

const passwordRules = [
  { required: true, message: '请输入密码' },
  { pattern: /^.{6,20}$/, message: '密码长度应为6-20位' }
];

const confirmPasswordRules = [
  { required: true, message: '请确认密码' }
];

const validateUsername = () => {
  if (!form.username) {
    showToast('请输入用户名');
    return false;
  }
  return true;
};

const validateEmail = () => {
  if (!form.email) {
    showToast('请输入邮箱地址');
    return false;
  }
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(form.email)) {
    showToast('请输入正确的邮箱地址');
    return false;
  }
  return true;
};

const validatePassword = () => {
  if (!form.password) {
    showToast('请输入密码');
    return false;
  }
  if (form.password.length < 6 || form.password.length > 20) {
    showToast('密码长度应为6-20位');
    return false;
  }
  return true;
};

const validateConfirmPassword = () => {
  if (!form.confirm_password) {
    showToast('请确认密码');
    return false;
  }
  if (form.password !== form.confirm_password) {
    showToast('两次输入的密码不一致');
    return false;
  }
  return true;
};

const validateForm = () => {
  return validateUsername() && validateEmail() && validatePassword() && validateConfirmPassword();
};

const handleRegister = async () => {
  console.log('handleRegister函数被调用');
  console.log('表单数据:', form);
  
  if (!validateForm()) {
    console.log('表单验证失败');
    return;
  }
  
  console.log('表单验证通过，开始注册');
  loading.value = true;
  
  try {
    console.log('调用userStore.register方法');
    const result = await userStore.register(form);
    
    console.log('注册结果:', result);
    
    if (result.success) {
      showToast({
        message: result.message,
        position: 'top'
      });
      
      // 注册成功后跳转到对话页面
      setTimeout(() => {
        router.push('/aichat');
      }, 1500);
    } else {
      showToast({
        message: result.message,
        position: 'top',
        type: 'fail'
      });
    }
  } catch (error) {
    console.error('注册失败:', error);
    showToast({
      message: '注册失败，请稍后重试',
      position: 'top',
      type: 'fail'
    });
  } finally {
    loading.value = false;
  }
};

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
  padding-bottom: 20px;
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

.register-form {
  padding: 0 16px;
}

.register-btn-container {
  margin-top: 24px;
  padding: 0 16px;
}

.login-link {
  text-align: center;
  margin-top: 24px;
  color: #969799;
  font-size: 14px;
}

.login-link span {
  color: #1989fa;
}
</style>