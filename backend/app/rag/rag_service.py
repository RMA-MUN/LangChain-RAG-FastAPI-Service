from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.rag.vector_store import VectorStoreService
from app.rag.reorder_service import reorder_service
from app.utils.factory import chat_model
from app.utils.prompt_loader import load_prompt
from app.core.logger_handler import logger


class RagService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = None  # 延迟初始化
        self.prompt_text = load_prompt(prompt_type="rag_summary_prompt")
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.chat_model = chat_model
        self.chain = self._init_chain()

    async def initialize_retriever(self):
        """
        初始化检索器
        """
        if self.retriever is None:
            self.retriever = await self.vector_store.get_retriever()


    def _init_chain(self):
        """初始化链"""
        chain = (
                self.prompt_template
                | self.chat_model
                | StrOutputParser()
        )
        return chain

    async def retrieve_document(self, query: str) -> list:
        """从向量数据库里检索文档"""
        try:
            # 确保检索器已初始化
            if self.retriever is None:
                await self.initialize_retriever()
            # 使用异步方式调用retriever
            documents = await self.retriever.ainvoke(query)
            logger.info(f"【RAG】检索到 {len(documents)} 个相关文档")
            return documents
        except Exception as e:
            logger.error(f"【RAG】检索文档失败: {e}")
            return []

    async def reorder_documents(self, query: str, documents: list) -> list:
        """
        对文档进行重排序
        :param query: 查询语句
        :param documents: 文档列表
        :return: 重排序后的文档列表
        """
        result = await reorder_service.reorder_documents(query, documents)
        if result["success"]:
            # 提取重排序后的文档内容
            reordered_documents = [doc.get("document", "") for doc in result["documents"]]
            logger.info(f"【RAG】文档重排序成功，返回 {len(reordered_documents)} 个文档")
            return reordered_documents
        else:
            logger.warning(f"【RAG】重排序失败: {result['error']}")
            return documents

    async def get_documents_and_summary(self, query: str) -> dict:
        """
        获取文档列表和摘要
        :param query: 查询语句
        :return: 包含文档列表和摘要的字典
        """
        try:
            documents = await self.retrieve_document(query)
            
            # 提取文档内容列表
            document_contents = [doc.page_content for doc in documents]
            
            # 对文档进行重排序
            reordered_documents = await self.reorder_documents(query, document_contents)
            
            # 构建上下文（使用重排序后的文档）
            context = ""
            for i, doc in enumerate(reordered_documents, 1):
                context += f"【参考资料{i}】:{doc}\n"
            
            # 如果没有检索到文档
            if not context:
                return {
                    "documents": [],
                    "summary": "抱歉，我没有找到相关的信息。"
                }
            
            # 生成摘要
            response = await self.chain.ainvoke({"input": query, "context": context})
            logger.info(f"【RAG】生成摘要成功")
            return {
                "documents": reordered_documents,
                "summary": response
            }
        except Exception as e:
            logger.error(f"【RAG】生成摘要失败: {e}")
            return {
                "documents": [],
                "summary": "抱歉，处理您的请求时出现了错误。"
            }

    async def rag_summary(self, query: str) -> str:
        """RAG 摘要"""
        result = await self.get_documents_and_summary(query)
        return result.get("summary", "抱歉，处理您的请求时出现了错误。")

if __name__ == '__main__':
    import asyncio
    
    async def main():
        service = RagService()
        await service.initialize_retriever()
        result = await service.rag_summary("小户型适合什么扫地机器人")
        print(result)
    
    asyncio.run(main())