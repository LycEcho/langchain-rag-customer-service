from typing import Optional, Dict
from langchain_community.chat_models import ChatTongyi
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
import json
from .chat_history_store import  ChatHistoryStore
from langchain.agents import AgentExecutor, create_react_agent
from .tools import tools
from .prompt import agent_prompt

chat_history_store: ChatHistoryStore = ChatHistoryStore()
llm: Optional[ChatTongyi] = None
user_memories: Dict[str, ConversationBufferWindowMemory] = {}
agent: create_react_agent = None
agent_executor: AgentExecutor = None


def initLLm():
    global llm
    global agent_executor
    global agent

    # 加载环境变量
    load_dotenv()
    try:
        llm = ChatTongyi(
            api_key=os.getenv("TONGYI_API_KEY"),
            model=os.getenv("TONGYI_MODEL", "qwen-max-2025-01-25"),
        )
        print("聊天模型初始化成功")
    except Exception as e:
        print("聊天模型初始化失败:", e)
        raise

    # 确保create_react_agent正确接收模板变量
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=agent_prompt  # 传递完整的提示模板
    )
    # 调整代理执行器配置
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=3,  # 适当增加迭代次数
        verbose=True,
        handle_parsing_errors=True
    )


# 修改处理客户问题的函数
def process_customer_question(question, user_id=None, chat_history=None):
    global user_memories
    global agent_executor
    global agent
    global chat_history_store

    # 获取或创建用户记忆
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=30,
            return_messages=True
        )

    memory = user_memories[user_id]

    # 如果传入了历史记录（JSON格式）
    if chat_history:
        try:
            # 加载历史对话记录
            history_data = json.loads(chat_history)
            # 清空当前记忆并加载历史
            memory.clear()
            for msg in history_data.get("history", []):
                memory.save_context({"input": msg["user"]}, {"output": msg["bot"]})
        except Exception as e:
            print(f"历史记录加载失败: {str(e)}")
    # 如果没有传入历史记录，尝试从Chroma加载
    elif user_id:
        try:
            # 从向量数据库加载历史记录
            history = chat_history_store.load_recent_history(user_id)
            if history:
                # 清空当前记忆并加载历史
                memory.clear()
                for msg in history:
                    print("msg",msg)
                    memory.save_context({"input": msg["user"]}, {"output": msg["bot"]})
        except Exception as e:
            print(f"从向量数据库加载历史记录失败: {str(e)}")

    # 执行带历史记录的查询
    chat_history_value = memory.load_memory_variables({}).get("chat_history", "")
    response = agent_executor.invoke({
        "input": question,
        "chat_history": chat_history_value
    })

    output = response["output"]

    # 保存更新后的记忆
    memory.save_context({"input": question}, {"output": output})

    # 将对话保存到向量数据库
    if user_id:
        chat_history_store.save_conversation(user_id, question, output)

    return output
