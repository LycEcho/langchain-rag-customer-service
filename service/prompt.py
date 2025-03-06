from langchain_core.prompts import ChatPromptTemplate


class ChatPrompt:
    def agent(self):
        # 修改代理提示模板
        return ChatPromptTemplate.from_template("""
        你是一个智能助手。
        
        对话历史（如没有就不使用）：
        {chat_history}
        
        工具列表: {tools}
        
        请严格按以下格式回答：
        Question: 需要回答的问题
        Thought: 你的思考过程
        Action: 需要使用的工具名称（必须是[{tool_names}]中的一个）
        Action Input: 工具需要的输入
        Observation: 工具返回的结果

        Thought: 我现在知道最终答案
        Final Answer: 最终回答内容
        
        用户问题：{input}
        {agent_scratchpad}
        """)

    def summarize(self,conversations:list):
        # 构建用于总结的文本
        summary_text = "以下是用户的聊天记录，请总结主要内容和关键信息，越简洁越好：\n\n"
        for conv in conversations:
            summary_text += f"用户: {conv['user']}\n回复: {conv['bot']}\n\n"
        return summary_text