"""manage_medication_list 工具 — 管理个人用药清单。"""
import json
from db.drug_repo import drug_repo
from db.medlist_repo import MedListRepo

# medlist_repo 由 main.py 注入
_repo: MedListRepo | None = None


def set_medlist_repo(repo: MedListRepo):
    global _repo
    _repo = repo


async def manage_medication_list(session_id: str, args: dict) -> str:
    action = args.get("action", "list")
    drug_name = args.get("drug_name", "")

    if action == "list":
        meds = await _repo.get_medications(session_id)
        return json.dumps(
            {
                "medications": [m.model_dump() for m in meds],
                "changed": False,
                "message": f"当前用药清单共 {len(meds)} 种药物",
            },
            ensure_ascii=False,
        )

    if action == "add":
        if not drug_name:
            return json.dumps(
                {"error": "请指定要添加的药物名称"}, ensure_ascii=False
            )
        drug_result = drug_repo.search(drug_name)
        if not drug_result.found or not drug_result.drug:
            return json.dumps(
                {
                    "error": f"未找到药物「{drug_name}」，无法添加到清单。请检查药名拼写或使用通用名"
                },
                ensure_ascii=False,
            )
        result = await _repo.add_medication(
            session_id, drug_result.drug.id, drug_result.drug.name_cn
        )
        return json.dumps(result.model_dump(), ensure_ascii=False)

    if action == "remove":
        if not drug_name:
            return json.dumps(
                {"error": "请指定要移除的药物名称"}, ensure_ascii=False
            )
        drug_result = drug_repo.search(drug_name)
        if not drug_result.found or not drug_result.drug:
            return json.dumps(
                {"error": f"未找到药物「{drug_name}」，无法从清单移除"},
                ensure_ascii=False,
            )
        result = await _repo.remove_medication(
            session_id, drug_result.drug.id
        )
        return json.dumps(result.model_dump(), ensure_ascii=False)

    return json.dumps({"error": f"未知操作: {action}"}, ensure_ascii=False)
