from typing import List, Optional, Tuple, Dict, Any
import uuid
import magic

from fastapi import HTTPException, UploadFile
from langchain_chroma.vectorstores import cosine_similarity
from langchain_ollama import OllamaEmbeddings
import numpy as np

from app.core.logger_handler import logger
from app.rag.vector_store import VectorStoreService
from app.rag.rag_service import RagService
from app.agent.agent import get_agent_response
from app.services import session_manager as sm
from app.utils.config import rag_config


class ChatService:
    """路由服务层，处理业务逻辑"""

    async def handle_agent_query(self, query: str, session_id: Optional[str], user_id: str) -> Tuple[str, dict, str]:
        """处理智能代理查询逻辑"""
        # 如果未提供 session_id，则生成一个
        session_id = session_id or str(uuid.uuid4())

        # 获取会话历史
        history = await sm.session_manager.get_history(session_id, user_id)

        # 获取智能代理响应
        result = await get_agent_response(query, history)
        response = result.get("response")
        steps = result.get("steps", [])

        # 添加到会话历史
        await sm.session_manager.add_message(session_id, user_id, query, response)

        return session_id, response, steps

    async def handle_rag_query(self, query: str) -> str:
        """处理 RAG 查询逻辑"""
        rag_service = RagService()
        response = await rag_service.rag_summary(query)
        return response

    async def handle_get_session(self, session_id: str, user_id: str) -> List[Tuple[str, str]]:
        """处理获取会话逻辑"""
        # 获取会话历史，会自动验证会话属于该用户
        history = await sm.session_manager.get_history(session_id, user_id)
        return history

    async def handle_delete_session(self, session_id: str, user_id: str) -> None:
        """处理删除会话逻辑"""
        await sm.session_manager.clear_session(session_id, user_id)

    async def handle_get_all_sessions(self) -> List[str]:
        """处理获取所有会话逻辑"""
        session_ids = await sm.session_manager.get_all_session_ids()
        return session_ids

    async def handle_get_user_sessions(self, user_id: str, current_user_id: str) -> List[Dict]:
        """处理获取用户会话逻辑"""
        # 确保用户只能获取自己的会话
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        sessions = await sm.session_manager.get_user_sessions(user_id)
        return sessions

    async def handle_add_vector_single(self, file: UploadFile, user_id: str) -> str:
        """处理添加单个向量逻辑"""
        # 创建向量数据库服务实例
        store = VectorStoreService()

        # 检查文件大小，如果超过20MB则抛出异常
        max_file_size = 20 * 1024 * 1024  # 20MB
        if file.size > max_file_size:
            raise HTTPException(status_code=400, detail="文件大小不能超过20MB")

        # 使用python-magic检查文件类型
        content = await file.read()
        # 重置文件指针
        await file.seek(0)
        
        # 检测文件类型
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        
        # 检查文件类型是否允许
        allowed_mime_types = {'application/pdf', 'text/plain'}
        if file_type not in allowed_mime_types:
            raise HTTPException(status_code=400, detail=f"文件类型不支持，仅支持PDF和TXT文件。检测到的文件类型: {file_type}")

        # 处理文件并存储到向量数据库
        await store.get_document(files=[file], user_id=user_id)

        return file.filename

    async def handle_add_vector_multiple(self, files: List[UploadFile], user_id: str) -> List[str]:
        """处理添加多个向量逻辑"""
        store = VectorStoreService()
        max_file_folder_size = 200 * 1024 * 1024  # 最大文件大小200MB

        # 检查文件类型和大小
        total_size = 0
        allowed_mime_types = {'application/pdf', 'text/plain'}
        mime = magic.Magic(mime=True)
        
        for file in files:
            content = await file.read()
            total_size += len(content)
            
            # 检测文件类型
            file_type = mime.from_buffer(content)
            if file_type not in allowed_mime_types:
                raise HTTPException(status_code=400, detail=f"文件 {file.filename} 类型不支持，仅支持PDF和TXT文件。检测到的文件类型: {file_type}")
            
            # 重置文件指针以便后续处理
            await file.seek(0)

        if total_size > max_file_folder_size:
            raise HTTPException(status_code=400, detail="文件总大小不能超过200MB")

        await store.get_document(files=files, user_id=user_id)

        return [file.filename for file in files]

    async def clean_user_upload(self, user_id: str) -> None:
        """处理删除用户上传的所有向量逻辑"""
        # 创建向量数据库服务实例
        store = VectorStoreService()
        # 删除用户的所有文档
        await store.delete_user_documents(user_id)

    async def handle_reorder(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """
        使用Ollama嵌入模型对文档进行中文重排序
        :param query: 查询语句
        :param documents: 文档列表
        :return: 排序后的文档列表，包含文档内容和相似度
        """
        try:
            # 检查文档列表是否为空
            if not documents:
                return []
            
            # 初始化Ollama嵌入模型，使用配置文件中定义的模型
            embeddings = OllamaEmbeddings(
                model=rag_config['text_embedding_model_name'],
                base_url="http://localhost:11434"
            )
            
            # 获取查询的嵌入向量
            query_embedding = await embeddings.aembed_query(query)
            
            # 获取所有文档的嵌入向量
            doc_embeddings = await embeddings.aembed_documents(documents)
            
            # 检查嵌入向量是否为空
            if not doc_embeddings:
                return []
            
            # 计算查询与每个文档的余弦相似度
            similarities = cosine_similarity(
                [query_embedding],
                doc_embeddings
            )[0]
            
            # 按相似度排序
            sorted_indices = np.argsort(similarities)[::-1]
            
            # 构建排序后的结果
            sorted_docs = []
            for idx in sorted_indices:
                sorted_docs.append({
                    "document": documents[idx],
                    "similarity": float(similarities[idx])
                })

            # log记录排序结果
            logger.info(f"重排序结果: {sorted_docs}")
            return sorted_docs
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"重排序过程中出错: {str(e)}")


def get_router_service() -> ChatService:
    """获取路由服务实例（用于依赖注入）"""
    return ChatService()