from typing import List
import uuid

from fastapi.routing import APIRouter
from fastapi import UploadFile, File, Depends
from fastapi.responses import StreamingResponse

from app.agent.agent import get_agent_stream_response
from app.router.chat_service import ChatService, get_router_service

from app.schemas.models import QueryRequest, RAGResponse, RAGRequest, SessionResponse
from app.utils.auth_utils import get_current_user_id
from app.core.success_response import success_response


chat_router = APIRouter(prefix="/api", tags=["api"])

@chat_router.post("/agent/query/stream")
async def query_stream(request: QueryRequest, user_id: str = Depends(get_current_user_id)):
    """查询Agent流式响应"""
    # 如果没有提供session_id，自动生成一个
    session_id = request.session_id or str(uuid.uuid4())
    
    # 直接调用get_agent_stream_response函数
    return StreamingResponse(
        get_agent_stream_response(request.query, session_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@chat_router.post("/rag/query", response_model=RAGResponse)
async def query_rag(request: RAGRequest, router_service: ChatService = Depends(get_router_service)):
    """RAG检索"""
    response = await router_service.handle_rag_query(request.query)
    return success_response(data=RAGResponse(response=response))


@chat_router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """获取会话信息，使用user_id验证"""
    history = await router_service.handle_get_session(session_id, user_id)
    return success_response(data=SessionResponse(session_id=session_id, history=history))



@chat_router.delete("/session/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """删除会话"""
    await router_service.handle_delete_session(session_id, user_id)
    return success_response(message=f"Session {session_id} deleted successfully")

@chat_router.get("/sessions")
async def get_all_sessions(router_service: ChatService = Depends(get_router_service)):
    """获取所有会话ID"""
    session_ids = await router_service.handle_get_all_sessions()
    return success_response(data={"sessions": session_ids})



@chat_router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, current_user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """获取用户所有会话ID"""
    session_ids = await router_service.handle_get_user_sessions(user_id, current_user_id)
    return success_response(data={"sessions": session_ids})


@chat_router.post("/vector/add/single")
async def add_vector_single(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """上传文件，将文件保存到向量数据库，仅支持TXT和PDF"""
    filename = await router_service.handle_add_vector_single(file, user_id)
    return success_response(message=f"文件 {filename} 已成功上传并存储到向量数据库")



@chat_router.post("/vector/add/multiple")
async def add_vector_multiple(files: List[UploadFile] = File(..., description="要上传的文件列表，仅支持PDF和TXT格式"), user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """上传多个文件，将文件保存到向量数据库，仅支持TXT和PDF"""
    filenames = await router_service.handle_add_vector_multiple(files, user_id)
    return success_response(message=f"文件 {filenames} 已成功上传并存储到向量数据库")


@chat_router.delete("/vector/clean")
async def clean_user_vectors(user_id: str = Depends(get_current_user_id), router_service: ChatService = Depends(get_router_service)):
    """删除用户上传的所有向量"""
    await router_service.clean_user_upload(user_id)
    return success_response(message="已成功删除用户上传的所有向量")