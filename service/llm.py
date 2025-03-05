import json
import os
from langchain_community.chat_models import ChatTongyi
from langchain.agents import AgentExecutor, create_react_agent
from .chatHistoryStrore import ChatHistoryStoreService
from .tools import Tools
from .prompt import ChatPrompt
from typing import Optional
from langchain.memory import ConversationBufferMemory


class LLM:
    """LLM 模型管理类"""

    def __init__(self):
        # 初始化相关属性
        self.model: Optional[ChatTongyi] = None
        self.agent = None
        self.agent_executor = None
        # 用户记忆字典
        self.user_memories = {}

    def init(self):
        """初始化 LLM 模型"""
        # 加载环境变量
        try:
            self.model = ChatTongyi(
                api_key=os.getenv("TONGYI_API_KEY"),
                model=os.getenv("TONGYI_MODEL", "qwen-max-2025-01-25"),
            )
            print("聊天模型初始化成功")
        except Exception as e:
            print("聊天模型初始化失败:", e)
            raise

        tools = Tools().get()
        prompt = ChatPrompt().get()

        # 确保create_react_agent正确接收模板变量
        self.agent = create_react_agent(
            llm=self.model,
            tools=tools,
            prompt=prompt  # 传递完整的提示模板
        )

        # 调整代理执行器配置
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            max_iterations=3,  # 适当增加迭代次数
            verbose=True,
            handle_parsing_errors=True
        )
        return self

    # 修改处理客户问题的函数
    def process_customer_question(self, question, user_id=None, chat_history=None):
        # 获取或创建用户记忆
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

        memory = self.user_memories[user_id]

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
                history = ChatHistoryStoreService.load_recent_history(user_id)
                if history:
                    # 清空当前记忆并加载历史
                    memory.clear()
                    for msg in history:
                        print("msg", msg)
                        memory.save_context({"input": msg["user"]}, {"output": msg["bot"]})
            except Exception as e:
                print(f"从向量数据库加载历史记录失败: {str(e)}")

        # 执行带历史记录的查询
        chat_history_value = memory.load_memory_variables({}).get("chat_history", "")
        response = self.agent_executor.invoke({
            "input": question,
            "chat_history": chat_history_value
        })

        output = response["output"]

        # 保存更新后的记忆
        memory.save_context({"input": question}, {"output": output})

        # 将对话保存到向量数据库
        if user_id:
            ChatHistoryStoreService.save_conversation(user_id, question, output)

        return output


# 初始化llm
LlmService: LLM = LLM().init()
print("初始化llm成功")