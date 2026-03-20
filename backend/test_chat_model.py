import asyncio
from app.utils.factory import chat_model

async def test_chat_model():
    print("测试聊天模型...")
    
    try:
        # 测试简单的聊天请求
        response = await chat_model.ainvoke("你好，请介绍一下你自己")
        print("聊天响应:", response.content)
        
        # 测试关于扫地机器人的问题
        response2 = await chat_model.ainvoke("扫地机器人有哪些主要功能？")
        print("扫地机器人功能:", response2.content)
        
        print("聊天功能测试成功！")
        
    except Exception as e:
        print(f"聊天功能测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_model())