from typing import List, Dict, Any
import torch
import os
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from app.core.logger_handler import logger

# 加载环境变量
load_dotenv()


def check_and_download_reranker_model() -> None:
    """检查并重排序模型，在FastAPI启动时执行"""
    LOCAL_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", r"D:\Hugging_Face\models\Qwen3-Reranker-0.6B")
    HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
    
    try:
        # 检查本地模型是否存在
        if os.path.exists(LOCAL_MODEL_PATH) and os.path.isdir(LOCAL_MODEL_PATH):
            logger.info(f"✅ 检测到本地重排序模型：{LOCAL_MODEL_PATH}")
        else:
            logger.warning(f"⚠️  本地模型未找到：{LOCAL_MODEL_PATH}")
            logger.info(f"🔄 开始自动下载模型：{HF_MODEL_NAME}")
            
            # 创建模型目录
            os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
            
            # 自动下载模型
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = CrossEncoder(
                HF_MODEL_NAME,
                max_length=512,
                device=device,
                cache_folder=LOCAL_MODEL_PATH
            )
            logger.info(f"✅ 模型下载完成，使用设备：{device}")
            
    except Exception as e:
        logger.error(f"❌ 模型检查失败: {str(e)}")
        raise RuntimeError(f"重排序模型检查失败: {str(e)}")


class ReorderService:
    """文档重排序服务"""
    
    def __init__(self):
        # 从环境变量读取重排序模型路径
        self.LOCAL_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", r"D:\Hugging_Face\models\Qwen3-Reranker-0.6B")
        # Hugging Face模型名称
        self.HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
        # 自动选择设备（优先使用GPU）
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 模型实例（懒加载）
        self._model = None
    
    async def _get_model(self):
        """懒加载模型实例"""
        if self._model is None:
            logger.info(f"✅ 加载重排序模型：{self.LOCAL_MODEL_PATH}")
            self._model = CrossEncoder(
                self.LOCAL_MODEL_PATH,
                max_length=512,
                device=self.device,
                local_files_only=True
            )
            logger.info(f"✅ 模型加载成功，使用设备：{self.device}")
        return self._model
    
    @property
    async def model(self):
        """获取模型实例（懒加载）"""
        return await self._get_model()
    
    async def reorder_documents(self, query: str, documents: List[str]) -> Dict[str, Any]:
        """
        对文档进行重排序
        :param query: 查询语句
        :param documents: 文档列表
        :return: 包含重排序结果的字典，格式为：
                 {"success": bool, "documents": List[Dict], "error": str}
        """
        try:
            if not documents:
                return {
                    "success": True,
                    "documents": [],
                    "error": ""
                }
            
            # 构造查询+文档对
            pairs = [(query, doc) for doc in documents]
            
            # 使用模型进行批量预测（batch_size=1避免padding令牌报错）
            model = await self.model
            scores = model.predict(pairs, batch_size=1)
            
            # 构建结果列表
            scored_documents = []
            for doc, score in zip(documents, scores):
                scored_documents.append({
                    "document": doc,
                    "similarity": float(score)
                })
                logger.info(f"【重排序服务】文档相似度分数: {score:.4f}")
            
            # 按相似度分数降序排序
            sorted_docs = sorted(scored_documents, key=lambda x: x["similarity"], reverse=True)
            logger.info(f"【重排序服务】文档重排序成功，返回 {len(sorted_docs)} 个文档")
            
            return {
                "success": True,
                "documents": sorted_docs,
                "error": ""
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"【重排序服务】重排序失败: {error_msg}")
            return {
                "success": False,
                "documents": [],
                "error": error_msg
            }

    @staticmethod
    async def format_reorder_result(sorted_docs: List[Dict]) -> str:
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