from langchain_community.chat_models import ChatTongyi
import os
from dotenv import load_dotenv

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