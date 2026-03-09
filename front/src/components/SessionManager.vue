<template>
  <div class="session-manager">
    <div class="session-header">
      <h2>会话管理</h2>
    </div>
    
    <div class="session-list">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-else-if="error" class="error-state">
        <span>{{ error }}</span>
        <button @click="loadSessions">重试</button>
      </div>
      <div v-else>
        <div 
          v-for="sessionId in sessions" 
          :key="sessionId"
          :class="['session-item', { active: currentSessionId === sessionId }]"
          @click="switchSession(sessionId)"
        >
          <span class="session-id">{{ sessionId }}</span>
          <button 
            class="delete-btn"
            @click.stop="deleteSession(sessionId)"
            title="删除会话"
            :disabled="isDeleting === sessionId"
          >
            {{ isDeleting === sessionId ? '...' : '×' }}
          </button>
        </div>
        <div v-if="sessions.length === 0" class="empty-sessions">
          暂无会话
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { getSessions, deleteSession as deleteSessionApi, getSessionHistory } from '../services/api';

const props = defineProps<{
  currentSessionId: string | null;
}>();

const emit = defineEmits<{
  (e: 'sessionChange', sessionId: string, history: [string, string][]): void;
  (e: 'sessionDelete', sessionId: string): void;
}>();

const sessions = ref<string[]>([]);
const isLoading = ref(false);
const isDeleting = ref<string | null>(null);
const error = ref<string | null>(null);

// 加载会话列表
const loadSessions = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await getSessions();
    sessions.value = response.sessions;
  } catch (err) {
    error.value = '加载会话失败';
    console.error('Failed to load sessions:', err);
  } finally {
    isLoading.value = false;
  }
};

// 切换会话
const switchSession = async (sessionId: string) => {
  isLoading.value = true;
  error.value = null;
  try {
    const history = await getSessionHistory(sessionId);
    emit('sessionChange', sessionId, history.history);
  } catch (err) {
    error.value = '加载会话历史失败';
    console.error('Failed to load session history:', err);
  } finally {
    isLoading.value = false;
  }
};

// 删除会话
const deleteSession = async (sessionId: string) => {
  if (confirm(`确定要删除会话 ${sessionId} 吗？`)) {
    isDeleting.value = sessionId;
    error.value = null;
    try {
      await deleteSessionApi(sessionId);
      sessions.value = sessions.value.filter(id => id !== sessionId);
      emit('sessionDelete', sessionId);
    } catch (err) {
      error.value = '删除会话失败';
      console.error('Failed to delete session:', err);
    } finally {
      isDeleting.value = null;
    }
  }
};

// 监听当前会话ID变化
watch(() => props.currentSessionId, (newSessionId) => {
  // 可以在这里添加逻辑，比如更新会话列表
  if (newSessionId && !sessions.value.includes(newSessionId)) {
    loadSessions();
  }
});

// 组件挂载时加载会话列表
onMounted(() => {
  loadSessions();
});
</script>

<style scoped>
.session-manager {
  width: 300px;
  border-right: 1px solid #e0e0e0;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.session-header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: white;
}

.session-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.session-item:hover {
  background-color: #f0f0f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.session-item.active {
  background-color: #e8f5e8;
  border-color: #4CAF50;
}

.session-id {
  font-size: 0.9rem;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.delete-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  padding: 0 0.5rem;
  transition: color 0.3s ease;
}

.delete-btn:hover:not(:disabled) {
  color: #f44336;
}

.delete-btn:disabled {
  color: #c1c1c1;
  cursor: not-allowed;
}

.empty-sessions {
  text-align: center;
  padding: 2rem;
  color: #999;
  font-style: italic;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: #666;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 0.5rem;
}

.error-state {
  text-align: center;
  padding: 2rem;
  color: #c62828;
  background-color: #ffebee;
  border-radius: 6px;
  margin: 0.5rem;
}

.error-state button {
  margin-top: 0.5rem;
  padding: 0.3rem 0.8rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.error-state button:hover {
  background-color: #45a049;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 滚动条样式 */
.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>