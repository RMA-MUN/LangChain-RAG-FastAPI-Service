from fastapi.routing import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from app.router.models import QueryRequest, RAGRequest, SessionResponse, AgentResponse, RAGResponse
from app.rag.rag_service import RagService
from app.agent.agent import get_agent_response
from app.services import session_manager as sm

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/agent/query", response_model=AgentResponse)
async def query_agent(request: QueryRequest):
    """查询Agent"""
    try:
        # 获取会话历史
        history = await sm.session_manager.get_history(request.session_id)
        
        # 获取Agent响应
        response = await get_agent_response(request.query, history)
        
        # 添加到会话历史
        await sm.session_manager.add_message(request.session_id, request.query, response)
        
        return AgentResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/query/stream")
async def query_stream(request: QueryRequest):
    """查询Agent流式响应"""
    async def stream_response():
        try:
            # 获取会话历史
            history = await sm.session_manager.get_history(request.session_id)
            
            # 获取Agent响应
            response = await get_agent_response(request.query, history)
            
            # 添加到会话历史
            await sm.session_manager.add_message(request.session_id, request.query, response)
            
            # 模拟流式输出，将响应分割成多个块
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i+chunk_size]
                # 发送SSE格式的数据
                yield f"data: {chunk}\n\n"
                # 模拟网络延迟
                await asyncio.sleep(0.1)
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            # 发送错误信息
            yield f"data: 错误: {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    
    # 返回流式响应
    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/rag/query", response_model=RAGResponse)
async def query_rag(request: RAGRequest):
    """RAG检索"""
    try:
        rag_service = RagService()
        response = await rag_service.rag_summary(request.query)
        return RAGResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """获取会话信息"""
    try:
        history = await sm.session_manager.get_history(session_id)
        return SessionResponse(session_id=session_id, history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        await sm.session_manager.clear_session(session_id)
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_all_sessions():
    """获取所有会话ID"""
    try:
        session_ids = await sm.session_manager.get_all_session_ids()
        return {"sessions": session_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))