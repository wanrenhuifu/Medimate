"""配置管理 — 从 .env 文件和环境变量加载配置。"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        # DeepSeek (LLM)
        self.deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url: str = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
        )
        self.deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        # Supabase
        self.supabase_db_url: str = os.getenv("SUPABASE_DB_URL", "")

        # Embedding API
        self.embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
        self.embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "")
        self.embedding_model: str = os.getenv(
            "EMBEDDING_MODEL", "BAAI/bge-m3"
        )
        self.embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))

        # RAG
        self.rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
        self.port: int = int(os.getenv("PORT", "8000"))


config = Config()
