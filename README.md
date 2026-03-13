# 🚀 微服务智能对话服务

## 项目简介

这是一个基于 FastAPI + LangChain 构建的智能对话系统，集成了 RAG 检索增强生成，能够基于文档内容进行智能问答 💬

## 技术栈

### 后端技术栈
- **FastAPI** ⚡: 高性能的 Python Web 框架
- **LangChain** 🦜: 大语言模型应用开发框架
- **ChromaDB** 📚: 轻量级向量数据库，用于存储和检索文档嵌入
- **Django** 🎯: 用于用户认证和管理
- **DashScope API** 🔑: 提供大语言模型和嵌入模型服务

### 前端技术栈
- **Vue 3** 🖼️: 前端框架
- **Vite** ⚡: 构建工具
- **Vue Router** 🛣️: 路由管理
- **Pinia** 📦: 状态管理
- **i18n** 🌍: 国际化支持

## 项目亮点

1. **RAG 技术** 📖: 结合文档检索和大语言模型，提供基于文档的智能问答
2. **会话持久化** 💾: 使用 MySQL 存储会话历史，支持长期保存
3. **多语言支持** 🌐: 前端集成 i18n，支持中英文切换
4. **模块化设计** 🧩: 清晰的代码结构，易于维护和扩展
5. **向量数据库** 📊: 使用 ChromaDB 实现高效的文档检索
6. **微服务架构** 🏗️: 分离的用户服务和对话服务

## 项目结构

```
├── backend/          # FastAPI 后端服务
│   ├── app/          # 应用代码
│   │   ├── agent/    # 智能代理
│   │   ├── config/   # 配置文件
│   │   ├── model/    # 数据模型
│   │   ├── prompt/   # 提示词模板
│   │   ├── rag/      # RAG 相关功能
│   │   ├── router/   # API 路由
│   │   ├── services/ # 服务层
│   │   └── utils/    # 工具函数
│   ├── data/         # 数据文件
│   ├── main.py       # 应用入口
│   └── requirements.txt
├── front/            # Vue 前端
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json
├── DjangoUserService/ # Django 用户服务
└── README.md         # 项目说明
```

## api文档

***<u>[智能对话API文档](.\backend\api.md)</u>***

**<u>*[用户服务API文档](.\DjangoUserService\api.md)*</u>**

## 快速开始 🚀

### 1. 环境准备

#### 后端环境
- Python 3.12
- pip

#### 前端环境
- Node.js 16+
- npm 或 pnpm

### 克隆项目

```bash
git clone https://github.com/RMA-MUN/LangChain-RAG-FastAPI-Service.git
cd LangChain-RAG-FastAPI-Service
```

### 2. 安装依赖

#### 后端依赖
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

#### 前端依赖
```bash
# 进入前端目录
cd front

# 安装依赖
npm install
# 或使用 pnpm
pnpm install
```

### 3. 配置

#### 3.1 环境变量配置

创建 `.env` 文件在 `backend` 目录下：

```env
# DashScope API Key (用于大语言模型和嵌入模型)
DASHSCOPE_API_KEY=your_dashscope_api_key

# 数据库配置 (如果使用 MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=chatbot

# 其他配置
SECRET_KEY=your_secret_key
```

#### 3.2 模型配置

修改 `backend/app/config/rag.yaml` 文件：

```yaml
# 聊天模型名称
chat_model_name: qwen3-max

# 文本嵌入模型名称
text_embedding_model_name: text-embedding-v4
```

#### 3.3 向量数据库配置

修改 `backend/app/config/chroma.yaml` 文件：

```yaml
# 向量数据库配置
collection_name: rag_collection
persist_directory: data/chromadb
k: 3

data_path: data
md5_hex_store: data/md5_hex_store/md5_hex_store.txt
allow_knowledge_file_types: ["txt", "pdf"]

# 文档切分配置
chunk_size: 200
chunk_overlap: 20
separators: ["\n\n", "\n", "。", "！", "？", "!", "?", " ", ""]
```

### 4. 运行项目

#### 4.1 启动后端服务

