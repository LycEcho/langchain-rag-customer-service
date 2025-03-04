# 在文件顶部添加导入

import json
from lib import llm

# # 用户A的对话
# response1 = process_customer_question("昨天的发货情况", user_id="user_123")
# print(response1)

# # 用户B的对话（独立历史）
# response2 = process_customer_question("订单1的状态", user_id="user_456")

# 带历史记录的调用
# history_json = json.dumps({
#     "history": [
#         {"user": "昨天的发货情况", "bot": "2025-03-02发货了3个包裹"},
#         {"user": "订单1的状态", "bot": "订单1已发货"},
#         # {"user": "我是谁", "bot": "你是陈老师"}
#     ]
# })
# response3 = llm.process_customer_question("我是林先生", user_id="user_789", chat_history=history_json)
response3 = llm.process_customer_question("我是谁？", user_id="user_111")
print(response3)
response3 = llm.process_customer_question("我是谁？", user_id="user_789")
print(response3)