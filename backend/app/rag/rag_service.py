from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.rag.vector_store import VectorStoreService
from app.utils.factory import chat_model
from app.utils.prompt_loader import load_prompt
from app.utils.logger_handler import logger


class RagService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_prompt(prompt_type="rag_summary_prompt")
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.chat_model = chat_model
        self.chain = self._init_chain()


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
            # 使用异步方式调用retriever
            documents = await self.retriever.ainvoke(query)
            logger.info(f"【RAG】检索到 {len(documents)} 个相关文档")
            return documents
        except Exception as e:
            logger.error(f"【RAG】检索文档失败: {e}")
            return []

    async def rag_summary(self, query: str) -> str:
        """RAG 摘要"""
        try:
            documents = await self.retrieve_document(query)
            
            # 构建上下文
            context = ""
            for i, doc in enumerate(documents, 1):
                context += f"【参考资料{i}】:{doc.page_content}\n"
            
            # 如果没有检索到文档
            if not context:
                return "抱歉，我没有找到相关的信息。"
            
            # 生成摘要
            response = await self.chain.ainvoke({"input": query, "context": context})
            logger.info(f"【RAG】生成摘要成功")
            return response
        except Exception as e:
            logger.error(f"【RAG】生成摘要失败: {e}")
            return "抱歉，处理您的请求时出现了错误。"

if __name__ == '__main__':
    service = RagService()
    print(service.rag_summary("小户型适合什么扫地机器人"))
