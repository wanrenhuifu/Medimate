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

    def validate(self) -> list[str]:
        """检查关键配置是否已填写，返回警告列表。"""
        warnings: list[str] = []

        if not self.deepseek_api_key or "your-deepseek" in self.deepseek_api_key.lower():
            warnings.append("DEEPSEEK_API_KEY 未配置（LLM 功能不可用）")

        if not self.supabase_db_url:
            warnings.append("SUPABASE_DB_URL 未配置（数据库功能不可用）")

        embedding_key = self.embedding_api_key
        if not embedding_key or "your-embedding" in embedding_key.lower() or "sk-your" in embedding_key.lower():
            # 检查 fallback 是否可用
            dsk = self.deepseek_api_key
            if not dsk or "your-deepseek" in dsk.lower():
                warnings.append(
                    "EMBEDDING_API_KEY 未配置，且 DeepSeek 不提供 embedding 服务。"
                    "请注册硅基流动 https://siliconflow.cn 获取免费 embedding API Key"
                )

        return warnings


config = Config()
