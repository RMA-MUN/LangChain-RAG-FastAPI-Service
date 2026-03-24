import httpx
from typing import List, Dict, Any
from app.core.logger_handler import logger


class ReorderService:
    """文档重排序服务"""
    
    @staticmethod
    async def reorder_documents(query: str, documents: List[str]) -> Dict[str, Any]:
        """
        对文档进行重排序
        :param query: 查询语句
        :param documents: 文档列表
        :return: 包含重排序结果的字典，格式为：
                 {"success": bool, "documents": List[Dict], "error": str}
        """
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
                    logger.info(f"【重排序服务】文档重排序成功，返回 {len(sorted_docs)} 个文档")
                    return {
                        "success": True,
                        "documents": sorted_docs,
                        "error": ""
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    logger.warning(f"【重排序服务】重排序失败: {error_msg}")
                    return {
                        "success": False,
                        "documents": [],
                        "error": error_msg
                    }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"【重排序服务】重排序请求失败: {error_msg}")
            return {
                "success": False,
                "documents": [],
                "error": error_msg
            }

    @staticmethod
    def format_reorder_result(sorted_docs: List[Dict]) -> str:
        """
        格式化重排序结果
        :param sorted_docs: 重排序后的文档列表
        :return: 格式化后的字符串
        """
        formatted_result = "重排序后的文档列表：\n"
        for i, doc in enumerate(sorted_docs, 1):
            formatted_result += f"{i}. 相似度: {doc.get('similarity', 0):.4f}\n"
            formatted_result += f"   内容: {doc.get('document', '')}\n\n"
        return formatted_result


# 全局重排序服务实例
reorder_service = ReorderService()