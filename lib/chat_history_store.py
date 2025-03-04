from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import os
import json
from datetime import datetime

# 所有用户共用一个数据库目录
CHAT_HISTORY_PATH = "./chroma"

class ChatHistoryStore:
    def __init__(self):
        self.embedding_function = HuggingFaceEmbeddings()
        # 确保数据库目录存在
        os.makedirs(CHAT_HISTORY_PATH, exist_ok=True)
        # 初始化共享数据库
        self.db = Chroma(
            persist_directory=CHAT_HISTORY_PATH,
            embedding_function=self.embedding_function,
            collection_name="shared_chat_history"
        )
    
    def save_conversation(self, user_id, user_message, bot_response):
        """保存一轮对话到共享数据库"""
        timestamp = datetime.now().isoformat()
        metadata = {
            "timestamp": timestamp,
            "type": "conversation",
            "user_id": user_id
        }
        
        content = json.dumps({
            "user": user_message,
            "bot": bot_response,
            "timestamp": timestamp
        }, ensure_ascii=False)
        
        document = Document(page_content=content, metadata=metadata)
        self.db.add_documents([document])
        return True
    
    def load_recent_history(self, user_id, limit=10):
        """从共享数据库加载指定用户的最近聊天记录"""
        try:
            results = self.db.similarity_search(
                "最近的对话",
                k=limit,
                filter={"$and": [
                    {"user_id": {"$eq": user_id}},
                    {"type": {"$eq": "conversation"}}
                ]}
            )
            
            history = []
            for doc in results:
                try:
                    data = json.loads(doc.page_content)
                    history.append({
                        "user": data["user"],
                        "bot": data["bot"]
                    })
                except:
                    continue
            
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return history
            
        except Exception as e:
            print(f"加载用户历史记录失败: {str(e)}")
            return []