<template>
  <div class="chat-container">
    <!-- 会话管理界面 -->
    <div class="centered-content" v-if="showSessionManagerFlag">
      <SessionManager
        :currentSessionId="currentSessionId"
        @sessionChange="handleSessionChange"
        @sessionDelete="handleSessionDelete"
      />
    </div>

    <!-- 历史会话列表 -->
    <div class="session-list-overlay" v-if="showSessionListFlag">
      <div class="session-list-container">
        <div class="session-list-header">
          <h2>历史会话</h2>
          <button class="close-btn" @click="showSessionListFlag = false">×</button>
        </div>
        <div class="session-list-content">
          <div v-if="isLoadingSessions" class="loading-state">
            <div class="loading-spinner"></div>
            <span>加载中...</span>
          </div>
          <div v-else-if="sessionError" class="error-state">
            <span>{{ sessionError }}</span>
            <button @click="loadSessions">重试</button>
          </div>
          <div v-else>
            <div
              v-for="sessionId in recentSessions"
              :key="sessionId"
              :class="['session-item', { active: currentSessionId === sessionId }]"
              @click="switchToSession(sessionId)"
            >
              <span class="session-id">{{ sessionId }}</span>
            </div>
            <div v-if="recentSessions.length === 0" class="empty-sessions">暂无历史会话</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 聊天界面 -->
    <div class="chat-main" v-else>
      <div class="chat-header">
        <h1>智能客服</h1>
        <div class="header-right">
          <div class="session-info" v-if="currentSessionId">会话: {{ currentSessionId }}</div>
          <div class="menu-container">
            <button class="menu-btn" @click="toggleMenu">☰</button>
            <div class="menu" v-if="menuOpen">
              <div class="menu-item" @click="showSessionList">切换历史会话</div>
              <div class="menu-item" @click="toggleSessionManager">管理历史会话</div>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
          <div class="message-content" v-if="message.type === 'user'">
            {{ message.content }}
          </div>
          <div class="message-content" v-else v-html="renderMarkdown(message.content)"></div>
        </div>
        <div v-if="isLoading" class="message loading">
          <div class="loading-spinner"></div>
          <span>正在思考...</span>
        </div>
      </div>

      <div class="chat-input">
        <input
          type="text"
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          placeholder="请输入您的问题..."
          :disabled="isLoading"
        />
        <button @click="sendMessage" :disabled="isLoading || !inputMessage.trim()">发送</button>
      </div>

      <!-- 错误提示 -->
      <div class="error-toast" v-if="error">
        <span>{{ error }}</span>
        <button @click="error = null">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { marked } from 'marked'
import {
  agentQuery,
  agentQueryStream,
  getCurrentSessionId,
  setCurrentSessionId,
  clearCurrentSessionId,
  generateNewSessionId,
} from '../services/api'
import SessionManager from '../components/SessionManager.vue'

// 配置 marked 库以支持所有基础 Markdown 语法

// 配置 marked 选项
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true, // 支持 GitHub Flavored Markdown
  headerIds: true, // 为标题添加 ID
  mangle: false, // 不混淆邮件地址
  silent: false, // 显示错误
  highlight: (code, lang) => {
    // 可以添加代码高亮逻辑
    return code
  },
  // 支持脚注
  footnotes: true,
})

// 缓存渲染结果，避免重复渲染相同内容
const markdownCache = new Map<string, string>()

// 确保 marked 函数在模板中可用
const renderMarkdown = (content: string) => {
  // 检查缓存
  if (markdownCache.has(content)) {
    return markdownCache.get(content)!
  }

  // 渲染并缓存结果
  const rendered = marked(content)
  markdownCache.set(content, rendered)

  // 限制缓存大小，避免内存占用过高
  if (markdownCache.size > 50) {
    // 删除最早的缓存项
    const firstKey = markdownCache.keys().next().value
    markdownCache.delete(firstKey)
  }

  return rendered
}

interface Message {
  type: 'user' | 'bot'
  content: string
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const currentSessionId = ref<string | null>(getCurrentSessionId())
const error = ref<string | null>(null)
const menuOpen = ref(false)
const showSessionManagerFlag = ref(false)
const showSessionListFlag = ref(false)
const recentSessions = ref<string[]>([])
const isLoadingSessions = ref(false)
const sessionError = ref<string | null>(null)

// 滚动到最新消息
const scrollToBottom = () => {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 100)
}

