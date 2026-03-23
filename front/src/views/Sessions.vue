<template>
  <div class="sessions-container">
    <van-nav-bar title="会话管理" fixed />
    
    <div class="sessions-content">
      <div class="sessions-header">
        <h2>历史会话</h2>
        <van-button type="primary" @click="createNewSession">
          新会话
        </van-button>
      </div>
      
      <div v-if="sessionStore.isLoading" class="loading">
        <van-loading type="spinner" color="#1989fa" />
        <p>加载中...</p>
      </div>
      
      <div v-else-if="sessionStore.sessions.length === 0" class="empty-sessions">
        <van-icon name="chat-o" size="64" color="#ccc" />
        <p>暂无会话记录</p>
        <van-button type="primary" @click="createNewSession">
          创建新会话
        </van-button>
      </div>
      
      <div v-else class="sessions-list">
        <van-cell-group>
          <van-cell
            v-for="session in sessionStore.sessions"
            :key="session.session_id"
            :title="getSessionTitle(session)"
            :value="getSessionTime(session)"
            is-link
            @click="selectSession(session)"
            :class="{ active: sessionStore.currentSession?.session_id === session.session_id }"
          >
            <template #right-icon>
              <van-button
                type="danger"
                plain
                size="small"
                @click.stop="deleteSession(session.session_id)"
              >
                删除
              </van-button>
            </template>
          </van-cell>
        </van-cell-group>
      </div>
    </div>
    
    <!-- 新会话对话框 -->
    <van-popup v-model:show="showNewSessionDialog" position="bottom">
      <div class="new-session-dialog">
        <h3>新会话</h3>
        <van-field
          v-model="newSessionQuery"
          type="textarea"
          rows="3"
          placeholder="请输入您的问题..."
          maxlength="200"
        />
        <div class="dialog-buttons">
          <van-button @click="showNewSessionDialog = false">取消</van-button>
          <van-button type="primary" @click="confirmNewSession" :disabled="!newSessionQuery.trim()">
            开始对话
          </van-button>
        </div>
      </div>
    </van-popup>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { showToast, Toast } from 'vant';
import TabBar from '../components/TabBar.vue';
import { useSessionStore } from '../store/session';
import { useUserStore } from '../store/user';

const router = useRouter();
const sessionStore = useSessionStore();
const userStore = useUserStore();

const showNewSessionDialog = ref(false);
const newSessionQuery = ref('');

// 组件挂载时获取会话列表
onMounted(async () => {
  // 检查是否登录
  if (!userStore.getLoginStatus) {
    showToast('请先登录');
    router.push('/login');
    return;
  }
  
  // 获取用户ID（假设从用户信息中获取）
  if (!userStore.userInfo) {
    const result = await userStore.getUserInfoDetail();
    if (!result.success) {
      showToast('获取用户信息失败');
      return;
    }
  }
  
  if (userStore.userInfo) {
    // 调试信息：打印用户信息
    console.log('用户信息:', userStore.userInfo);
    
    // 尝试获取用户ID，支持不同的字段名
    let userId = userStore.userInfo.uuid || userStore.userInfo.id || userStore.userInfo.user_id;
    
    if (userId) {
      await sessionStore.getUserSessions(userId);
    } else {
      // 显示详细的错误信息
      showToast('获取用户ID失败，请检查用户信息结构');
      console.error('用户信息中没有找到ID字段:', userStore.userInfo);
    }
  } else {
    showToast('获取用户信息失败');
  }
});

// 获取会话标题（使用第一条消息作为标题）
const getSessionTitle = (session) => {
  if (session.history && session.history.length > 0) {
    const firstMessage = session.history[0][0]; // 第一条用户消息
    return firstMessage.length > 20 ? firstMessage.substring(0, 20) + '...' : firstMessage;
  }
  return '新会话';
};

// 获取会话时间（这里简化处理，实际应该从会话数据中获取）
const getSessionTime = (session) => {
  return new Date().toLocaleString();
};

// 选择会话
const selectSession = (session) => {
  // 跳转到带会话ID的路由
  router.push(`/aichat/${session.session_id}`);
};

// 删除会话
const deleteSession = async (sessionId) => {
  // 调试信息：打印会话ID
  console.log('删除会话，会话ID:', sessionId);
  
  const result = await sessionStore.deleteSession(sessionId);
  if (result.success) {
    showToast('会话删除成功');
  } else {
    showToast(result.message || '删除失败');
  }
};

// 打开新会话对话框
const createNewSession = () => {
  showNewSessionDialog.value = true;
};

// 确认创建新会话
const confirmNewSession = async () => {
  if (!newSessionQuery.value.trim()) return;
  
  // 显示加载状态，保存返回的toast实例
  const toastInstance = showToast({
    type: 'loading',
    message: '创建会话中...',
    forbidClick: true,
    duration: 0
  });
  
  try {
    const result = await sessionStore.createSession(newSessionQuery.value);
    if (result.success) {
      showToast('会话创建成功');
      showNewSessionDialog.value = false;
      newSessionQuery.value = '';
      // 跳转到聊天页面
      router.push('/aichat');
    } else {
      showToast(result.message || '创建会话失败');
    }
  } catch (error) {
    showToast('创建会话失败');
    console.error('创建会话失败:', error);
  } finally {
    // 使用返回的toast实例进行清除
    toastInstance.clear();
  }
};
</script>

<style scoped>
.sessions-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 46px;
  padding-bottom: 50px;
  box-sizing: border-box;
  background-color: #f7f8fa;
}

.sessions-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sessions-header h2 {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.loading p {
  margin-top: 16px;
  color: #666;
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.empty-sessions p {
  margin: 16px 0;
  color: #999;
}

.sessions-list {
  margin-top: 10px;
}

.active {
  background-color: #f0f9ff !important;
}

.new-session-dialog {
  background-color: #fff;
  border-radius: 16px 16px 0 0;
  padding: 20px;
}

.new-session-dialog h3 {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin: 0 0 20px 0;
  text-align: center;
}

.dialog-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.dialog-buttons van-button {
  flex: 1;
  margin: 0 5px;
}
</style>