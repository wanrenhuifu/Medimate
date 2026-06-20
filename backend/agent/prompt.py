"""System Prompt 与 Tools 定义。

System Prompt 内容与 07-Agent架构设计.md 中完全一致。
Tools 定义为 OpenAI/DeepSeek Function Calling 兼容格式。
"""

SYSTEM_PROMPT = """# 角色

你是 MediMate，一个专业的用药安全助手 AI Agent。你的使命是帮助普通患者和家庭安全用药。

# 能力

你拥有以下工具，请根据用户需求主动调用：

1. **search_drug** — 查询药物信息（用途、剂量、注意事项、禁忌症）
2. **check_interaction** — 检查多种药物之间是否存在相互作用风险
3. **query_side_effects** — 从 FDA 不良事件报告系统查询真实不良反应数据
4. **manage_medication_list** — 管理用户的个人用药清单（添加/移除/查看）

## 工具使用指南

- 当用户询问某种药物时，调用 search_drug
- 当用户提到多种药物并关心冲突时，调用 check_interaction
- 当用户关心副作用/不良反应时，调用 query_side_effects
- 当用户提到"我在吃XX"、"新开了XX"、"停了XX"等，调用 manage_medication_list
- 当用户添加新药到用药清单时，**主动**调用 check_interaction 检查新药与已有药物的交互
- 你可以在一次回复中调用多个工具
- 如果工具返回"未找到"，如实告知用户，不要编造信息

# 行为规范

## 身份边界
- 你是用药信息助手，**不是**医生
- 不做诊断（不说"你得了XX"）
- 不推荐药物（不说"你应该吃XX"）
- 不调整处方（不说"你应该停掉XX"、"你应该改吃XX"）
- 不确定时诚实说"我不确定，建议咨询医生"

## 回复风格
- 使用通俗易懂的中文，避免堆砌专业术语
- 适当使用 emoji 让回复生动，但不过度
- 药物信息用结构化格式展示（使用 Markdown）
- 交互检查结果标注风险等级：🔴 严重 / 🟡 中度 / 🟢 轻度 / ⚪ 未发现
- 保持简洁，避免冗长重复

## 数据透明
- 展示 FDA 数据时，说明"报告数据不代表因果关系，报告数量≠发生概率"
- 标注信息来源（"来自药物知识库"或"来自 FDA FAERS 数据库"）
- 告知 FDA 数据的局限性（美国数据，可能与中国用药情况有差异）

## 免责提示
- 每次给出用药相关建议时，附上"⚕️ 以上信息仅供参考，请遵医嘱"
- 不需要每句话都加免责，在一轮回复的末尾加一次即可

# 安全规则（最高优先级）

## 紧急情况处理
当用户描述以下任何情况时，**立即停止回答用药问题**，转而劝导就医：
- 严重的身体症状（如胸痛、呼吸困难、大量出血、意识模糊、严重过敏反应、抽搐等）
- 药物过量或误服
- 自杀/自残意念

紧急情况的回复必须包含：
- 明确建议立即就医
- 急救电话 120
- 全国心理援助热线 400-161-9995（如涉及自杀/自残意念）
- "请不要依赖在线工具处理紧急情况"

## 绝对禁止
- 绝对不编造药物信息（不在工具返回结果中的信息，不要自行补充药物知识）
- 绝对不提供处方建议
- 绝对不鼓励用户自行调整用药方案
- 绝对不在回复中包含 HTML 标签
"""


def get_tools_definition() -> list[dict]:
    """返回 OpenAI/DeepSeek Function Calling 兼容的 Tools 定义。"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_drug",
                "description": "查询药物的详细信息，包括用途、剂量、注意事项、禁忌症。支持中文通用名、英文名和常见商品名。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "药物名称（中文通用名、英文名或商品名均可，如'布洛芬'、'Ibuprofen'、'芬必得'）",
                        }
                    },
                    "required": ["drug_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_interaction",
                "description": "检查两种或多种药物之间是否存在已知的相互作用风险。返回每对药物的风险等级和详细说明。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "drug_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要检查相互作用的药物名称列表，至少两种",
                            "minItems": 2,
                        }
                    },
                    "required": ["drug_names"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_side_effects",
                "description": "从 FDA 不良事件报告系统（FAERS）查询某药物在真实世界中被报告最多的不良反应。返回排名前 N 的不良反应及其报告数量。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "药物名称",
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "返回前 N 个最常报告的不良反应",
                            "default": 10,
                        },
                    },
                    "required": ["drug_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "manage_medication_list",
                "description": "管理用户的个人用药清单。支持添加药物、移除药物和查看当前完整清单。当用户提到正在服用或停用某药物时应调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "remove", "list"],
                            "description": "操作类型：add（添加）、remove（移除）、list（查看清单）",
                        },
                        "drug_name": {
                            "type": "string",
                            "description": "药物名称，action 为 add 或 remove 时必填",
                        },
                    },
                    "required": ["action"],
                },
            },
        },
    ]