// 发送消息
const sendMessage = () => {
  const message = inputMessage.value.trim()
  if (!message) return

  // 清空错误提示
  error.value = null

  // 添加用户消息
  messages.value.push({ type: 'user', content: message })
  inputMessage.value = ''
  scrollToBottom()

  // 显示加载状态
  isLoading.value = true

  // 添加一个临时的机器人消息，用于流式输出
  const botMessageIndex = messages.value.length
  messages.value.push({ type: 'bot', content: '' })

  // 调用流式API
  const closeStream = agentQueryStream(
    message,
    currentSessionId.value || undefined,
    (chunk, sessionId) => {
      // 更新当前会话ID
      currentSessionId.value = sessionId
      setCurrentSessionId(sessionId)

      // 更新机器人消息内容
      if (messages.value[botMessageIndex]) {
        messages.value[botMessageIndex].content += chunk
        scrollToBottom()
      }
    },
    () => {
      // 流式输出完成
      isLoading.value = false
      scrollToBottom()
    },
    (err) => {
      // 处理错误
      const errorMessage = '抱歉，我暂时无法回答您的问题，请稍后再试。'
      if (messages.value[botMessageIndex]) {
        messages.value[botMessageIndex].content = errorMessage
      } else {
        messages.value.push({ type: 'bot', content: errorMessage })
      }
      error.value = errorMessage
      console.error('API error:', err)

      // 隐藏加载状态
      isLoading.value = false
      scrollToBottom()

      // 3秒后自动关闭错误提示
      setTimeout(() => {
        error.value = null
      }, 3000)
    },
  )

  // 可以在需要时调用closeStream()来关闭流
}

// 监听消息变化，自动滚动到底部
watch(
  messages,
  () => {
    scrollToBottom()
  },
  { deep: true },
)

// 切换菜单
const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

// 显示会话列表
const showSessionList = () => {
  showSessionListFlag.value = true
  menuOpen.value = false
  loadSessions()
}

// 加载会话列表
const loadSessions = async () => {
  isLoadingSessions.value = true
  sessionError.value = null
  try {
    const { getSessions } = await import('../services/api')
    const response = await getSessions()
    recentSessions.value = response.sessions
  } catch (err) {
    sessionError.value = '加载会话失败'
    console.error('Failed to load sessions:', err)
  } finally {
    isLoadingSessions.value = false
  }
}

// 切换到指定会话
const switchToSession = async (sessionId: string) => {
  isLoadingSessions.value = true
  sessionError.value = null
  try {
    const { getSessionHistory, setCurrentSessionId } = await import('../services/api')
    const history = await getSessionHistory(sessionId)
    // 清空当前消息
    messages.value = []
    // 添加历史消息
    history.history.forEach(([userMsg, botMsg]) => {
      messages.value.push({ type: 'user', content: userMsg })
      messages.value.push({ type: 'bot', content: botMsg })
    })
    // 更新当前会话ID
    currentSessionId.value = sessionId
    setCurrentSessionId(sessionId)
    // 关闭会话列表
    showSessionListFlag.value = false
    // 滚动到底部
    scrollToBottom()
  } catch (err) {
    sessionError.value = '加载会话历史失败'
    console.error('Failed to load session history:', err)
  } finally {
    isLoadingSessions.value = false
  }
}

// 切换会话管理界面
const toggleSessionManager = () => {
  showSessionManagerFlag.value = !showSessionManagerFlag.value
  menuOpen.value = false
}

// 处理会话切换
const handleSessionChange = (sessionId: string, history: [string, string][]) => {
  // 清空当前消息
  messages.value = []
  // 添加历史消息
  history.forEach(([userMsg, botMsg]) => {
    messages.value.push({ type: 'user', content: userMsg })
    messages.value.push({ type: 'bot', content: botMsg })
  })
  // 更新当前会话ID
  currentSessionId.value = sessionId
  setCurrentSessionId(sessionId)
  // 关闭会话管理界面
  showSessionManagerFlag.value = false
  // 滚动到底部
  scrollToBottom()
}

