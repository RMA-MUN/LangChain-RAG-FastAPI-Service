# FastAPI LangChain 接口文档

## 1. 接口概览

本API提供了基于LangChain的智能对话、RAG检索和文件管理功能，支持JWT认证保护。

### 基础URL
- 本地开发: `http://localhost:8000`
- 生产环境: 根据部署环境配置

### 认证方式
- 使用JWT Bearer认证
- 从Django生成的JWT中提取用户UUID作为用户标识

## 2. 认证说明

所有需要认证的接口都需要在请求头中添加以下认证信息：

```
Authorization: Bearer <your-jwt-token>
```

其中 `<your-jwt-token>` 是从Django认证系统获取的JWT token。

## 3. API 端点

### 3.1 Agent 相关接口

#### 3.1.1 查询Agent流式响应
**POST /api/agent/query/stream**

功能：向Agent发送查询并获取流式响应，支持会话管理。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 否 | 会话ID，不提供则自动生成 |
| query | string | 是 | 查询内容 |

**请求体示例**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "什么是LangChain?"
}
```

**响应格式**：
- 类型: `text/event-stream`
- 数据格式: Server-Sent Events (SSE)

**响应事件**：
| 事件类型 | 描述 | 数据结构 |
|---------|------|---------|
| step | 执行步骤 | `{"type": "step", "content": {"thought": "思考内容", "tool": "工具名称", "tool_input": {"参数": "值"}, "tool_output": "工具输出"}}` |
| response | 响应内容 | `{"type": "response", "content": "响应片段", "session_id": "会话ID"}` |
| done | 结束标记 | `{"type": "done", "session_id": "会话ID"}` |
| error | 错误信息 | `{"type": "error", "content": "错误信息", "session_id": "会话ID"}` |

**示例响应**：
```
data: {"type": "step", "content": {"thought": "用户询问什么是LangChain，我需要使用RAG工具来获取相关信息", "tool": "rag_summary_tools", "tool_input": {"query": "LangChain定义"}, "tool_output": "LangChain是一个用于构建基于语言模型的应用程序的框架"}}

data: {"type": "response", "content": "LangChain是一个用于构建基于语言模型的应用程序的框架，它提供了一套工具和接口，帮助开发者更方便地集成语言模型到各种应用场景中。", "session_id": "550e8400-e29b-41d4-a716-446655440000"}

data: {"type": "done", "session_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### 3.2 RAG 相关接口

#### 3.2.1 RAG检索
**POST /api/rag/query**

功能：使用RAG技术检索相关信息并生成摘要。

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| query | string | 是 | 查询内容 |

**请求体示例**：
```json
{
  "query": "LangChain的核心组件有哪些?"
}
```

**响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "RAG检索生成的摘要内容"
  }
}
```

**示例响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "LangChain的核心组件包括：1. LLMs - 语言模型，2. Prompts - 提示模板，3. Chains - 链式调用，4. Agents - 智能代理，5. Memory - 记忆管理，6. Retrievers - 检索器..."
  }
}
```

### 3.3 会话管理接口

#### 3.3.1 获取会话信息
**GET /api/session/{session_id}**

功能：获取指定会话的历史记录，使用user_id验证。

**路径参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "会话ID",
    "history": [
      ["用户问题1", "助手回答1"],
      ["用户问题2", "助手回答2"]
    ]
  }
}
```

**示例请求**：
```bash
GET http://localhost:8000/api/session/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer your-jwt-token
```

**示例响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "history": [
      ["什么是LangChain?", "LangChain是一个用于构建基于语言模型的应用程序的框架..."],
      ["它有哪些核心组件?", "LangChain的核心组件包括：LLMs、Prompts、Chains、Agents、Memory、Retrievers..."]
    ]
  }
}
```

#### 3.3.2 删除会话
**DELETE /api/session/{session_id}**

功能：删除指定会话及其历史记录。

**路径参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应格式**：
```json
{
  "code": 200,
  "message": "Session {session_id} deleted successfully",
  "data": null
}
```

**示例请求**：
```bash
DELETE http://localhost:8000/api/session/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer your-jwt-token
```

**示例响应**：
```json
{
  "code": 200,
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "data": null
}
```

#### 3.3.3 获取所有会话ID
**GET /api/sessions**

功能：获取系统中所有会话的ID。

**响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessions": ["会话ID1", "会话ID2", "会话ID3"]
  }
}
```

**示例请求**：
```bash
GET http://localhost:8000/api/sessions
```

**示例响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessions": ["550e8400-e29b-41d4-a716-446655440000", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
  }
}
```

#### 3.3.4 获取用户所有会话ID
**GET /api/sessions/{user_id}**

功能：获取指定用户的所有会话ID（只能获取自己的会话）。

**路径参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| user_id | string | 是 | 用户ID |

**响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessions": ["会话ID1", "会话ID2"]
  }
}
```

**示例请求**：
```bash
GET http://localhost:8000/api/sessions/12345678-1234-1234-1234-123456789012
Authorization: Bearer your-jwt-token
```

**示例响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessions": ["550e8400-e29b-41d4-a716-446655440000", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
  }
}
```

