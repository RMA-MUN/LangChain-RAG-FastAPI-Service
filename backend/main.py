import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.db.db_config import init_db
from app.db.redis_config import connect_redis, close_redis
from app.router.chat import chat_router
from app.router.health import health_router
from app.router.user import user_router

from app.services.database_session_manager import init_database_session_manager

from app.core.failed_response_register import register_exception_handlers

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response

# 集成API路由
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(user_router)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许访问的源
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"], # 允许的请求方法
    allow_headers=["*"], # 允许的请求头
)

# 注册异常处理函数
register_exception_handlers(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化会话管理器"""
    # 初始化数据库表结构
    await init_db()
    print("数据库表结构初始化完成")
    
    # 使用数据库版本的会话管理器
    await init_database_session_manager()
    print("数据库会话管理器初始化完成")

    # 连接Redis
    await connect_redis()
    print("Redis连接初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时关闭Redis连接"""
    await close_redis()
    print("Redis连接已关闭")
