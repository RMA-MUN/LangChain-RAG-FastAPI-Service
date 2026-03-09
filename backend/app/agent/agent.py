from dotenv import load_dotenv
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agent.agent_tools import rag_summary_tools, get_weather_tools, what_time_is_now

load_dotenv()

# 初始化聊天模型
chat_model = ChatTongyi(model="qwen3-max")

# 定义工具列表，放入包装后的AsyncTool实例
tools = [
    rag_summary_tools,
    get_weather_tools,
    what_time_is_now,
]

# 创建Agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手，能够根据用户的问题选择合适的工具来回答。请根据用户的问题，选择最合适的工具来获取信息并回答用户。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# 创建工具调用Agent
agent = create_tool_calling_agent(chat_model, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True
)

async def get_agent_response(query: str, history: list = None):
    """
    获取Agent响应，支持会话历史
    :param query: 用户查询
    :param history: 会话历史，格式为[(user_msg, assistant_msg), ...]
    :return: Agent响应
    """
    try:
        # 构建聊天历史（原有逻辑不变）
        chat_history = []
        if history:
            for user_msg, assistant_msg in history:
                chat_history.append(HumanMessage(content=user_msg))
                chat_history.append(AIMessage(content=assistant_msg))

        # 使用Agent处理查询（ainvoke异步调用，适配异步工具）
        result = await agent_executor.ainvoke({
            "input": query,
            "chat_history": chat_history
        })

        # 检查结果类型（原有逻辑不变）
        if isinstance(result, dict):
            return result.get("output", "抱歉，我无法理解您的请求。")
        else:
            return str(result)
    except Exception as e:
        return f"抱歉，处理您的请求时出现了错误: {str(e)}"