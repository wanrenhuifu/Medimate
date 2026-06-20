"""search_drug 工具 — RAG 语义检索药品说明书。"""
import json
from rag.embedding import embedder
from db.rag_repo import RagRepo
from config import config

rag_repo = RagRepo(top_k=config.rag_top_k)


async def search_drug(session_id: str, args: dict) -> str:
    drug_name = args.get("drug_name", "")
    if not drug_name:
        return json.dumps({"found": False, "error": "请提供药物名称"}, ensure_ascii=False)

    query_embedding = embedder.embed(drug_name)
    result = await rag_repo.search(drug_name, query_embedding)

    if result.found and result.drug:
        return json.dumps(
            {
                "found": True,
                "drug": result.drug.model_dump(),
                "chunks": [c.model_dump() for c in result.chunks],
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "found": False,
            "message": (
                f"未找到「{drug_name}」的相关信息。"
                "请检查药名拼写，或尝试使用通用名查询。"
                "如仍无法找到，建议查阅药品说明书或咨询药师。"
            ),
        },
        ensure_ascii=False,
    )
