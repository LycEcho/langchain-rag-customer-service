from .chatHistoryStrore import ChatHistoryStoreService
from .llm import LlmService
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

class Logic:
    def summarize_user_history(self, user_id: str):
        return ChatHistoryStoreService.summarize_user_history(user_id=user_id, llmService=LlmService)

    def generate_text_agent(self, question: str, user_id: Optional[str] = None,
                            chat_history: Optional[List[ChatHistoryConstant]] = None,
                            prompt: PromptTemplate = ChatPrompt().agent(), tools: List[Any] = Tools().get(),
                            use_history: bool = True) -> str:
        return LlmService.generate_text_agent(question=question, user_id=user_id, chat_history=chat_history,
                                              prompt=prompt, tools=tools, use_history=use_history,
                                              chatHistoryStoreService=ChatHistoryStoreService)
