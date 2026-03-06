import os, hashlib

from langchain_core.documents import Document

from app.utils.logger_handler import logger
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(file_path: str) -> str:
    """获取文件的md5值"""
    if not os.path.exists(file_path):
        logger.error(f"【md5计算】文件路径 {file_path} 不存在")
        return ""

    if not os.path.isfile(file_path):
        logger.error(f"【md5计算】文件路径 {file_path} 不是文件")
        return ""

    md5_object = hashlib.md5()
    chunk_size = 1024
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_object.update(chunk)
    except Exception as e:
        logger.error(f"【md5计算】读取文件 {file_path} 时出错: {e}")
        return ""

    return md5_object.hexdigest()

def listdir_allowed_type(path: str, allowed_types: tuple[str]) -> tuple:
    """
    获取指定目录下所有允许的文件类型
    :param path: 目录路径
    :param allowed_types: 允许的文件类型元组
    :return: 符合条件的文件路径列表
    """
    if not os.path.exists(path):
        logger.error(f"【文件列表】目录路径 {path} 不存在")
        return allowed_types

    if not os.path.isdir(path):
        logger.error(f"【文件列表】目录路径 {path} 不是目录")
        return allowed_types

    file_list = []
    for f in os.listdir(path):
        if f.endswith(allowed_types):
            file_list.append(os.path.join(path, f))

    return tuple(file_list)


def pdf_loader(file_path: str, password: str = None) -> list[Document]:
    """
    加载PDF文件内容
    :param file_path: PDF文件路径
    :param password: PDF密码（如果有）
    :return: PDF文件内容
    """
    return PyPDFLoader(file_path, password).load()


def txt_loader(file_path: str) -> list[Document]:
    """
    加载TXT文件内容
    :param file_path: TXT文件路径
    :return: TXT文件内容
    """
    return TextLoader(file_path).load()
