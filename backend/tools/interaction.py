"""check_interaction 工具 — RAG 增强药物相互作用检查。"""
import json
from itertools import combinations
from rag.embedding import embedder
from db.rag_repo import RagRepo
from config import config

rag_repo = RagRepo(top_k=config.rag_top_k)

SEVERE_KEYWORDS = ["禁用", "禁忌", "禁止联用", "严重", "致死", "中毒", "极高风险"]
MILD_KEYWORDS = ["安全", "无相互作用", "可联用", "不影响", "未见", "暂无"]
NEGATION_PATTERNS = ["无", "未", "不", "没有", "并非", "非"]


def _is_negation_free(keyword: str, text: str) -> bool:
    """Check if keyword appears in text without being negated."""
    idx = text.find(keyword)
    if idx == -1:
        return False
    # Check up to 3 characters before the keyword for negation
    prefix = text[max(0, idx - 3):idx]
    for neg in NEGATION_PATTERNS:
        if neg in prefix:
            return False
    return True


async def check_interaction(session_id: str, args: dict) -> str:
    drug_names: list[str] = args.get("drug_names", [])
    if len(drug_names) < 2:
        return json.dumps({"error": "请至少提供两种药物名称"}, ensure_ascii=False)

    # 解析药物身份
    resolved: list[dict] = []
    not_found: list[str] = []
    seen_names: set[str] = set()

    for name in drug_names:
        exact = await rag_repo.search_by_name(name)
        if exact.found and exact.drug:
            if exact.drug.name_cn not in seen_names:
                resolved.append({"name": exact.drug.name_cn, "en_name": exact.drug.name_en})
                seen_names.add(exact.drug.name_cn)
        else:
            q_emb = await embedder.embed(name)
            semantic = await rag_repo.search(name, q_emb)
            if semantic.found and semantic.chunks:
                best = semantic.chunks[0]
                if best.score > 0.5 and best.name_cn not in seen_names:
                    resolved.append({"name": best.name_cn, "en_name": best.name_en})
                    seen_names.add(best.name_cn)
                else:
                    not_found.append(name)
            else:
                not_found.append(name)

    # RAG 检索药物对相互作用
    interaction_results = []
    not_checked = []

    for a, b in combinations(resolved, 2):
        query = f"{a['name']} 和 {b['name']} 相互作用 配伍禁忌 联合用药"
        q_emb = await embedder.embed(query)
        result = await rag_repo.search(query, q_emb)

        if result.found and result.chunks:
            content = result.chunks[0].content
            content_lower = content.lower()

            severity = "moderate"
            if any(_is_negation_free(kw, content_lower) for kw in SEVERE_KEYWORDS):
                severity = "severe"
            elif any(_is_negation_free(kw, content_lower) for kw in MILD_KEYWORDS):
                severity = "mild"

            interaction_results.append({
                "drug_a_cn": a["name"],
                "drug_b_cn": b["name"],
                "severity": severity,
                "description": content[:400],
                "mechanism": "",
                "advice": "",
                "source": result.chunks[0].source,
            })
        else:
            not_checked.append(f"{a['name']} × {b['name']}")

    severity_order = {"severe": 0, "moderate": 1, "mild": 2}
    interaction_results.sort(key=lambda r: severity_order.get(r["severity"], 3))

    return json.dumps(
        {
            "results": interaction_results,
            "not_found": not_found,
            "not_checked": not_checked,
        },
        ensure_ascii=False,
    )
