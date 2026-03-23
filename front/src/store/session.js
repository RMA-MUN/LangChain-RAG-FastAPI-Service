import { defineStore } from 'pinia';
import axios from 'axios';
import { apiConfig } from '../config/api';

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [],
    currentSession: null,
    loading: false
  }),
  
  getters: {
    getSessions: (state) => state.sessions,
    getCurrentSession: (state) => state.currentSession,
    isLoading: (state) => state.loading
  },
  
  actions: {
    // 获取用户的所有会话
    async getUserSessions(userId) {
      try {
        this.loading = true;
        const token = localStorage.getItem('jwt_token');
        
        const response = await axios.get(`${apiConfig.endpoints.getUserSessions}/${userId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        // 正确处理响应数据，从 response.data.data.sessions 获取会话ID数组
        const sessionIds = response.data.data?.sessions || [];
        
        // 将会话ID转换为包含session_id属性的对象数组
        this.sessions = sessionIds.map(sessionId => ({
          session_id: sessionId
        }));
        
        // 调试信息：打印会话列表
        console.log('获取到的会话列表:', this.sessions);
        return {
          success: true,
          data: this.sessions
        };
      } catch (error) {
        console.error('获取用户会话失败:', error);
        return {
          success: false,
          message: error.response?.data?.detail || '获取会话失败'
        };
      } finally {
        this.loading = false;
      }
    },
    
    // 获取单个会话详情
    async getSession(sessionId) {
      try {
        this.loading = true;
        const token = localStorage.getItem('jwt_token');
        
        const response = await axios.get(`${apiConfig.endpoints.getSession}${sessionId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        // 处理可能的包装格式，支持 {code, message, data} 格式
        const sessionData = response.data.data || response.data;
        this.currentSession = sessionData;
        return {
          success: true,
          data: sessionData
        };
      } catch (error) {
        console.error('获取会话详情失败:', error);
        return {
          success: false,
          message: error.response?.data?.detail || '获取会话详情失败'
        };
      } finally {
        this.loading = false;
      }
    },
    
    // 删除会话
    async deleteSession(sessionId) {
      try {
        this.loading = true;
        const token = localStorage.getItem('jwt_token');
        
        await axios.delete(`${apiConfig.endpoints.deleteSession}${sessionId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        // 从本地会话列表中移除
        if (Array.isArray(this.sessions)) {
          this.sessions = this.sessions.filter(session => session.session_id !== sessionId);
        } else {
          // 如果sessions不是数组，重置为空数组
          this.sessions = [];
        }
        
        // 如果删除的是当前会话，清除当前会话
        if (this.currentSession && this.currentSession.session_id === sessionId) {
          this.currentSession = null;
        }
        
        return {
          success: true,
          message: '会话删除成功'
        };
      } catch (error) {
        console.error('删除会话失败:', error);
        return {
          success: false,
          message: error.response?.data?.detail || '删除会话失败'
        };
      } finally {
        this.loading = false;
      }
    },
    
    // 创建新会话（通过发送第一个消息）
    async createSession(query) {
      try {
        this.loading = true;
        const token = localStorage.getItem('jwt_token');
        
        // 发送第一个消息来创建会话
        const response = await fetch(apiConfig.endpoints.agentQueryStream, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            query: query
          })
        });
        
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        // 处理SSE流，获取会话ID
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let sessionId = null;
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (!data) continue;
              
              try {
                const json = JSON.parse(data);
                if (json.session_id) {
                  sessionId = json.session_id;
                  break;
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
          
          if (sessionId) break;
        }
        
        if (sessionId) {
          // 获取新创建的会话详情
          const sessionResponse = await this.getSession(sessionId);
          return sessionResponse;
        } else {
          throw new Error('创建会话失败，未获取到会话ID');
        }
      } catch (error) {
        console.error('创建会话失败:', error);
        return {
          success: false,
          message: error.message || '创建会话失败'
        };
      } finally {
        this.loading = false;
      }
    },
    
    // 设置当前会话
    setCurrentSession(session) {
      this.currentSession = session;
    },
    
    // 清除所有会话
    clearSessions() {
      this.sessions = [];
      this.currentSession = null;
    }
  }
});