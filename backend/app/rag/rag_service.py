import asyncio

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
        self.hyde_prompt_template = PromptTemplate.from_template("基于以下问题，生成一个详细的假设性回答，我会根据你的这个假设性回答在向量数据库里检索文档：\n\n问题：{query}\n\n假设性回答：")

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

    async def generate_hypothetical_document(self, query: str) -> str:
        """
        使用HyDE技术生成假设性文档
        :param query: 用户查询
        :return: 假设性文档内容
        """
        try:
            hyde_chain = (
                self.hyde_prompt_template
                | self.chat_model
                | StrOutputParser()
            )
            hypothetical_doc = await hyde_chain.ainvoke({"query": query})
            logger.info(f"【HyDE】生成的假设性文档:\n{hypothetical_doc}")
            return hypothetical_doc
        except Exception as e:
            logger.error(f"【HyDE】生成假设性文档失败: {e}")
            return query

    async def retrieve_document(self, query: str) -> list:
        """使用HyDE技术 从向量数据库里检索文档"""
        try:
            # 确保检索器已初始化
            if self.retriever is None:
                await self.initialize_retriever()
            
            # 使用HyDE技术生成假设性文档
            logger.info(f"【HyDE】开始处理查询: {query}")
            hypothetical_doc = await self.generate_hypothetical_document(query)
            
            # 使用假设性文档进行检索
            logger.info(f"【HyDE】使用假设性文档进行检索")
            documents = await self.retriever.ainvoke(hypothetical_doc)
            logger.info(f"【HyDE】检索到 {len(documents)} 个相关文档")
            
            return documents
        except Exception as e:
            logger.error(f"【HyDE】检索文档失败: {e}")
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

            # 如果没有检索到文档
            if not reordered_documents:
                return {
                    "documents": [],
                    "summary": "抱歉，我没有找到相关的信息。"
                }

            # 使用分批总结策略
            try:
                # 对每个文档单独总结
                individual_summaries = []
                max_documents = 3  # 使用前3个最相关的文档
                
                for i, doc in enumerate(reordered_documents[:max_documents], 1):
                    logger.info(f"【RAG】正在总结第{i}个文档")
                    # 为单个文档构建上下文
                    single_context = f"【参考资料{i}】:{doc}\n"
                    # 生成单个文档的摘要
                    import time
                    start_time = time.time()
                    single_summary = await asyncio.wait_for(
                        self.chain.ainvoke({"input": query, "context": single_context}),
                        timeout=30.0  # 单个文档总结超时时间
                    )
                    end_time = time.time()
                    logger.info(f"【RAG】第{i}个文档总结耗时: {end_time - start_time:.2f}秒")
                    individual_summaries.append(single_summary)
                    logger.info(f"【RAG】第{i}个文档总结完成")

                # 如果只有一个文档，直接返回其摘要
                if len(individual_summaries) == 1:
                    logger.info(f"【RAG】生成摘要成功")
                    return {
                        "documents": reordered_documents,
                        "summary": individual_summaries[0]
                    }

                # 合并多个文档的摘要，生成最终总结
                combined_context = "以下是多个文档的摘要，请综合这些信息生成最终的回答：\n\n"
                for i, summary in enumerate(individual_summaries, 1):
                    combined_context += f"【文档{i}摘要】:{summary}\n\n"

                logger.info(f"【RAG】合并摘要完成，开始生成最终总结")
                
                # 生成最终总结
                final_summary = await asyncio.wait_for(
                    self.chain.ainvoke({"input": query, "context": combined_context}),
                    timeout=30.0  # 最终总结超时时间
                )
                
                logger.info(f"【RAG】生成摘要成功")
                return {
                    "documents": reordered_documents,
                    "summary": final_summary
                }
            except asyncio.TimeoutError:
                logger.error(f"【RAG】生成摘要超时")
                return {
                    "documents": reordered_documents,
                    "summary": "抱歉，生成摘要超时，请稍后再试。"
                }
        except Exception as e:
            logger.error(f"【RAG】生成摘要失败: {e}", exc_info=True)
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