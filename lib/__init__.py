# 导入chroma模块中的函数
from .chroma import get_chroma_db
from .llm import initLLm

#初始化llm
initLLm()

# 自动执行数据存储生成
get_chroma_db()

print("向量数据库已自动初始化")