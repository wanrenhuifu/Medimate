"""嵌入模型封装 — 通过 API 调用（兼容 OpenAI 接口格式）。

支持任意兼容 OpenAI embedding API 的服务商：
  - 阿里云 DashScope：https://dashscope.aliyuncs.com/compatible-mode/v1
  - 硅基流动 SiliconFlow：https://api.siliconflow.cn/v1（免费额度）
  - 智谱 AI：https://open.bigmodel.cn/api/paas/v4
  - OpenAI：https://api.openai.com/v1

配置方式：在 .env 中设置 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL
"""
from openai import AsyncOpenAI
from config import config


class Embedder:
    """文本嵌入器（API 模式）。"""

    def __init__(self):
        # Fallback: 如果 embedding 专用 key 未配置/是占位符，回退到 DeepSeek key
        # 注意：DeepSeek 不提供 embedding API，回退后 base_url 仍是 DeepSeek 时会失败
        api_key = config.embedding_api_key
        base_url = config.embedding_base_url
        if not api_key or "sk-your" in api_key:
            api_key = config.deepseek_api_key
        if not base_url:
            base_url = config.deepseek_base_url

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = config.embedding_model
        self._dim = config.embedding_dim
        print(f"Embedding API: {base_url}")
        print(f"Embedding model: {self._model}, dim={self._dim}")
        if not config.embedding_api_key or "sk-your" in config.embedding_api_key:
            print("⚠️  EMBEDDING_API_KEY 为占位符，使用 DeepSeek key 作为 fallback")
            print("⚠️  如 DeepSeek 不支持 embedding，请注册硅基流动: https://siliconflow.cn")

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return resp.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [d.embedding for d in resp.data]


embedder = Embedder()
