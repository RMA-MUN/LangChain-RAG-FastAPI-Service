from typing import List

import httpx
from langchain_core.tools import tool

from app.core.logger_handler import logger
from app.rag.rag_service import RagService
from app.utils.auth_utils import decode_django_jwt

import datetime

@tool(description="用于从向量数据库里检索文档并生成摘要，返回包含文档列表和摘要的结果。在获取到结果后，你需要调用`reorder_documents_tools`工具对文档进行重排序")
async def rag_summary_tools(query: str) -> str:
    """RAG 摘要工具"""
    result = await RagService().get_documents_and_summary(query)
    documents = result.get("documents", [])
    summary = result.get("summary", "")
    
    # 格式化返回结果
    formatted_result = f"摘要: {summary}\n\n"
    formatted_result += "检索到的文档列表:\n"
    for i, doc in enumerate(documents, 1):
        formatted_result += f"{i}. {doc[:200]}...\n"  # 只显示前200个字符
    
    return formatted_result

@tool(description="传入查询语句query和检索到的文档列表documents，返回重排序后的文档列表，包含文档内容和相似度")
async def reorder_documents_tools(query: str, documents: List[str]) -> str:
    """重排序文档工具"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/reorder",
                json={
                    "query": query,
                    "documents": documents
                },
                timeout=30.0
            )
            response.raise_for_status()  # 检查响应状态
            result = response.json()
            
            if result.get("code") == 200:
                sorted_docs = result.get("data", {}).get("documents", [])
                # 格式化返回结果
                formatted_result = "重排序后的文档列表：\n"
                for i, doc in enumerate(sorted_docs, 1):
                    formatted_result += f"{i}. 相似度: {doc.get('similarity', 0):.4f}\n"
                    formatted_result += f"   内容: {doc.get('document', '')}\n\n"
                # 记录日志
                logger.info(formatted_result)
                return formatted_result
            else:
                return f"重排序失败: {result.get('message', '未知错误')}"
    except Exception as e:
        return f"重排序请求失败: {str(e)}"

@tool(description="从JWT中获取当前用户信息，参数为完整的JWT token字符串")
async def get_user_info_tools(token: str) -> str:
    """获取用户信息工具"""
    payload = decode_django_jwt(token)
    if payload:
        user_id = payload.get("user_id", "未知")
        user_name = payload.get("user_name", "未知")
        return f"用户信息：\n- 用户ID: {user_id}\n- 用户名: {user_name}"
    else:
        return "无法解析JWT token，无法获取用户信息"


@tool(description="用于获取天气信息，需要提供城市名称作为参数，你需要从用户输入中提取城市名称，是str类型")
async def get_weather_tools(city: str = None) -> str:
    """获取天气工具"""
    if not city:
        return "请提供城市名称"
    return f"【{city}】的天气是晴朗的"


@tool(description="用于获取当前年月日时分的工具")
async def what_time_is_now() -> str:
    """获取当前年月日时分的工具"""
    return f"当前时间是：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}"