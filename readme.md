# langchain Rag-Agent模式 AI客服
# 效果
![img.png](doc/img.png)

# 整体逻辑
## 区分不同的用户提问 => 提问的问题 => 提取关键词  => 组成json => 请求 服务后端api 拿到数据 => 再返回结果给llm 大模型 => 根据json返回的数据 => 回答客户

# 代码逻辑
## 输入问题  Agent 自动分析调用 Tools

# 实现功能
1. 支持chroma向量数据库 - 永久保存聊天记录
2. 根据用户id区分对话


# 后期待开发功能
1. 支持api提问


# 运行方式
``` python run tools_retriever.py```
or
```python run api.py```