```bash
# 进入后端目录
cd backend

# 启动 FastAPI 服务
uvicorn main:app --reload
```

服务将在 `http://localhost:8000` 运行。

#### 4.2 启动前端服务

```bash
# 进入前端目录
cd front

# 启动开发服务器
npm run dev
# 或使用 pnpm
pnpm run dev
```

前端将在 `http://localhost:5173` 运行。

#### 4.3 启动用户服务 (可选)

```bash
# 进入 Django 用户服务目录
cd DjangoUserService

# 启动 Django 服务
python manage.py runserver
```

用户服务将在 `http://localhost:8000` 运行。

## 主要功能

### 1. 智能对话 💬
- 基于 RAG 技术，结合文档内容进行问答
- 支持多轮对话
- 会话历史持久化

### 2. 文档管理 📄
- 支持上传和管理文档
- 自动处理文档并生成向量嵌入
- 基于相似度检索相关文档

### 3. 用户系统 👤
- 用户注册和登录
- 个人资料管理
- 会话历史管理

### 4. 多语言支持 🌐
- 中英文界面切换
- 支持多语言对话

## API 文档

### FastAPI 后端 API

启动后端服务后，访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

### Django 用户服务 API

启动用户服务后，访问 `http://localhost:8000/api/` 查看用户服务 API 文档。

## 配置说明

### 1. 数据库配置

#### MySQL 配置

在 `backend/app/config/db_config.py` 中配置 MySQL 连接：

```python
# MySQL 配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "chatbot"),
}
```

### 2. API Key 配置

#### DashScope API Key

在 `.env` 文件中设置：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 模型配置

在 `backend/app/config/rag.yaml` 中配置模型参数：

```yaml
# 聊天模型名称
chat_model_name: qwen3-max

# 文本嵌入模型名称
text_embedding_model_name: text-embedding-v4
```

### 4. 向量数据库配置

在 `backend/app/config/chroma.yaml` 中配置向量数据库参数：

```yaml
# 向量数据库配置
collection_name: rag_collection
persist_directory: data/chromadb
k: 3

data_path: data
md5_hex_store: data/md5_hex_store/md5_hex_store.txt
allow_knowledge_file_types: ["txt", "pdf"]

# 文档切分配置
chunk_size: 200
chunk_overlap: 20
separators: ["\n\n", "\n", "。", "！", "？", "!", "?", " ", ""]
```

## 部署说明

### 生产环境部署

1. **后端部署**
   - 使用 Gunicorn 作为 WSGI 服务器
   - 配置 Nginx 作为反向代理

2. **前端部署**
   - 构建前端静态文件：`npm run build`
   - 将构建产物部署到 Nginx 或其他静态文件服务器

3. **数据库配置**
   - 生产环境建议使用 MySQL 或 PostgreSQL
   - 配置数据库连接字符串

## 开发指南

### 代码结构

- **backend/app/rag/**: RAG 相关功能，包括向量存储和检索
- **backend/app/agent/**: 智能代理，处理用户请求
- **backend/app/services/**: 服务层，提供会话管理等功能
- **backend/app/utils/**: 工具函数，包括配置加载、文件处理等
- **front/src/views/**: 前端页面
- **front/src/components/**: 前端组件

### 开发流程

1. **添加新功能**
   - 在对应的模块中添加代码
   - 运行测试确保功能正常
   - 更新文档

2. **调试技巧**
   - 使用 FastAPI 的自动重载功能：`uvicorn main:app --reload`
   - 使用 Vue 的热更新功能：`npm run dev`

## 故障排除

### 常见问题

1. **API Key 错误**
   - 检查 `.env` 文件中的 DASHSCOPE_API_KEY 是否正确
   - 确保 API Key 没有过期

2. **数据库连接失败**
   - 检查数据库配置是否正确
   - 确保数据库服务正在运行

3. **向量数据库问题**
   - 检查 `data/chromadb` 目录是否存在
   - 确保文件权限正确

4. **前端访问后端 API 失败**
   - 检查 CORS 配置
   - 确保后端服务正在运行

## 许可证

MIT License

## 联系方式

如果您有任何问题或建议，请随时联系我们。 😊