"""query_side_effects 工具 — 调用 OpenFDA FAERS API 查询不良反应数据。"""
import json
import httpx
from db.rag_repo import RagRepo

rag_repo = RagRepo()

# MedDRA 英文术语 → 中文 映射表
MEDDRA_CN_MAP = {
    "NAUSEA": "恶心",
    "HEADACHE": "头痛",
    "DIZZINESS": "头晕",
    "FATIGUE": "疲劳",
    "DIARRHOEA": "腹泻",
    "VOMITING": "呕吐",
    "RASH": "皮疹",
    "ABDOMINAL PAIN": "腹痛",
    "DYSPNOEA": "呼吸困难",
    "GASTROINTESTINAL HAEMORRHAGE": "胃肠道出血",
    "PRURITUS": "瘙痒",
    "INSOMNIA": "失眠",
    "PYREXIA": "发热",
    "PAIN": "疼痛",
    "DRUG INEFFECTIVE": "药物无效",
}

# 排除的非特异性术语（不展示给用户）
EXCLUDE_TERMS = {"DRUG INEFFECTIVE", "PRODUCT QUALITY ISSUE"}


async def query_side_effects(session_id: str, args: dict) -> str:
    drug_name = args.get("drug_name", "")
    top_n = args.get("top_n", 10)

    if not drug_name:
        return json.dumps(
            {"success": False, "error": "请提供药物名称"}, ensure_ascii=False
        )

    # 查找药物获取中文名
    fda_name = drug_name.upper()
    drug_name_cn = drug_name
    exact = await rag_repo.search_by_name(drug_name)
    if exact.found and exact.drug:
        drug_name_cn = exact.drug.name_cn

    # 调用 OpenFDA API
    url = (
        f"https://api.fda.gov/drug/event.json"
        f"?search=patient.drug.medicinalproduct:%22{fda_name}%22"
        f"&count=patient.reaction.reactionmeddrapt.exact"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return json.dumps(
                    {
                        "success": False,
                        "error": "FDA 数据暂时无法访问，请稍后重试",
                    },
                    ensure_ascii=False,
                )

            data = response.json()
            all_results = data.get("results", [])
            total_reports = (
                data.get("meta", {}).get("results", {}).get("total", 0)
            )

            # 翻译 + 过滤
            reactions = []
            for item in all_results:
                term_en = item.get("term", "")
                if term_en in EXCLUDE_TERMS:
                    continue
                reactions.append(
                    {
                        "term_en": term_en,
                        "term_cn": MEDDRA_CN_MAP.get(term_en, term_en),
                        "count": item.get("count", 0),
                    }
                )
                if len(reactions) >= top_n:
                    break

            return json.dumps(
                {
                    "success": True,
                    "drug_name_cn": drug_name_cn,
                    "reactions": reactions,
                    "total_reports": total_reports,
                },
                ensure_ascii=False,
            )

    except httpx.TimeoutException:
        return json.dumps(
            {
                "success": False,
                "error": "FDA 数据请求超时，请稍后重试",
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"查询 FDA 数据时出错: {str(e)}",
            },
            ensure_ascii=False,
        )
