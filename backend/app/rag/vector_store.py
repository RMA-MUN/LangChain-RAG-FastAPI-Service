import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.utils.file_handler import txt_loader, pdf_loader, listdir_allowed_type, get_file_md5_hex
from app.utils.logger_handler import logger
from app.utils.path_tool import get_abstract_path


class VectorStoreService:
    """向量数据库服务"""
    def __init__(self):
        # 使用绝对路径存储向量数据库，确保无论从哪个目录运行都能正确访问
        persist_dir = get_abstract_path(chroma_config['persist_directory'])
        self.vectors_store = Chroma(
            collection_name=chroma_config['collection_name'],
            embedding_function=embed_model,
            persist_directory=persist_dir,
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_config['chunk_size'],
            chunk_overlap=chroma_config['chunk_overlap'],
            separators=chroma_config['separators'],
        )

    def get_retriever(self):
        """获取检索器"""
        return self.vectors_store.as_retriever(
            search_type='similarity',
            search_kwargs={'k': chroma_config['k']},
        )

    def get_document(self):
        """
        从数据文件夹内读取文档，转为向量并存入向量数据库
        要计算文件的md5并去重
        :return:
        """
        def check_md5_hex(md5_for_check: str) -> bool:
            """检查md5是否已存在"""
            if not os.path.exists(get_abstract_path(chroma_config['md5_hex_store'])):
                # 如果文件不存在，创建文件，文件未被写入过md5
                open(get_abstract_path(chroma_config['md5_hex_store']), 'w', encoding="utf-8").close()
                return False

            with open(get_abstract_path(chroma_config['md5_hex_store']), 'r', encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True

                return False

        def save_md5_hex(md5_hex: str):
            """保存md5"""
            with open(get_abstract_path(chroma_config['md5_hex_store']), 'a', encoding="utf-8") as f:
                f.write(md5_hex + '\n')

        def get_file_document(read_path: str) -> list[Document]:
            if read_path.endswith('.txt'):
                return txt_loader(read_path)
            elif read_path.endswith('.pdf'):
                return pdf_loader(read_path)
            else:
                return []

        allowed_file_path: tuple[str] = listdir_allowed_type(
            chroma_config['data_path'],
            tuple(chroma_config['allow_knowledge_file_types'])
        )

        for file_path in allowed_file_path:
            # 计算文件的md5值
            md5_hex = get_file_md5_hex(file_path)
            if check_md5_hex(md5_hex):
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已存在，跳过")
                continue

            try:
                # 加载文件内容
                document: list[Document] = get_file_document(file_path)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 加载内容为空，跳过")
                    continue
                # 切分文档
                document: list[Document] = self.spliter.split_documents(document)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 切分内容为空，跳过")
                    continue
                # 向量化文档
                self.vectors_store.add_documents(document)
                # 保存md5值
                save_md5_hex(md5_hex)
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已保存")

            except Exception as e:
                logger.error(f"【向量数据库】文件 {file_path} 处理时出错: {e}")
                continue


if __name__ == '__main__':
    # 测试向量数据库服务
    store = VectorStoreService()
    store.get_document()

    retriever = store.get_retriever()
    results = retriever.invoke('扫地')
    print(f"检索结果数量: {len(results)}")
    for result in results:
        print(result)