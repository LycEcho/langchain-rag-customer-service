# 在文件顶部添加全局字典
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
import tools
import json
import llm
import prompt

# 创建全局字典存储用户记忆
user_memories = {}

# 确保create_react_agent正确接收模板变量
agent = create_react_agent(
    llm=llm.llm,
    tools=tools.tools,
    prompt=prompt.agent_prompt  # 传递完整的提示模板
)
# 调整代理执行器配置
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools.tools,
    max_iterations=3,  # 适当增加迭代次数
    verbose=True,
    handle_parsing_errors=True
)


# 修改内存初始化部分
def process_customer_question(question, user_id=None, chat_history=None):
    global user_memories

    # 获取或创建用户记忆 - 修复弃用警告
    if user_id not in user_memories:
        # 使用新的推荐方式创建记忆对象
        user_memories[user_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",  # 明确指定内存键
            k=30,  # 保留最近3轮对话
            return_messages=True  # 返回消息对象
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

    # 执行带历史记录的查询
    chat_history_value = memory.load_memory_variables({}).get("chat_history", "")
    response = agent_executor.invoke({
        "input": question,
        "chat_history": chat_history_value
    })

    # 保存更新后的记忆
    memory.save_context({"input": question}, {"output": response["output"]})

    return response["output"]


# # 用户A的对话
# response1 = process_customer_question("昨天的发货情况", user_id="user_123")
# print(response1)

# # 用户B的对话（独立历史）
# response2 = process_customer_question("订单1的状态", user_id="user_456")

# 带历史记录的调用
history_json = json.dumps({
    "history": [
        {"user": "昨天的发货情况", "bot": "2025-03-02发货了3个包裹"},
        {"user": "订单1的状态", "bot": "订单1已发货"},
        # {"user": "我是谁", "bot": "你是陈老师"}
    ]
})
response3 = process_customer_question("我是谁", user_id="user_789", chat_history=history_json)
print(response3)