// 处理会话删除
const handleSessionDelete = (sessionId: string) => {
  // 如果删除的是当前会话，清空消息并创建新会话
  if (currentSessionId.value === sessionId) {
    messages.value = []
    currentSessionId.value = null
    clearCurrentSessionId()
    // 添加欢迎消息
    messages.value.push({
      type: 'bot',
      content: '您好！我是智能客服助手，有什么可以帮到您的吗？',
    })
    scrollToBottom()
  }
  // 关闭会话管理界面
  showSessionManagerFlag.value = false
}

// 页面加载时添加欢迎消息
onMounted(() => {
  // 生成新的会话ID
  const newSessionId = generateNewSessionId()
  currentSessionId.value = newSessionId
  setCurrentSessionId(newSessionId)

  if (messages.value.length === 0) {
    messages.value.push({
      type: 'bot',
      content: '您好！我是智能客服助手，有什么可以帮到您的吗？',
    })
    scrollToBottom()
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
  padding: 1rem;
}

.centered-content {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.centered-content :deep(.session-manager) {
  width: 100%;
  max-width: 600px;
  height: 90vh;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.chat-main {
  width: 100%;
  max-width: 800px;
  height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.chat-header {
  background-color: #4caf50;
  color: white;
  padding: 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.session-info {
  font-size: 0.9rem;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
}

.menu-container {
  position: relative;
}

.menu-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.menu-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 150px;
  z-index: 1000;
}

.menu-item {
  padding: 0.8rem 1rem;
  cursor: pointer;
  color: #333;
  transition: background-color 0.3s ease;
}

.menu-item:first-child {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.menu-item:last-child {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.menu-item:hover {
  background-color: #f5f5f5;
}

.chat-messages {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.message {
  margin-bottom: 1.2rem;
  max-width: 80%;
  animation: fadeIn 0.3s ease;
  display: flex;
  align-items: flex-end;
}

.message-content {
  padding: 0.8rem 1rem;
  border-radius: 18px;
  word-wrap: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message.user {
  align-self: flex-end;
  margin-left: auto;
  flex-direction: row-reverse;
}

.message.user .message-content {
  background-color: #4caf50;
  color: white;
  border-radius: 18px;
}

.message.bot {
  align-self: flex-start;
  margin-right: auto;
}

.message.bot .message-content {
  background-color: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-radius: 18px;
}

.message.loading {
  align-self: flex-start;
  display: flex;
  align-items: center;
  color: #666;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

.chat-input {
  display: flex;
  padding: 1.2rem;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.chat-input input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  margin-right: 0.8rem;
  font-size: 1rem;
  transition:
    border-color 0.3s ease,
    box-shadow 0.3s ease;
}

.chat-input input:focus {
  outline: none;
  border-color: #4caf50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.chat-input input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.chat-input button {
  padding: 0.8rem 1.5rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 1rem;
  transition:
    background-color 0.3s ease,
    transform 0.1s ease;
}

.chat-input button:hover:not(:disabled) {
  background-color: #45a049;
  transform: translateY(-1px);
}

.chat-input button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
  transform: none;
}

.error-toast {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #f44336;
  color: white;
  padding: 0.8rem 1.2rem;
  border-radius: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  z-index: 1000;
  animation: slideUp 0.3s ease;
}

.error-toast span {
  margin-right: 1rem;
}

.error-toast button {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* 历史会话列表样式 */
.session-list-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.session-list-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.session-list-header {
  background-color: #4caf50;
  color: white;
  padding: 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-list-header h2 {
  margin: 0;
  font-size: 1.3rem;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.session-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.session-item {
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  background-color: #f5f5f5;
  color: #333;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.session-item:hover {
  background-color: #e8f5e8;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.session-item.active {
  background-color: #4caf50;
  color: white;
}

.session-id {
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.error-state button:hover {
  background-color: #45a049;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
  transition: background 0.3s ease;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* Markdown 样式 */
.message.bot .message-content {
  line-height: 1.6;
}

/* 标题样式 */
.message.bot .message-content h1,
.message.bot .message-content h2,
.message.bot .message-content h3,
.message.bot .message-content h4,
.message.bot .message-content h5,
.message.bot .message-content h6 {
  margin-top: 1.2rem;
  margin-bottom: 0.6rem;
  font-weight: 600;
  color: #333;
}

.message.bot .message-content h1 {
  font-size: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.3rem;
}

.message.bot .message-content h2 {
  font-size: 1.3rem;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 0.2rem;
}

.message.bot .message-content h3 {
  font-size: 1.1rem;
}

.message.bot .message-content h4 {
  font-size: 1rem;
}

.message.bot .message-content h5 {
  font-size: 0.9rem;
}

.message.bot .message-content h6 {
  font-size: 0.8rem;
  color: #666;
}

/* 列表样式 */
.message.bot .message-content ul,
.message.bot .message-content ol {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1.8rem;
}

.message.bot .message-content ul {
  list-style-type: disc;
}

.message.bot .message-content ol {
  list-style-type: decimal;
}

.message.bot .message-content li {
  margin-bottom: 0.3rem;
}

.message.bot .message-content ul ul,
.message.bot .message-content ol ol,
.message.bot .message-content ul ol,
.message.bot .message-content ol ul {
  margin-top: 0.2rem;
  margin-bottom: 0.2rem;
}

/* 链接样式 */
.message.bot .message-content a {
  color: #4caf50;
  text-decoration: none;
  transition: color 0.3s ease;
}

.message.bot .message-content a:hover {
  color: #45a049;
  text-decoration: underline;
}

/* 代码样式 */
.message.bot .message-content code {
  background-color: #f5f5f5;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
  color: #e91e63;
}

.message.bot .message-content pre {
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.8rem 0;
  border: 1px solid #e0e0e0;
}

.message.bot .message-content pre code {
  background-color: transparent;
  padding: 0;
  color: #333;
}

/* 引用样式 */
.message.bot .message-content blockquote {
  border-left: 4px solid #4caf50;
  padding-left: 1.2rem;
  margin: 0.8rem 0;
  font-style: italic;
  color: #666;
  background-color: #f9f9f9;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border-radius: 0 4px 4px 0;
}

/* 水平分隔线 */
.message.bot .message-content hr {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 1.2rem 0;
}

/* 表格样式 */
.message.bot .message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8rem 0;
  font-size: 0.9rem;
}

.message.bot .message-content th,
.message.bot .message-content td {
  border: 1px solid #e0e0e0;
  padding: 0.6rem;
  text-align: left;
}

.message.bot .message-content th {
  background-color: #f5f5f5;
  font-weight: 600;
}

.message.bot .message-content tr:nth-child(even) {
  background-color: #f9f9f9;
}

/* 粗体和斜体 */
.message.bot .message-content strong {
  font-weight: 600;
  color: #333;
}

.message.bot .message-content em {
  font-style: italic;
  color: #666;
}

/* 任务列表 */
.message.bot .message-content input[type='checkbox'] {
  margin-right: 0.5rem;
}

/* 图片样式 */
.message.bot .message-content img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 0.8rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 脚注样式 */
.message.bot .message-content .footnote-ref {
  font-size: 0.8rem;
  vertical-align: super;
  margin-left: 0.2rem;
  color: #4caf50;
}

.message.bot .message-content .footnotes {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  font-size: 0.9rem;
  color: #666;
}

.message.bot .message-content .footnotes ol {
  margin-top: 0.5rem;
  padding-left: 1.5rem;
}

.message.bot .message-content .footnotes li {
  margin-bottom: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-main {
    width: 100%;
    height: 100vh;
    border-radius: 0;
  }

  .chat-header {
    padding: 1rem;
  }

  .chat-header h1 {
    font-size: 1.2rem;
  }

  .header-right {
    gap: 0.5rem;
  }

  .session-info {
    font-size: 0.8rem;
    padding: 0.2rem 0.6rem;
  }

  .menu-btn {
    font-size: 1rem;
    padding: 0.2rem 0.4rem;
  }

  .chat-messages {
    padding: 1rem;
  }

  .chat-input {
    padding: 1rem;
  }

  .session-list-container {
    width: 95%;
    max-height: 90vh;
  }

  .session-list-header {
    padding: 1rem;
  }

  .session-list-header h2 {
    font-size: 1.1rem;
  }

  .session-list-content {
    padding: 0.8rem;
  }

  .session-item {
    padding: 0.6rem;
  }
}

@media (max-width: 480px) {
  .header-right {
    flex-direction: column;
    align-items: flex-end;
    gap: 0.3rem;
  }

  .session-info {
    font-size: 0.7rem;
  }

  .menu {
    min-width: 120px;
  }

  .menu-item {
    padding: 0.6rem 0.8rem;
    font-size: 0.9rem;
  }
}
</style>
