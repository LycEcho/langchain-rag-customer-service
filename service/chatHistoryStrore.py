from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import os
import json
from datetime import datetime
from .chroma import ChromaService
from sklearn.metrics.pairwise import cosine_similarity


class ChatHistoryStore:
    def __init__(self):
        self.embedding_function = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_EMBEDDINGS_MODEL_NAME"))
        # 使用项目中的Chroma类
        self.db = ChromaService.db

    def check_similarity(self, user_id, text, threshold=0.8, k=3):
        """检查文本相似度
        Args:
            user_id: 用户ID
            text: 要检查的文本
            threshold: 相似度阈值
            k: 返回结果数量
        Returns:
            bool: True 表示发现相似文本，False 表示未发现
        """
        # 获取文本的嵌入向量
        text_vector = self.embedding_function.embed_query(text)

        results = self.db.similarity_search_with_score(
            text,
            k=k,
            filter={"$and": [
                {"user_id": {"$eq": user_id}},
                {"type": {"$eq": "conversation"}}
            ]}
        )

        for result, score in results:
            try:
                # 获取数据库中结果的嵌入向量
                result_vector = self.embedding_function.embed_query(result.page_content)
                # 计算余弦相似度
                cosine_sim = cosine_similarity([text_vector], [result_vector])[0][0]
                if cosine_sim > threshold:
                    print(result)
                    print(f"发现相似文本(相似度: {cosine_sim})，超过阈值 {threshold}")
                    return True
            except Exception as e:
                print(f"解析结果时出错: {e}")
                continue
        return False

    def save_conversation(self, user_id, user_message, bot_response):
        """保存一轮对话到共享数据库"""
        # 检查问题和回答的相似度
        if self.check_similarity(user_id, user_message):
            print("发现相似的问题，跳过保存。")
            return False

        if self.check_similarity(user_id, bot_response):
            print("发现相似的回答，跳过保存。")
            return False
        # 保存新对话
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
                "abc",
                k=limit,
                filter={"$and": [
                    {"user_id": {"$eq": user_id}},
                    {"type": {"$eq": "conversation"}}
                ]}
            )

            history = []
            for doc in results:
                try:
                    print(doc)
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

    def delete_user_history(self, user_id):
        """删除指定用户的所有对话记录"""
        try:
            self.db.delete(
                where={"$and": [
                    {"user_id": {"$eq": user_id}},
                    {"type": {"$eq": "conversation"}}
                ]}
            )
            print(f"已删除用户 {user_id} 的所有记录")
            return True
        except Exception as e:
            print(f"删除用户记录失败: {str(e)}")
            return False


# 初始化历史查询
ChatHistoryStoreService: ChatHistoryStore = ChatHistoryStore()
print("初始化历史查询类成功")
