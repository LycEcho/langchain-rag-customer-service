# from langchain.document_loaders import DirectoryLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma as LangChainChroma

import os
import shutil
import time

CHROMA_PATH = "chroma"
DATA_PATH = "data"


class Chroma:
    """Chroma 向量数据库管理类"""

    # 类变量，用于跟踪是否已初始化
    _instance = None
    _initialized = False

    def __new__(cls):
        # 单例模式实现
        if cls._instance is None:
            cls._instance = super(Chroma, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 只初始化一次
        if not Chroma._initialized:
            print("开始初始化 Chroma...")
            start_time = time.time()
            
            print("正在加载嵌入模型...")
            embedding_start = time.time()
            self.db = None
            self.embedding_function = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_EMBEDDINGS_MODEL_NAME"))
            embedding_end = time.time()
            print(f"嵌入模型加载完成，耗时: {embedding_end - embedding_start:.2f} 秒")
            
            Chroma._initialized = True
            end_time = time.time()
            print(f"Chroma 初始化完成，总耗时: {end_time - start_time:.2f} 秒")

    def init(self):
        """初始化并连接到现有的Chroma向量数据库"""
        # 如果已经初始化过，直接返回现有实例
        if self.db is not None:
            return self

        # 检查数据库是否存在
        if not os.path.exists(CHROMA_PATH):
            print(f"警告: 向量数据库路径 {CHROMA_PATH} 不存在，正在自动创建...")
            # 自动创建目录
            os.makedirs(CHROMA_PATH, exist_ok=True)
            # 初始化一个空数据库
            self.generate_data_store()
            print(f"已自动创建并初始化空数据库: {CHROMA_PATH}")
            time.sleep(3)
        # 连接到现有的数据库
        print("正在连接到 Chroma 数据库...")
        start_time = time.time()
        self.db = LangChainChroma(persist_directory=CHROMA_PATH, embedding_function=self.embedding_function)
        end_time = time.time()
        print(f"成功连接到Chroma向量数据库，位于 {CHROMA_PATH}，耗时: {end_time - start_time:.2f} 秒")
        
        return self

    def generate_data_store(self):
        # documents = self.load_documents()
        # chunks = self.split_text(documents)
        self.save_to_chroma([])

    def load_documents(self):
        loader = DirectoryLoader(DATA_PATH, glob="*.md")
        documents = loader.load()
        return documents

    def split_text(self, documents: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

        if chunks:
            document = chunks[10] if len(chunks) > 10 else chunks[0]
            print(document.page_content)
            print(document.metadata)

        return chunks

    def save_to_chroma(self, chunks: list[Document]):
        # Clear out the database first.
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)

        # Create a new DB from the documents.
        self.db = LangChainChroma.from_documents(
            chunks, self.embedding_function, persist_directory=CHROMA_PATH
        )
        self.db.persist()
        print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

# 自动执行数据存储生成
ChromaService: Chroma | None = Chroma().init()
print("初始化Chroma成功")
