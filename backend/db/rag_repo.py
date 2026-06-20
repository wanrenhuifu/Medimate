"""RAG 向量检索 Repository — 语义搜索药品说明书。"""
from db.postgres import get_pool
from models.types import DrugInfo, DrugSearchResult


class RagRepo:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    async def search(
        self, query: str, query_embedding: list[float]
    ) -> DrugSearchResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT name_cn, name_en, aliases, chunk_text, source,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM drug_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                str(query_embedding),
                self.top_k,
            )

        if not rows:
            return DrugSearchResult(found=False, chunks=[])

        chunks = [
            DrugInfo(
                name_cn=row["name_cn"],
                name_en=row["name_en"],
                aliases=list(row["aliases"]) if row["aliases"] else [],
                content=row["chunk_text"],
                source=row["source"],
                score=round(row["similarity"], 4),
            )
            for row in rows
        ]

        best = chunks[0]
        return DrugSearchResult(
            found=True,
            drug=DrugInfo(
                name_cn=best.name_cn,
                name_en=best.name_en,
                aliases=best.aliases,
                content="\n\n---\n\n".join(c.content for c in chunks[:3]),
                source=" | ".join(
                    sorted(set(c.source for c in chunks[:3]))
                ),
                score=best.score,
            ),
            chunks=chunks,
        )

    async def search_by_name(self, name: str) -> DrugSearchResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT name_cn, name_en, aliases, chunk_text, source
                FROM drug_chunks
                WHERE name_cn = $1
                   OR name_en ILIKE $1
                   OR $1 = ANY(aliases)
                LIMIT 1
                """,
                name,
            )
            if row:
                chunks = [
                    DrugInfo(
                        name_cn=row["name_cn"],
                        name_en=row["name_en"],
                        aliases=list(row["aliases"]) if row["aliases"] else [],
                        content=row["chunk_text"],
                        source=row["source"],
                        score=1.0,
                    )
                ]
                return DrugSearchResult(found=True, drug=chunks[0], chunks=chunks)

        return DrugSearchResult(found=False, chunks=[])
