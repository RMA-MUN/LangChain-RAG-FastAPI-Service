import asyncio
import sys
import os
import tempfile

# 将根目录添加到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import aiofiles
from aiofiles import os as aio_os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.utils.file_handler import pdf_loader, txt_loader, listdir_allowed_type, get_file_md5_hex
from app.utils.logger_handler import logger
from app.utils.path_tool import get_abstract_path

class VectorStoreService:
    """向量数据库服务"""
    def __init__(self):
        persist_dir = get_abstract_path(chroma_config['persist_directory'])
        # 使用同步 Chroma, 在调用时用 to_thread 包裹
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

    async def check_md5_hex(self, md5_for_check: str) -> bool:
        """异步检查md5"""
        md5_path = get_abstract_path(chroma_config['md5_hex_store'])
        # 确保目录存在
        md5_dir = os.path.dirname(md5_path)
        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir, exist_ok=True)
        if not await aio_os.path.exists(md5_path):
            async with aiofiles.open(md5_path, 'w', encoding="utf-8"):
                pass
            return False

        async with aiofiles.open(md5_path, 'r', encoding="utf-8") as f:
            async for line in f:
                if line.strip() == md5_for_check:
                    return True
            return False

    async def save_md5_hex(self, md5_hex: str):
        """异步保存md5"""
        async with aiofiles.open(get_abstract_path(chroma_config['md5_hex_store']), 'a', encoding="utf-8") as f:
            await f.write(md5_hex + '\n')

    async def get_file_document(self, read_path: str) -> list[Document]:
        """异步加载文件"""
        if read_path.endswith('.txt'):
            return await txt_loader(read_path)
        elif read_path.endswith('.pdf'):
            return await pdf_loader(read_path)
        else:
            return []

    async def get_document(self, files: list = None):
        """
        处理文档并将其转为向量存入向量数据库
        :param files: 上传的文件列表，如果为None则从数据文件夹读取
        """
        # 确定要处理的文件列表
        file_paths = []
        if files:
            # 处理上传的文件
            for file in files:
                # 创建临时文件，使用asyncio.to_thread 包裹
                temp_file_path = await asyncio.to_thread(
                    tempfile.NamedTemporaryFile,
                    delete=False,
                    suffix=os.path.splitext(file.filename)[1]
                )
                content = await file.read()
                await asyncio.to_thread(temp_file_path.write, content)
                file_paths.append(temp_file_path.name)
        else:
            # 从数据文件夹读取文件
            allowed_file_path: tuple[str] = await listdir_allowed_type(
                chroma_config['data_path'],
                tuple(chroma_config['allow_knowledge_file_types'])
            )
            file_paths = list(allowed_file_path)

        for file_path in file_paths:
            # 2. 计算MD5
            md5_hex = await get_file_md5_hex(file_path)
            if await self.check_md5_hex(md5_hex):
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已存在，跳过")
                # 如果是临时文件，删除
                if files:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                continue

            try:
                # 3. 加载文档
                document: list[Document] = await self.get_file_document(file_path)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 加载内容为空，跳过")
                    # 如果是临时文件，删除
                    if files:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            pass
                    continue

                # 4. 切分文档 (同步执行，因为是CPU密集操作，没必要异步)
                document: list[Document] = self.spliter.split_documents(document)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 切分内容为空，跳过")
                    # 如果是临时文件，删除
                    if files:
                        try:
                            os.unlink(file_path)
                        except:
                            pass
                    continue

                # 5. 异步写入向量库
                await asyncio.to_thread(self.vectors_store.add_documents, document)

                # 6. 保存MD5
                await self.save_md5_hex(md5_hex)
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已保存")

                # 如果是临时文件，删除
                if files:
                    try:
                        os.unlink(file_path)
                    except:
                        pass

            except Exception as e:
                logger.error(f"【向量数据库】文件 {file_path} 处理时出错: {e}")
                # 如果是临时文件，删除
                if files:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                continue


if __name__ == '__main__':
    async def main():
        store = VectorStoreService()
        await store.get_document()

        retriever = store.get_retriever()
        # 检索通过 to_thread 包裹
        results = await asyncio.to_thread(retriever.invoke, '扫地')
        print(f"检索结果数量: {len(results)}")
        for result in results:
            print(result)

    asyncio.run(main())