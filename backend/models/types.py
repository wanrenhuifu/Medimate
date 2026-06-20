"""Pydantic 数据模型定义。"""
from __future__ import annotations
from pydantic import BaseModel


# ========== 药物相关 ==========

class DrugInfo(BaseModel):
    """从 RAG 检索到的药物信息。"""
    name_cn: str = ""
    name_en: str = ""
    aliases: list[str] = []
    content: str = ""            # 说明书原文片段
    source: str = ""             # 来源：说明书文件名
    score: float = 0.0           # 检索相似度分数


class DrugSearchResult(BaseModel):
    found: bool
    drug: DrugInfo | None = None
    chunks: list[DrugInfo] = []  # 多个检索片段


# ========== 交互相关 ==========

class Interaction(BaseModel):
    drug_a: str
    drug_b: str
    severity: str  # "severe" | "moderate" | "mild"
    description: str
    mechanism: str
    advice: str


class InteractionCheckResult(BaseModel):
    drug_a_cn: str
    drug_b_cn: str
    severity: str
    description: str
    mechanism: str
    advice: str


# ========== 不良反应相关 ==========

class SideEffectItem(BaseModel):
    term_en: str
    term_cn: str
    count: int


class SideEffectsResult(BaseModel):
    success: bool
    drug_name_cn: str = ""
    reactions: list[SideEffectItem] = []
    total_reports: int = 0
    error: str = ""


# ========== 用药清单相关 ==========

class Medication(BaseModel):
    drug_id: str
    name_cn: str


class MedListResult(BaseModel):
    medications: list[Medication] = []
    changed: bool = False
    message: str = ""


# ========== API 相关 ==========

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class SSEEvent(BaseModel):
    type: str  # "token" | "tool_call" | "tool_result" | "done" | "error" | "session"
    content: str | None = None
    name: str | None = None
    args: dict | None = None
    result: dict | None = None
