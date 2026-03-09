<template>
  <div class="rag-search">
    <div class="rag-header">
      <h2>RAG检索</h2>
      <p class="rag-description">输入关键词进行文档检索</p>
    </div>
    
    <div class="rag-input">
      <input 
        type="text" 
        v-model="searchQuery"
        @keyup.enter="search"
        placeholder="请输入检索关键词..."
        :disabled="isLoading"
      />
      <button @click="search" :disabled="isLoading || !searchQuery.trim()">
        <span v-if="isLoading" class="loading-spinner small"></span>
        {{ isLoading ? '检索中...' : '检索' }}
      </button>
    </div>
    
    <div class="rag-results" v-if="results">
      <div class="results-header">
        <h3>检索结果</h3>
        <button class="clear-btn" @click="clearResults">清空</button>
      </div>
      <div class="results-content">
        <pre>{{ results.response }}</pre>
      </div>
    </div>
    
    <div class="rag-error" v-if="error">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="search">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ragQuery } from '../services/api';

const searchQuery = ref('');
const results = ref<any>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);

// 执行检索
const search = async () => {
  const query = searchQuery.value.trim();
  if (!query) return;
  
  // 清空之前的结果和错误
  results.value = null;
  error.value = null;
  
  // 显示加载状态
  isLoading.value = true;
  
  try {
    // 调用API进行检索
    const response = await ragQuery(query);
    results.value = response;
  } catch (err) {
    error.value = '检索失败，请稍后再试';
    console.error('RAG search error:', err);
  } finally {
    // 隐藏加载状态
    isLoading.value = false;
  }
};

// 清空结果
const clearResults = () => {
  results.value = null;
  searchQuery.value = '';
};
</script>

<style scoped>
.rag-search {
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 1rem 0;
}

.rag-header {
  margin-bottom: 1rem;
}

.rag-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
  color: #333;
}

.rag-description {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
}

.rag-input {
  display: flex;
  margin-bottom: 1.5rem;
}

.rag-input input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  margin-right: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.rag-input input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.rag-input input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.rag-input button {
  display: flex;
  align-items: center;
  padding: 0.8rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.rag-input button:hover:not(:disabled) {
  background-color: #45a049;
}

.rag-input button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
}

.rag-results {
  margin-top: 1rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
}

.results-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
}

.clear-btn {
  padding: 0.3rem 0.8rem;
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  background-color: #e0e0e0;
}

.results-content {
  background-color: #f9f9f9;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  max-height: 400px;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.results-content:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.results-content pre {
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #333;
}

.rag-error {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 6px;
  color: #c62828;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rag-error p {
  margin: 0;
  flex: 1;
}

.retry-btn {
  padding: 0.3rem 0.8rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease;
  margin-left: 1rem;
}

.retry-btn:hover {
  background-color: #45a049;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 滚动条样式 */
.results-content::-webkit-scrollbar {
  width: 6px;
}

.results-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.results-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.results-content::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>