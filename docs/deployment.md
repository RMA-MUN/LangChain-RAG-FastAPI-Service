# 部署指南

## 生产环境部署

### 后端部署

#### 1. 安装依赖
```bash
cd backend
uv sync
```

#### 2. 配置环境变量
创建 `.env` 文件：
```env
# DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_api_key

# 数据库配置
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=chatbot

# 安全配置
SECRET_KEY=your_secret_key

# 重排序模型配置（可选）
RERANKER_MODEL_PATH=D:\Hugging_Face\models\Qwen3-Reranker-0.6B
```

#### 3. 使用 Gunicorn 部署
```bash
# 安装 Gunicorn
uv add gunicorn

# 启动服务（4个工作进程）
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

#### 4. 配置 Nginx 反向代理

创建 Nginx 配置文件 `/etc/nginx/sites-available/fastapi-app`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/fastapi-app /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 前端部署

#### 1. 构建前端
```bash
cd front
npm run build
# 或使用 pnpm
pnpm run build
```

#### 2. 部署静态文件

将 `dist` 目录部署到 Nginx 或其他静态文件服务器：
```nginx
server {
    listen 80;
    server_name frontend.your-domain.com;

    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 数据库配置

#### MySQL 配置
- 生产环境建议使用 MySQL 8.0+
- 配置数据库连接字符串和访问权限
- 确保数据库用户有足够的权限

#### Redis 配置
- 用于缓存和限流控制
- 建议配置密码认证
- 设置合理的内存策略

### Docker 部署（可选）

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=chatbot
    depends_on:
      - db
      - redis

  frontend:
    build: ./front
    ports:
      - "5173:5173"
    depends_on:
      - backend

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=chatbot
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

volumes:
  mysql_data:
```

启动服务：
```bash
docker-compose up -d
```

### 监控和日志

#### 日志配置
- 应用日志位于 `backend/logs/` 目录
- 配置日志轮转避免磁盘空间耗尽

#### 监控建议
- 使用 Prometheus + Grafana 监控系统指标
- 设置告警机制监控服务健康状态

### 安全建议

1. **HTTPS**：使用 Let's Encrypt 配置 SSL 证书
2. **防火墙**：配置防火墙规则限制访问
3. **定期更新**：定期更新依赖包和系统组件
4. **备份策略**：定期备份数据库和重要配置文件