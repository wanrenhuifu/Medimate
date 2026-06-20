"""嵌入模型封装 — 通过 API 调用（兼容 OpenAI 接口格式）。

支持任意兼容 OpenAI embedding API 的服务商：
  - 阿里云 DashScope：https://dashscope.aliyuncs.com/compatible-mode/v1
  - 硅基流动 SiliconFlow：https://api.siliconflow.cn/v1（免费额度）
  - 智谱 AI：https://open.bigmodel.cn/api/paas/v4
  - OpenAI：https://api.openai.com/v1

配置方式：在 .env 中设置 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL
"""
from openai import OpenAI
from config import config


class Embedder:
    """文本嵌入器（API 模式）。"""

    def __init__(self):
        self._client = OpenAI(
            api_key=config.embedding_api_key or config.deepseek_api_key,
            base_url=config.embedding_base_url or config.deepseek_base_url,
        )
        self._model = config.embedding_model
        self._dim = config.embedding_dim
        print(f"Embedding API: {config.embedding_base_url or config.deepseek_base_url}")
        print(f"Embedding model: {self._model}, dim={self._dim}")

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        resp = self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return resp.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [d.embedding for d in resp.data]


embedder = Embedder()
