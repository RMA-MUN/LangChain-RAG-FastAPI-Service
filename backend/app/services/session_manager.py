import json
import os
import asyncio
from typing import Dict, List, Tuple

import aiofiles
from app.utils.path_tool import get_abstract_path
from app.utils.logger_handler import logger


class SessionManager:
    """会话管理器"""

    def __init__(self, storage_path: str = "data/sessions.json"):
        """
        同步初始化（仅做属性赋值，不执行异步逻辑）
        :param storage_path: 会话数据存储路径（相对于项目根目录）
        """
        self.storage_path = get_abstract_path(storage_path)
        self.sessions: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()

    @classmethod
    async def create(cls, storage_path: str = "data/sessions.json") -> "SessionManager":
        """
        异步创建并初始化 SessionManager
        :param storage_path: 会话存储路径
        :return: 初始化完成的 SessionManager 实例
        """
        instance = cls(storage_path)
        await instance._load_sessions()  # 异步加载数据
        return instance

    async def _load_sessions(self):
        """异步加载会话数据"""
        if os.path.exists(self.storage_path):
            try:
                async with self._lock:  # 加锁保证并发安全
                    async with aiofiles.open(self.storage_path, 'r', encoding='utf-8') as f:
                        data = await f.read()  # 异步读文件
                        data = json.loads(data)
                        # 列表转元组
                        for session_id, session_data in data.items():
                            history = session_data.get("history", [])
                            session_data["history"] = [
                                (msg[0], msg[1]) for msg in history
                            ]
                        self.sessions = data
                logger.info(f"【会话管理】成功加载 {len(self.sessions)} 个会话")
            except Exception as e:
                logger.error(f"【会话管理】加载会话数据失败: {e}")
                self.sessions = {}
        else:
            logger.info("【会话管理】会话文件不存在，创建新的会话存储")
            self.sessions = {}

    async def _save_sessions(self):
        """异步保存会话数据（加锁 + aiofiles 异步写）"""
        try:
            # 确保目录存在（同步操作，目录创建无需异步）
            storage_dir = os.path.dirname(self.storage_path)
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)

            # 元组转列表（JSON 序列化要求）
            data_to_save = {}
            for session_id, session_data in self.sessions.items():
                history = session_data.get("history", [])
                data_to_save[session_id] = {
                    "history": [[msg[0], msg[1]] for msg in history]
                }

            # 异步写文件 + 锁保护
            async with self._lock:
                async with aiofiles.open(self.storage_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data_to_save, ensure_ascii=False, indent=2))

            logger.info(f"【会话管理】成功保存 {len(self.sessions)} 个会话")
        except Exception as e:
            logger.error(f"【会话管理】保存会话数据失败: {e}")

    async def get_session(self, session_id: str) -> Dict:
        """获取会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": []}
        return self.sessions[session_id]

    async def add_message(self, session_id: str, user_message: str, assistant_message: str):
        """添加消息并异步保存"""
        session = await self.get_session(session_id)
        session["history"].append((user_message, assistant_message))
        await self._save_sessions()

    async def get_history(self, session_id: str) -> List[Tuple[str, str]]:
        """获取会话历史"""
        session = await self.get_session(session_id)
        return session["history"]

    async def clear_session(self, session_id: str):
        """清除会话并保存"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            await self._save_sessions()
            logger.info(f"【会话管理】会话 {session_id} 已清除")

    async def get_all_session_ids(self) -> List[str]:
        """获取所有会话 ID"""
        return list(self.sessions.keys())

# 全局会话管理器实例
session_manager = None

if __name__ == '__main__':
    pass