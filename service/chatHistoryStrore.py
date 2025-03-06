from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import os
import json
from datetime import datetime

import constant.chatRequest
from .chroma import ChromaService
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Optional, Dict, Any, Union, Tuple
from .prompt import ChatPrompt
from constant.chatRequest import ChatHistoryConstant


class ChatHistoryStore:
    def __init__(self) -> None:
        self.embedding_function: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
            model_name=os.getenv("HUGGINGFACE_EMBEDDINGS_MODEL_NAME"))
        self.db: Any = ChromaService.db

    def check_similarity(self, user_id: str, text: str, threshold: float = 0.8, k: int = 3) -> bool:
        """检查文本相似度"""
        text_vector = self.embedding_function.embed_query(text)

        results: List[Document] = self.db.similarity_search_by_vector(
            text_vector,
            k=k,
            filter={"$and": [
                {"user_id": {"$eq": user_id}},
                {"type": {"$eq": "conversation"}}
            ]}
        )

        for result in results:  # 这里不再是(result, score)的元组
            try:
                # 解析JSON内容
                data = json.loads(result.page_content)
                user_text = data.get("user", "")

                # 获取数据库中结果的嵌入向量
                result_vector = self.embedding_function.embed_query(user_text)

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

    def save_conversation(self, user_id: str, user_message: Optional[str] = None,
                          bot_response: Optional[str] = None) -> bool:
        """保存一轮对话到共享数据库"""
        # 检查问题和回答的相似度
        if user_message is not None and self.check_similarity(user_id, user_message):
            print("发现相似的问题，跳过保存。")
            return False

        if bot_response is not None and self.check_similarity(user_id, bot_response):
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

    def load_recent_history(self, user_id: str, limit: int = 100) -> List[ChatHistoryConstant]:
        """从共享数据库加载指定用户的最近聊天记录"""
        try:
            results = self.db.get(
                where={"$and": [
                    {"user_id": {"$eq": user_id}},
                    {"type": {"$eq": "conversation"}}
                ]},
                limit=limit,
                include=['documents', 'metadatas']
            )

            history: List[ChatHistoryConstant] = []
            if results and results.get('documents'):
                for doc in results['documents']:
                    try:
                        data = json.loads(doc)
                        history.append(
                            ChatHistoryConstant(
                                user=data["user"],
                                bot=data["bot"],
                                timestamp=data.get("timestamp")
                            ))
                    except:
                        continue

            history.sort(key=lambda x: x.timestamp, reverse=True)
            return history

        except Exception as e:
            print(f"加载用户历史记录失败: {str(e)}")
            return []

    def delete_user_history(self, user_id: str) -> bool:
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

    def summarize_user_history(self, user_id: str, llmService: any) -> bool:
        """提取用户的所有聊天记录，使用LLM模型总结，并更新到数据库"""
        try:
            results = self.db.get(
                where={"$and": [
                    {"user_id": {"$eq": user_id}},
                    {"type": {"$eq": "conversation"}}
                ]},
                include=['documents', 'metadatas']
            )

            if not results or not results.get('documents'):
                print(f"用户 {user_id} 没有聊天记录，跳过总结")
                return False

            conversations: List[Dict[str, str]] = []
            for doc in results['documents']:
                try:
                    data = json.loads(doc)
                    conversations.append({
                        "user": data.get("user", ""),
                         "bot": "",#这里不要机器人回答的 data.get("bot", ""),
                        "timestamp": data.get("timestamp", "")
                    })
                except Exception as e:
                    print(f"解析对话记录时出错: {e}")
                    continue

            conversations.sort(key=lambda x: x.get("timestamp", ""))
            if len(conversations) <= 1 :
                print(f"用户 {user_id} 只有一条记录不需要合并")
                return True

            summary_text: str = ChatPrompt().summarize(conversations)
            summary: str = llmService.generate_text(summary_text)

            self.delete_user_history(user_id)
            self.save_conversation(user_id, summary)

            print(f"已成功为用户 {user_id} 生成聊天记录总结")
            return True

        except Exception as e:
            print(f"总结用户历史记录失败: {str(e)}")
            return False

    def get_all_user_ids(self) -> List[str]:
        """获取所有用户的ID列表

        Returns:
            List[str]: 用户ID列表
        """
        try:
            # 使用空字符串作为查询文本，仅通过metadata筛选
            results = self.db.get(
                where={"type": {"$eq": "conversation"}},
                include=['metadatas']
            )

            # 从元数据中提取所有不重复的用户ID
            user_ids = set()
            if results and results.get('metadatas'):
                for metadata in results['metadatas']:
                    if metadata and 'user_id' in metadata:
                        user_ids.add(metadata['user_id'])

            return list(user_ids)
        except Exception as e:
            print(f"获取用户ID列表失败: {str(e)}")
            return []


# 初始化历史查询
ChatHistoryStoreService: ChatHistoryStore = ChatHistoryStore()
print("初始化历史查询类成功")
