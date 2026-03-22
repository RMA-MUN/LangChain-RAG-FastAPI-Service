import os
import json
import asyncio
from typing import List, Optional, AsyncGenerator

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from app.agent.agent_middleware import get_middleware
from app.agent.agent_tools import rag_summary_tools, get_weather_tools, what_time_is_now, get_user_info_tools, \
    reorder_documents_tools
from app.core.logger_handler import logger
from app.services import session_manager as sm
from app.utils.prompt_loader import load_prompt


class AgentFactory:
    """
    生产 Agent 工厂类
    支持：
    - 每次调用创建全新的 AgentExecutor 实例
    - 动态注入工具、提示词、模型配置
    - 支持异步流式调用
    """

    def __init__(
            self,
            model: str = "qwen2.5:7b",
            api_key: Optional[str] = None,
            default_tools: Optional[List[BaseTool]] = None,
            default_middleware: Optional[List] = None,
            default_system_prompt: Optional[str] = None,
    ):
        """
        初始化工厂配置（仅配置，不创建实例）
        :param model: 默认模型名称
        :param api_key: 默认 API Key（不传则从env读取）
        :param default_tools: 默认工具列表
        :param default_system_prompt: 默认系统提示词
        """
        self.model = model
        self.api_key = api_key or os.getenv("CHAT_API_KEY")
        self.default_tools = default_tools or self._get_default_tools()
        self.default_middleware = default_middleware or self._get_default_middleware()
        self.default_system_prompt = default_system_prompt or self._get_default_system_prompt()

    @staticmethod
    def _get_default_tools() -> List[BaseTool]:
        """获取默认工具列表"""
        return [
            rag_summary_tools,
            reorder_documents_tools,
            get_weather_tools,
            what_time_is_now,
            get_user_info_tools,
        ]

    def _get_default_middleware(self) -> List:
        """获取默认中间件列表"""
        return get_middleware()

    @staticmethod
    def _get_default_system_prompt() -> str:
        """获取默认系统提示词"""
        return load_prompt('main_prompt')

    def _create_chat_model(self, custom_model: Optional[str] = None) -> ChatOllama:
        """内部方法：创建聊天模型实例"""
        return ChatOllama(
            model=custom_model or self.model,
            base_url="http://localhost:11434",
            temperature=0.7,
            streaming=True  # 开启流式输出
        )

    def _create_prompt(self, custom_system_prompt: Optional[str] = None) -> ChatPromptTemplate:
        """内部方法：创建提示词模板"""
        return ChatPromptTemplate.from_messages([
            ("system", custom_system_prompt or self.default_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

    def create_agent_executor(
            self,
            custom_tools: Optional[List[BaseTool]] = None,
            custom_model: Optional[str] = None,
            custom_system_prompt: Optional[str] = None,
            verbose: bool = True,
            return_intermediate_steps: bool = True,
            **kwargs
    ) -> AgentExecutor:
        """
        核心工厂方法：创建全新的 AgentExecutor 实例
        每次调用都会生成新的实例，彻底避免全局状态污染

        :param custom_tools: 自定义工具列表（覆盖默认）
        :param custom_model: 自定义模型（覆盖默认）
        :param custom_system_prompt: 自定义系统提示词（覆盖默认）
        :param verbose: 是否打印详细日志
        :param return_intermediate_steps: 是否返回中间步骤
        :param kwargs: 其他 AgentExecutor 参数
        :return: 全新的 AgentExecutor 实例
        """
        # 1. 创建组件（每次都重新创建，避免全局状态污染）
        chat_model = self._create_chat_model(custom_model)
        prompt = self._create_prompt(custom_system_prompt)
        tools = custom_tools or self.default_tools

        # 2. 创建 Agent
        agent = create_tool_calling_agent(chat_model, tools, prompt)
        
        # 3. 创建 Executor
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=verbose,
            return_intermediate_steps=return_intermediate_steps,
            **kwargs
        )


# 初始化全局工厂配置
agent_factory = AgentFactory(model="qwen2.5:7b")


async def get_agent_response(
        query: str,
        history: Optional[List[tuple]] = None,
        custom_tools: Optional[List[BaseTool]] = None,
        **kwargs
):
    """
    获取 Agent 响应（使用工厂创建实例）
    :param query: 用户查询
    :param history: 会话历史 [(user_msg, assistant_msg), ...]
    :param custom_tools: 自定义工具（可选，用于动态切换工具）
    :param kwargs: 其他工厂参数
    :return: 响应结果
    """
    try:
        # 1. 从工厂获取全新的 Executor 实例
        agent_executor = agent_factory.create_agent_executor(custom_tools=custom_tools, **kwargs)

        # 2. 构建聊天历史
        chat_history: List[BaseMessage] = []
        if history:
            from langchain_core.messages import HumanMessage, AIMessage
            for user_msg, assistant_msg in history:
                chat_history.append(HumanMessage(content=user_msg))
                chat_history.append(AIMessage(content=assistant_msg))

        # 3. 流式执行
        full_response = []
        steps = []
        async for chunk in agent_executor.astream({
            "input": query,
            "chat_history": chat_history
        }):
            if "output" in chunk:
                full_response.append(chunk["output"])
            elif "intermediate_steps" in chunk:
                for action, observation in chunk["intermediate_steps"]:
                    # 记录日志
                    logger.info(f"\n\n🧠 [Agent 思考] {action.log}")
                    logger.info(f"🛠️ [调用工具] {action.tool}")
                    logger.info(f"📥 [工具输入] {action.tool_input}")
                    logger.info(f"📤 [工具结果] {observation}\n")
                    # 收集步骤
                    steps.append({
                        "thought": action.log,
                        "tool": action.tool,
                        "tool_input": action.tool_input,
                        "tool_output": observation
                    })

        return {
            "response": "".join(full_response) if full_response else "抱歉，我无法理解您的请求。",
            "steps": steps
        }

    except Exception as e:
        logger.error(f"Agent 执行错误: {str(e)}", exc_info=True)
        return {
            "response": f"抱歉，处理您的请求时出现了错误: {str(e)}",
            "steps": []
        }


async def get_agent_stream_response(
        query: str,
        session_id: str,
        user_id: str,
        custom_tools: Optional[List[BaseTool]] = None,
        **kwargs
) -> AsyncGenerator[str, None]:
    """
    获取 Agent 流式响应
    :param query: 用户查询
    :param session_id: 会话 ID
    :param user_id: 用户 ID
    :param custom_tools: 自定义工具（可选）
    :param kwargs: 其他参数
    :return: 流式响应生成器
    """
    try:
        logger.info(f"【Agent流式响应】开始处理请求，用户ID: {user_id}, 会话ID: {session_id}, 查询: {query}")
        
        # 获取会话历史
        history = await sm.session_manager.get_history(session_id, user_id)
        logger.info(f"【Agent流式响应】获取会话历史成功，历史记录数: {len(history)}")

        # 获取Agent响应
        result = await get_agent_response(query, history, custom_tools, **kwargs)
        response = result.get("response")
        steps = result.get("steps", [])
        
        logger.info(f"【Agent流式响应】获取Agent响应成功，响应长度: {len(response)}")
        
        # 记录步骤信息
        if steps:
            logger.info(f"【Agent流式响应】执行步骤数: {len(steps)}")
            for i, step in enumerate(steps):
                logger.info(f"【Agent流式响应】步骤 {i+1}: 调用工具 {step['tool']}")
                logger.info(f"【Agent流式响应】思考: {step['thought']}")
                logger.info(f"【Agent流式响应】工具输入: {step['tool_input']}")
                logger.info(f"【Agent流式响应】工具输出: {step['tool_output']}")
                logger.info(f"【Agent流式响应】工具输出: {step['tool_output']}")

        # 添加到会话历史
        await sm.session_manager.add_message(session_id, user_id, query, response)
        logger.info(f"【Agent流式响应】添加到会话历史成功")

        # 先发送步骤信息
        for step in steps:
            yield f"data: {json.dumps({'type': 'step', 'content': step}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        # 发送实际响应内容
        yield f"data: {json.dumps({'type': 'response', 'content': '', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        # 模拟流式输出，将响应分割成多个块
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            # 发送SSE格式的数据
            yield f"data: {json.dumps({'type': 'response', 'content': chunk}, ensure_ascii=False)}\n\n"
            # 模拟网络延迟
            await asyncio.sleep(0.1)

        # 发送结束标记
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        logger.info(f"【Agent流式响应】处理完成，会话ID: {session_id}")
    except Exception as e:
        logger.error(f"【Agent流式响应】处理请求失败: {e}", exc_info=True)
        # 发送错误信息
        error_message = f"错误: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'content': error_message, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"