### 3.4 向量数据库接口

#### 3.4.1 上传单个文件
**POST /api/vector/add/single**

功能：上传单个文件到向量数据库，支持TXT和PDF格式。

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| file | file | 是 | 要上传的文件，支持TXT和PDF格式 |

**响应格式**：
```json
{
  "code": 200,
  "message": "文件 {filename} 已成功上传并存储到向量数据库",
  "data": null
}
```

**示例请求**：
```bash
POST http://localhost:8000/api/vector/add/single
Content-Type: multipart/form-data
Authorization: Bearer your-jwt-token

# 表单数据
file: [选择文件]
```

**示例响应**：
```json
{
  "code": 200,
  "message": "文件 example.pdf 已成功上传并存储到向量数据库",
  "data": null
}
```

**限制**：
- 文件大小不能超过20MB
- 仅支持PDF和TXT文件

#### 3.4.2 上传多个文件
**POST /api/vector/add/multiple**

功能：上传多个文件到向量数据库，支持TXT和PDF格式。

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| files | array[file] | 是 | 要上传的文件列表，支持TXT和PDF格式 |

**响应格式**：
```json
{
  "code": 200,
  "message": "文件 [\"file1.pdf\", \"file2.txt\"] 已成功上传并存储到向量数据库",
  "data": null
}
```

**示例请求**：
```bash
POST http://localhost:8000/api/vector/add/multiple
Content-Type: multipart/form-data
Authorization: Bearer your-jwt-token

# 表单数据
files: [选择多个文件]
```

**示例响应**：
```json
{
  "code": 200,
  "message": "文件 [\"example1.pdf\", \"example2.txt\"] 已成功上传并存储到向量数据库",
  "data": null
}
```

**限制**：
- 文件总大小不能超过200MB
- 仅支持PDF和TXT文件

## 4. 错误处理

### 401 Unauthorized
- 原因：认证失败，JWT token无效或过期
- 响应格式：
  ```json
  {
    "code": 401,
    "message": "Could not validate credentials",
    "data": null
  }
  ```

### 403 Forbidden
- 原因：权限不足，尝试访问其他用户的资源
- 响应格式：
  ```json
  {
    "code": 403,
    "message": "Forbidden",
    "data": null
  }
  ```

### 400 Bad Request
- 原因：请求参数错误，如文件类型不支持或文件大小超过限制
- 响应格式：
  ```json
  {
    "code": 400,
    "message": "文件大小不能超过20MB",
    "data": null
  }
  ```

### 500 Internal Server Error
- 原因：服务器内部错误
- 响应格式：
  ```json
  {
    "code": 500,
    "message": "服务器内部错误",
    "data": {
      "error_type": "ErrorType",
      "error_detail": "错误详情",
      "traceback": "堆栈跟踪信息",
      "path": "/api/endpoint"
    }
  }
  ```

## 5. 使用示例

### 5.1 认证示例
```bash
# 使用curl发送认证请求
curl -X POST "http://localhost:8000/api/agent/query/stream" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是LangChain?"}'
```

### 5.2 流式响应示例
```javascript
// 使用JavaScript接收流式响应
const eventSource = new EventSource("http://localhost:8000/api/agent/query/stream", {
  headers: {
    "Authorization": "Bearer your-jwt-token",
    "Content-Type": "application/json"
  },
  method: "POST",
  body: JSON.stringify({ query: "什么是LangChain?" })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "step":
      console.log("执行步骤:", data.content);
      break;
    case "response":
      console.log("响应内容:", data.content);
      break;
    case "done":
      console.log("会话ID:", data.session_id);
      eventSource.close();
      break;
    case "error":
      console.error("错误:", data.content);
      eventSource.close();
      break;
  }
};
```

### 5.3 文件上传示例
```bash
# 使用curl上传单个文件
curl -X POST "http://localhost:8000/api/vector/add/single" \
  -H "Authorization: Bearer your-jwt-token" \
  -F "file=@/path/to/file.pdf"

# 使用curl上传多个文件
curl -X POST "http://localhost:8000/api/vector/add/multiple" \
  -H "Authorization: Bearer your-jwt-token" \
  -F "files=@/path/to/file1.pdf" \
  -F "files=@/path/to/file2.txt"
```

## 6. 注意事项

1. **会话管理**：
   - 不提供session_id时，系统会自动生成一个UUID作为会话ID
   - 会话ID用于跟踪和存储对话历史

2. **文件上传**：
   - 单个文件大小限制为20MB
   - 多个文件总大小限制为200MB
   - 仅支持PDF和TXT格式的文件

3. **认证**：
   - 所有需要用户身份的接口都需要JWT认证
   - JWT token应从Django认证系统获取

4. **权限控制**：
   - 用户只能访问和管理自己的会话
   - 尝试访问其他用户的会话会返回403 Forbidden错误

5. **响应格式**：
   - 非流式接口返回JSON格式，包含code、message和data字段
   - 流式接口返回Server-Sent Events格式

6. **工具调用**：
   - 当使用天气工具时，需要提供城市名称作为参数
   - 其他工具也需要提供相应的必需参数
