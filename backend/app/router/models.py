from pydantic import BaseModel
from typing import List, Optional, Tuple


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    session_id: str


class RAGRequest(BaseModel):
    """RAG检索请求模型"""
    query: str


class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str
    history: List[Tuple[str, str]]


class AgentResponse(BaseModel):
    """Agent响应模型"""
    response: str
    session_id: str


class RAGResponse(BaseModel):
    """RAG检索响应模型"""
    response: str
