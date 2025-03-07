import json
import os
from langchain_community.chat_models import ChatTongyi
from langchain.agents import AgentExecutor, create_react_agent
from .tools import Tools
from .prompt import ChatPrompt
from typing import Optional, Dict, List, Any, Union
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from constant.chatRequest import ChatHistoryConstant


class LLM:
    """LLM 模型管理类"""

    def __init__(self):
        # 初始化相关属性
        self.model: Optional[ChatTongyi] = None
        self.agent: Any = None
        self.agent_executor: Optional[AgentExecutor] = None
        # 用户记忆字典
        self.user_memories: Dict[str, ConversationBufferMemory] = {}

    def init(self) -> "LLM":
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

        return self

    # 普通模式
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成简单的文本回复

        Args:
            prompt: 用户输入的提示
            system_prompt: 系统提示，用于设置模型行为

        Returns:
            str: 模型生成的回复
        """
        if not self.model:
            raise ValueError("模型尚未初始化，请先调用 init() 方法")

        messages = []

        # 添加系统提示（如果有）
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # 添加用户提示
        messages.append(HumanMessage(content=prompt))

        # 调用模型生成回复
        response = self.model.invoke(messages)

        return response.content

    # 创建agent和执行器的辅助方法
    def _create_agent_executor(self, prompt: PromptTemplate, tools: List[Any]) -> AgentExecutor:
        """创建agent和执行器

        Args:
            prompt: agent提示模板
            tools: agent可用工具

        Returns:
            AgentExecutor: 配置好的agent执行器
        """
        # 创建agent
        self.agent = create_react_agent(
            llm=self.model,
            tools=tools,
            prompt=prompt
        )

        # 配置agent执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            max_iterations=3,
            verbose=True,
            handle_parsing_errors=True
        )

        return self.agent_executor

    # 不需要历史记录的agent模式
    def generate_text_agent_without_history(
            self,
            question: str,
            user_id: Optional[str] = None,
            store_id: Optional[str] = None,
            prompt: PromptTemplate = None,
            tools: List[Any] = None,
            chatHistoryStoreService: any = None
    ) -> str:

        """不使用历史记录的agent模式

        Args:
            question: 用户问题
            user_id: 用户ID，用于保存对话
            prompt: agent提示模板
            tools: agent可用工具

        Returns:
            str: 模型生成的回复
        """

        # 使用辅助方法创建agent执行器
        agent_executor = self._create_agent_executor(prompt, tools)

        # 直接执行查询，不使用历史记录
        response = agent_executor.invoke({
            "input": question,
            "chat_history": "",
            "user_id": user_id,
            "store_id": store_id
        })
        output = response["output"]

        # 如果提供了用户ID，保存对话
        if user_id:
            chatHistoryStoreService.save_conversation(user_id, question, output)

        return output

    # 需要历史记录的agent模式
    def generate_text_agent_with_history(
            self,
            question: str,
            user_id: Optional[str] = None,
            store_id: Optional[str] = None,
            chat_history: Optional[List[ChatHistoryConstant]] = None,
            prompt: PromptTemplate = None,
            tools: List[Any] = None,
            chatHistoryStoreService: any = None
    ) -> str:
        """使用历史记录的agent模式

        Args:
            question: 用户问题
            user_id: 用户ID
            chat_history: JSON格式的历史记录
            prompt: agent提示模板
            tools: agent可用工具

        Returns:
            str: 模型生成的回复
        """


        # 使用辅助方法创建agent执行器
        agent_executor = self._create_agent_executor(prompt, tools)

        # 获取或创建用户记忆
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

        memory = self.user_memories[user_id]

        # 如果传入了历史记录（JSON格式）
        if chat_history is not None and len(chat_history) > 0:
            try:
                # 清空当前记忆并加载历史
                memory.clear()
                for msg in chat_history:
                    memory.save_context({"input": msg.user}, {"output": msg.bot})
            except Exception as e:
                print(f"历史记录加载失败: {str(e)}")
        # 如果没有传入历史记录，尝试从Chroma加载
        elif user_id:
            try:
                # 从向量数据库加载历史记录
                history: List[ChatHistoryConstant] = chatHistoryStoreService.load_recent_history(user_id)
                if history:
                    # 清空当前记忆并加载历史
                    memory.clear()
                    for msg in history:
                        memory.save_context({"input": msg.user}, {"output": msg.bot})
            except Exception as e:
                print(f"从向量数据库加载历史记录失败: {str(e)}")

        # 执行带历史记录的查询
        chat_history_value = memory.load_memory_variables({}).get("chat_history", "")
        print("chat_history_value", chat_history_value)

        response = agent_executor.invoke({
            "input": question,
            "chat_history": chat_history_value,
            "user_id": user_id,
            "store_id":store_id
        })

        output = response["output"]

        # 保存更新后的记忆
        memory.save_context({"input": question}, {"output": output})

        # 将对话保存到向量数据库
        if user_id:
            chatHistoryStoreService.save_conversation(user_id, question, output)

        return output

    # 总函数，根据参数调用不同的实现
    def generate_text_agent(
            self,
            question: str,
            user_id: Optional[str] = None,
            store_id: Optional[str] = None,
            chat_history: Optional[List[ChatHistoryConstant]] = None,
            prompt: PromptTemplate = None,
            tools: List[Any] = None,
            use_history: bool = True,
            chatHistoryStoreService: any = None
    ) -> str:
        """Agent模式生成回复的总函数

        Args:
            question: 用户问题
            user_id: 用户ID
            chat_history: JSON格式的历史记录
            prompt: agent提示模板
            tools: agent可用工具
            use_history: 是否使用历史记录

        Returns:
            str: 模型生成的回复
        """
        if prompt is None:
            prompt = ChatPrompt().agent()
        if tools is None:
            tools = Tools().get()

        if use_history:
            return self.generate_text_agent_with_history(question=question, user_id=user_id,store_id=store_id, chat_history=chat_history,
                                                         prompt=prompt, tools=tools,
                                                         chatHistoryStoreService=chatHistoryStoreService)
        else:
            return self.generate_text_agent_without_history(question=question, user_id=user_id,store_id=store_id,
                                                            prompt=prompt, tools=tools,
                                                            chatHistoryStoreService=chatHistoryStoreService)


# 初始化llm
LlmService: LLM = LLM().init()
print("初始化llm成功")
