from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.utils.config import rag_config

# 加载环境变量
load_dotenv()


class BaseModelFactory(ABC):
    """基础模型工厂"""

    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        pass


class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        return ChatTongyi(
            model=rag_config['chat_model_name'],
            dashscope_api_key=os.getenv('DASHSCOPE_API_KEY')
        )


class EmbedModelFactory(BaseModelFactory):
    """嵌入模型工厂"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        """生成模型"""
        return DashScopeEmbeddings(
            model=rag_config['embed_model_name'],
            dashscope_api_key=os.getenv('DASHSCOPE_API_KEY')
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbedModelFactory().generator()