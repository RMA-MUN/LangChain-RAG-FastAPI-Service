from langchain_core.tools import tool

from app.rag.rag_service import RagService

import datetime

@tool(description="用于从向量数据库里检索文档并生成摘要")
async def rag_summary_tools(query: str) -> str:
    """RAG 摘要工具"""
    return await RagService().rag_summary(query)


@tool(description="用于获取天气信息")
def get_weather_tools(city: str) -> str:
    """获取天气工具"""
    return f"【{city}】的天气是晴朗的"


@tool(description="用于获取当前年月日时分的工具")
def what_time_is_now() -> str:
    """获取当前年月日时分的工具"""
    return f"当前时间是：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}"


