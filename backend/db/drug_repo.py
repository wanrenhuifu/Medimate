"""药物查询 Repository — 封装名称查找 + 语义搜索回退。"""
from rag.embedding import embedder
from db.rag_repo import RagRepo
from models.types import DrugSearchResult
from config import config


class DrugRepo:
    """药物查询，先精确名称匹配，失败后回退到语义搜索。"""

    def __init__(self):
        self._rag = RagRepo(top_k=config.rag_top_k)

    async def search(self, name: str) -> DrugSearchResult:
        # 1. 先尝试精确名称匹配
        exact = await self._rag.search_by_name(name)
        if exact.found and exact.drug:
            return exact

        # 2. 回退到语义向量搜索
        query_embedding = await embedder.embed(name)
        return await self._rag.search(name, query_embedding)


drug_repo = DrugRepo()
