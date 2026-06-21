# PLAN.md — MediMate 技术实现指南（全栈版）

> **本文档面向 AI Agent 阅读。** 按照此文档的指引，可以从零完整实现 MediMate 项目。
> 人类开发者同样可以参考此文档。

---

## 项目概述

MediMate 是一个全栈 AI 用药安全助手 Agent，采用 **Vue 3 + Vite** 前端 + **Python FastAPI** 后端 + **DeepSeek LLM Function Calling** 架构。

### 核心能力

1. **药物信息查询** — LLM 通过 Function Calling 调用 `search_drug` 工具，从 pgvector 向量库语义检索药品说明书
2. **药物相互作用检查** — LLM 调用 `check_interaction` 工具，RAG 增强检查多种药物之间的冲突
3. **FDA 不良反应查询** — LLM 调用 `query_side_effects` 工具，请求 OpenFDA FAERS API 获取真实数据
4. **个人用药清单** — LLM 调用 `manage_medication_list` 工具，对 Supabase PostgreSQL 做增删查操作
5. **紧急情况处理** — LLM 通过 System Prompt 安全规则自主识别紧急症状，引导就医
6. **流式回复** — SSE (Server-Sent Events) 实现逐字输出

### 技术栈

| 层 | 技术 | 版本建议 |
|----|------|---------|
| 前端 | Vue 3 + Vite | Vue 3.4+, Vite 5+ |
| 后端 | Python + FastAPI | Python 3.11+, FastAPI 0.110+ |
| LLM SDK | openai (Python) | openai >= 1.0 |
| 数据库 | Supabase PostgreSQL + pgvector | asyncpg >= 0.29 |
| 向量嵌入 | Embedding API（OpenAI 兼容） | openai >= 1.0 |
| HTTP 客户端 | httpx | httpx >= 0.27 |
| 数据校验 | Pydantic | Pydantic >= 2.0 |
| 异步 | asyncio + uvicorn | Python 标准库 + uvicorn |

### 数据架构：RAG + pgvector（核心设计）

**不再使用硬编码 JSON。** 药物知识通过 RAG（检索增强生成）从药品说明书中实时检索：

```
药品说明书（公开数据源）
    ↓ 切片 + 嵌入（Embedding API）
Supabase pgvector 向量库
    ↓ 语义检索（相似度匹配）
找到 Top-K 相关说明书段落
    ↓ 喂给 LLM System Prompt / 工具结果
Agent 生成准确、有据可查的回答
```

**为什么选 RAG 而非硬编码？**

| 维度 | 硬编码 JSON（已废弃） | RAG + pgvector（当前方案） |
|------|--------------------------|---------------------------|
| 药物覆盖 | 50 种手写 | 数千种，说明书自动覆盖 |
| 信息深度 | 6 个固定字段 | 说明书全文，任何细节都能查 |
| 扩展方式 | 改 JSON 代码 | 导入新说明书即可 |
| 可信度 | 手写可能出错 | 说明书原文引用 |
| 交互检查 | 35 组手写 | RAG 增强 + 结构化交互库 |

---

## 项目文件结构

```
d:\MediMate\
├── README.md
├── PLAN.md                      # 本文件
├── docs/                        # PRD 文档（14 个 .md 文件，已存在）
│
├── backend/                     # Python FastAPI 后端
│   ├── requirements.txt         # Python 依赖
│   ├── .env.example             # 环境变量模板
│   ├── main.py                  # 入口 + 路由 + 启动
│   ├── config.py                # 配置管理（从 .env 读取）
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent 核心：System Prompt + Function Calling 循环
│   │   ├── prompt.py            # System Prompt + Tools 定义
│   │   └── session.py           # 会话管理（内存存储 + 过期清理）
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py          # 工具注册表 + 分发器
│   │   ├── drug.py              # search_drug（RAG 语义检索药品说明书）
│   │   ├── interaction.py       # check_interaction（RAG 增强交互检查）
│   │   ├── sideeffects.py       # query_side_effects（OpenFDA API）
│   │   └── medlist.py           # manage_medication_list
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py          # Supabase 连接池 + pgvector 建表/索引
│   │   ├── rag_repo.py          # RAG 向量检索 repository
│   │   └── medlist_repo.py      # 用药清单 repository（PostgreSQL）
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedding.py         # Embedding API 封装（OpenAI 兼容）
│   │   ├── chunker.py           # 说明书文本切片
│   │   └── pipeline.py          # 数据流水线：抓取→切片→嵌入→入库
│   ├── models/
│   │   ├── __init__.py
│   │   └── types.py             # Pydantic 数据模型定义
│   └── data/
│       ├── package_inserts/     # 药品说明书原始文本（PDF/HTML/Markdown）
│       └── seed_interactions.json # 结构化交互数据（RAG 增强用）
│
├── frontend/                    # Vue 3 + Vite 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css
│       ├── api/chat.js
│       ├── stores/chat.js
│       ├── components/
│       │   ├── ChatArea.vue
│       │   ├── MessageBubble.vue
│       │   ├── DrugCard.vue
│       │   ├── InteractionResult.vue
│       │   ├── SideEffectsChart.vue
│       │   ├── MedList.vue
│       │   ├── EmergencyAlert.vue
│       │   ├── QuickActions.vue
│       │   ├── ChatInput.vue
│       │   └── LoadingDots.vue
│       └── utils/markdown.js
│
└── Makefile
```

---

## 实现顺序

```
Phase 1: 后端基础 + RAG 数据层
  Step 1:  backend/requirements.txt       — Python 依赖定义
  Step 2:  backend/.env.example           — 环境变量模板
  Step 3:  backend/config.py              — 配置管理
  Step 4:  backend/models/types.py        — Pydantic 数据模型
  Step 5:  backend/rag/embedding.py       — Embedding API 封装
  Step 6:  backend/rag/chunker.py         — 说明书文本切片
  Step 7:  backend/db/postgres.py         — Supabase + pgvector 建表
  Step 8:  backend/db/rag_repo.py         — RAG 向量检索
  Step 9:  backend/db/medlist_repo.py     — 用药清单
  Step 10: backend/rag/pipeline.py        — 数据流水线

Phase 2: 后端 Agent
  Step 11: backend/tools/registry.py      — 工具注册表
  Step 12: backend/tools/drug.py          — search_drug（RAG）
  Step 13: backend/tools/interaction.py   — check_interaction（RAG 增强）
  Step 14: backend/tools/sideeffects.py   — query_side_effects
  Step 15: backend/tools/medlist.py       — manage_medication_list
  Step 16: backend/agent/prompt.py        — System Prompt + Tools JSON
  Step 17: backend/agent/session.py       — 会话管理
  Step 18: backend/agent/agent.py         — Agent 核心 (Function Calling Loop)
  Step 19: backend/main.py                — 入口 + 路由 + SSE

Phase 3: 前端
  Step 20-26: Vue 3 前端（与之前相同）

Phase 4: 构建与联调
  Step 27: Makefile
  Step 28: 数据初始化 → 启动后端 → 启动前端 → 端到端测试
```

---

## Phase 1: 后端基础 + RAG 数据层

### Step 1: `backend/requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
openai>=1.30.0
asyncpg>=0.29.0
httpx>=0.27.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pgvector>=0.3.0
```

### Step 2: `backend/.env.example`

```
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@[PROJECT-ID].supabase.co:5432/postgres
EMBEDDING_API_KEY=sk-your-embedding-api-key
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=1024
RAG_TOP_K=5
PORT=8000
```

### Step 3: `backend/config.py`

```python
"""配置管理 — 从 .env 文件和环境变量加载配置。"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url: str = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
        )
        self.deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.supabase_db_url: str = os.getenv("SUPABASE_DB_URL", "")
        self.embedding_model: str = os.getenv(
            "EMBEDDING_MODEL", "BAAI/bge-m3"
        )
        self.embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))
        self.embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
        self.embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "")
        )
        self.rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
        self.port: int = int(os.getenv("PORT", "8000"))


config = Config()
```

### Step 4: `backend/models/types.py`

```python
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
    source: str = ""             # 来源：说明书文件名/段落编号
    score: float = 0.0           # 检索相似度分数


class DrugSearchResult(BaseModel):
    found: bool
    drug: DrugInfo | None = None
    chunks: list[DrugInfo] = []  # 多个检索片段


# ========== 交互相关 ==========

class Interaction(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
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
    type: str
    content: str | None = None
    name: str | None = None
    args: dict | None = None
    result: dict | None = None
```

### Step 5: `backend/rag/embedding.py`

```python
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
    """文本嵌入器（异步 API 模式）。"""

    def __init__(self):
        # Fallback: 如果 embedding 专用 key 未配置/是占位符，回退到 DeepSeek key
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

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model=self._model, input=text
        )
        return resp.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._model, input=texts
        )
        return [d.embedding for d in resp.data]


embedder = Embedder()
```

### Step 6: `backend/rag/chunker.py`

```python
"""药品说明书文本切片。

将完整的药品说明书按语义段落切分成小块，
每块保留足够的上下文（约 200-500 字），
相邻块之间有重叠以保证检索连贯性。
"""
import re


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """将长文本按段落和句子边界切片。

    Args:
        text: 药品说明书全文
        chunk_size: 每块目标字数
        overlap: 相邻块重叠字数
    Returns:
        文本块列表
    """
    # 1. 按段落分割
    paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 2. 短段落直接作为一个块
        if len(para) <= chunk_size:
            chunks.append(para)
            continue

        # 3. 长段落按句子分割
        sentences = re.split(r"(?<=[。！？；\.\!\?\;])", para)
        current = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(current) + len(sent) <= chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current)
                # 重叠：保留上一块的末尾
                if len(current) > overlap:
                    current = current[-overlap:] + sent
                else:
                    current = sent
        if current:
            chunks.append(current)

    return chunks


def chunk_document(
    filepath: str,
    drug_name_cn: str,
    drug_name_en: str = "",
    aliases: list[str] | None = None,
) -> list[dict]:
    """读取说明书文件，切片并附加元数据。

    Returns:
        [{"text": "...", "meta": {"name_cn": "...", "name_en": "...", "aliases": [...], "source": "..."}}]
    """
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    meta = {
        "name_cn": drug_name_cn,
        "name_en": drug_name_en,
        "aliases": aliases or [],
        "source": filepath,
    }
    return [{"text": c, "meta": meta, "chunk_index": i} for i, c in enumerate(chunks)]
```

### Step 7: `backend/db/postgres.py`

```python
"""Supabase PostgreSQL 连接池 + pgvector 扩展 + 建表。"""
import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pg(dsn: str, vector_dim: int = 512) -> asyncpg.Pool:
    """初始化连接池，启用 pgvector，创建药物知识库表。

    - 创建 asyncpg 连接池
    - 启用 pgvector 扩展（幂等）
    - 创建 drug_chunks 表（向量 + 元数据）
    - 创建 medications 表（用户用药清单）
    - 创建 IVFFlat 索引（加速向量检索）
    """
    global _pool
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)

    async with _pool.acquire() as conn:
        # 启用 pgvector 扩展
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # 药物知识库表（RAG）
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS drug_chunks (
                id SERIAL PRIMARY KEY,
                name_cn TEXT NOT NULL,
                name_en TEXT DEFAULT '',
                aliases TEXT[] DEFAULT '{{}}',
                chunk_text TEXT NOT NULL,
                chunk_index INT DEFAULT 0,
                source TEXT DEFAULT '',
                embedding vector({vector_dim})
            )
        """)

        # 向量检索索引（IVFFlat，适合 1000+ 条数据）
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_drug_chunks_embedding
                ON drug_chunks USING ivfflat (embedding vector_cosine_ops)
        """)

        # 文本搜索索引（支持别名/名称精确匹配）
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_drug_chunks_name
                ON drug_chunks USING gin (aliases)
        """)

        # 用户用药清单表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                drug_id TEXT NOT NULL,
                name_cn TEXT NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_medications_session
                ON medications(session_id)
        """)

    return _pool


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pg() first.")
    return _pool


async def close_pg():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
```

### Step 8: `backend/db/rag_repo.py`

```python
"""RAG 向量检索 Repository — 语义搜索药品说明书。"""
from db.postgres import get_pool
from models.types import DrugInfo, DrugSearchResult


class RagRepo:
    """药品知识 RAG 检索。"""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    async def search(
        self, query: str, query_embedding: list[float]
    ) -> DrugSearchResult:
        """语义搜索药品说明书。

        Args:
            query: 用户原始查询文本
            query_embedding: 查询文本的嵌入向量
        Returns:
            DrugSearchResult（含多个检索片段）
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            # pgvector 余弦相似度检索
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

        # 取最高分的药物名作为主结果
        best = chunks[0]
        return DrugSearchResult(
            found=True,
            drug=DrugInfo(
                name_cn=best.name_cn,
                name_en=best.name_en,
                aliases=best.aliases,
                content="\n\n---\n\n".join(c.content for c in chunks[:3]),
                source=" | ".join(c.source for c in chunks[:3]),
                score=best.score,
            ),
            chunks=chunks,
        )

    async def search_by_name(self, name: str) -> DrugSearchResult:
        """按名称精确检索（用于交互检查时快速定位药物）。

        先按别名数组精确匹配，匹配不到再走语义检索。
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            # 精确匹配：名称或别名
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
```

### Step 9: `backend/db/medlist_repo.py`

（与之前相同 — 用户用药清单持久化到 PostgreSQL）

```python
"""用药清单 Repository — 基于 Supabase PostgreSQL 持久化存储。"""
from models.types import Medication, MedListResult
from db.postgres import get_pool


class MedListRepo:
    async def get_medications(self, session_id: str) -> list[Medication]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT drug_id, name_cn FROM medications WHERE session_id = $1 ORDER BY added_at",
                session_id,
            )
        return [Medication(drug_id=row["drug_id"], name_cn=row["name_cn"]) for row in rows]

    async def add_medication(self, session_id: str, drug_id: str, name_cn: str) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchval(
                "SELECT id FROM medications WHERE session_id = $1 AND drug_id = $2",
                session_id, drug_id,
            )
            if existing:
                meds = await self.get_medications(session_id)
                return MedListResult(medications=meds, changed=False, message=f"药物「{name_cn}」已在您的用药清单中")
            await conn.execute(
                "INSERT INTO medications (session_id, drug_id, name_cn) VALUES ($1, $2, $3)",
                session_id, drug_id, name_cn,
            )
            meds = await self.get_medications(session_id)
            return MedListResult(medications=meds, changed=True, message=f"已将「{name_cn}」添加到您的用药清单")

    async def remove_medication(self, session_id: str, drug_id: str) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            name_cn = await conn.fetchval(
                "SELECT name_cn FROM medications WHERE session_id = $1 AND drug_id = $2",
                session_id, drug_id,
            )
            if not name_cn:
                meds = await self.get_medications(session_id)
                return MedListResult(medications=meds, changed=False, message="未在清单中找到该药物")
            await conn.execute("DELETE FROM medications WHERE session_id = $1 AND drug_id = $2", session_id, drug_id)
            meds = await self.get_medications(session_id)
            return MedListResult(medications=meds, changed=True, message=f"已将「{name_cn}」从用药清单中移除")

    async def clear(self, session_id: str) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM medications WHERE session_id = $1", session_id)
            return MedListResult(medications=[], changed=True, message="用药清单已清空")
```

### Step 10: `backend/rag/pipeline.py`

```python
"""RAG 数据流水线：药品说明书 → 切片 → 嵌入 → 入库。

用法：
    python -m rag.pipeline --input_dir data/package_inserts --batch_size 32
"""
import os
import glob
import argparse
from rag.chunker import chunk_document
from rag.embedding import embedder
from db.postgres import init_pg, close_pg
from config import config


async def index_documents(input_dir: str, batch_size: int = 32):
    """扫描目录下所有说明书文件，切片、嵌入、入库。"""
    print(f"Connecting to Supabase...")
    await init_pg(config.supabase_db_url, vector_dim=embedder.dimension)

    files = glob.glob(os.path.join(input_dir, "**/*.txt"), recursive=True)
    if not files:
        print(f"No .txt files found in {input_dir}")
        print("Put drug package insert text files in data/package_inserts/")
        print("Naming convention: [Chinese drug name].txt")
        return

    print(f"Found {len(files)} documents")

    all_chunks = []
    for filepath in sorted(files):
        basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            chunks = chunk_document(filepath, drug_name_cn=basename)
            all_chunks.extend(chunks)
            print(f"  {basename}: {len(chunks)} chunks")
        except Exception as e:
            print(f"  [SKIP] {basename}: {e}")

    if not all_chunks:
        print("No chunks generated. Check input files.")
        return

    texts = [c["text"] for c in all_chunks]
    print(f"Embedding {len(texts)} chunks in batches of {batch_size}...")

    # 分批嵌入，避免单次 API 请求超限
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}: {len(batch)} texts")
        batch_embeddings = await embedder.embed_batch(batch)
        embeddings.extend(batch_embeddings)

    # 批量入库
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 清空旧数据（幂等重导入）
        await conn.execute("TRUNCATE drug_chunks")

        for i, chunk in enumerate(all_chunks):
            meta = chunk["meta"]
            await conn.execute(
                """
                INSERT INTO drug_chunks (name_cn, name_en, aliases, chunk_text, chunk_index, source, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                meta["name_cn"],
                meta["name_en"],
                meta.get("aliases", []),
                chunk["text"],
                chunk["chunk_index"],
                meta["source"],
                str(embeddings[i]),
            )

        # 重建 IVFFlat 索引
        try:
            await conn.execute("DROP INDEX IF EXISTS idx_drug_chunks_embedding")
            await conn.execute(
                "CREATE INDEX idx_drug_chunks_embedding ON drug_chunks USING ivfflat (embedding vector_cosine_ops)"
            )
        except Exception:
            pass  # 数据太少时 IVFFlat 可能失败

    print(f"Done: {len(all_chunks)} chunks indexed")
    await close_pg()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default="data/package_inserts")
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    import asyncio
    asyncio.run(index_documents(args.input_dir, args.batch_size))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

> **说明书数据来源**：中国 NMPA 药品说明书可通过以下方式获取：
> 1. 国家药品监督管理局数据查询平台（需爬虫解析）
> 2. 丁香园用药助手公开数据
> 3. 药智网等第三方医药数据平台
> 初期建议手动收集 100-200 种常用药说明书（纯文本格式），放入 `data/package_inserts/` 目录。

---

## Phase 2: 后端 Agent

### Step 11: `backend/tools/registry.py`

```python
"""工具注册表 — 注册和分发 LLM 工具调用。"""
from typing import Any, Awaitable, Callable

ToolFunc = Callable[[str, dict[str, Any]], Awaitable[str]]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolFunc] = {}

    def register(self, name: str, func: ToolFunc):
        self._tools[name] = func

    async def execute(self, name: str, session_id: str, args: dict[str, Any]) -> str:
        if name not in self._tools:
            return '{"error": "未知工具: ' + name + '"}'
        try:
            return await self._tools[name](session_id, args)
        except Exception as e:
            return f'{{"error": "工具执行失败: {str(e)}"}}'
```

### Step 12: `backend/tools/drug.py` — search_drug（RAG 语义检索）

```python
"""search_drug 工具 — RAG 语义检索药品说明书。"""
import json
from rag.embedding import embedder
from db.rag_repo import RagRepo

rag_repo = RagRepo(top_k=5)


async def search_drug(session_id: str, args: dict) -> str:
    drug_name = args.get("drug_name", "")
    if not drug_name:
        return json.dumps({"found": False, "error": "请提供药物名称"}, ensure_ascii=False)

    # 先生成查询嵌入向量
    query_embedding = embedder.embed(drug_name)

    # RAG 检索
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
            "message": f"未找到「{drug_name}」的相关信息。请检查药名拼写，或尝试使用通用名查询。如仍无法找到，建议查阅药品说明书或咨询药师。",
        },
        ensure_ascii=False,
    )
```

### Step 13: `backend/tools/interaction.py` — check_interaction（RAG 增强）

```python
"""check_interaction 工具 — RAG 增强药物相互作用检查。"""
import json
from itertools import combinations
from rag.embedding import embedder
from db.rag_repo import RagRepo

rag_repo = RagRepo(top_k=3)


async def check_interaction(session_id: str, args: dict) -> str:
    drug_names: list[str] = args.get("drug_names", [])
    if len(drug_names) < 2:
        return json.dumps({"error": "请至少提供两种药物名称"}, ensure_ascii=False)

    # 1. 逐个解析药物名称（RAG 检索确认药物身份）
    resolved = []
    not_found = []
    for name in drug_names:
        q_emb = embedder.embed(name)
        result = await rag_repo.search(name, q_emb)
        if result.found and result.drug:
            resolved.append({"name": result.drug.name_cn, "en_name": result.drug.name_en})
        else:
            # 尝试精确名称匹配
            exact = await rag_repo.search_by_name(name)
            if exact.found and exact.drug:
                resolved.append({"name": exact.drug.name_cn, "en_name": exact.drug.name_en})
            else:
                not_found.append(name)

    # 2. 对每对药物，用 RAG 检索相互作用信息
    interaction_results = []
    not_checked = []

    for a, b in combinations(resolved, 2):
        query = f"{a['name']} 和 {b['name']} 相互作用 禁忌 配伍"
        q_emb = embedder.embed(query)
        result = await rag_repo.search(query, q_emb)

        if result.found and result.drug:
            content = result.drug.content
            # 简单启发式判断严重程度
            severity = "moderate"
            severe_keywords = ["禁用", "禁忌", "禁止联用", "严重", "致死", "中毒"]
            mild_keywords = ["安全", "无相互作用", "可联用", "不影响"]
            content_lower = content.lower()
            if any(kw in content_lower for kw in severe_keywords):
                severity = "severe"
            elif any(kw in content_lower for kw in mild_keywords):
                severity = "mild"

            interaction_results.append({
                "drug_a_cn": a["name"],
                "drug_b_cn": b["name"],
                "severity": severity,
                "description": content[:300],
                "mechanism": "",
                "advice": "",
                "source": result.drug.source,
            })
        else:
            not_checked.append(f"{a['name']} × {b['name']}")

    # 3. 按严重程度排序
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
```

### Step 14: `backend/tools/sideeffects.py`

（与之前相同 — 调用 OpenFDA FAERS API）

### Step 15: `backend/tools/medlist.py`

（与之前相同 — 管理用户用药清单）

### Step 16: `backend/agent/prompt.py`

System Prompt 需更新工具描述以反映 RAG 能力：

```python
SYSTEM_PROMPT = """# 角色

你是 MediMate，一个专业的用药安全助手 AI Agent。你的使命是帮助普通患者和家庭安全用药。

# 能力

你拥有以下工具：

1. **search_drug** — 从药品说明书中语义检索药物信息（用途、剂量、注意事项、禁忌症等）
2. **check_interaction** — 检查多种药物之间是否存在已知的相互作用风险
3. **query_side_effects** — 从 FDA 不良事件报告系统查询真实不良反应数据
4. **manage_medication_list** — 管理用户的个人用药清单

## 工具使用指南

- 当用户询问某种药物时，调用 search_drug
- 药物信息来自药品说明书原文，请引用来源
- 当用户提到多种药物并关心冲突时，调用 check_interaction
- 当用户关心副作用时，调用 query_side_effects；对于说明书中的不良反应信息，search_drug 也能回答
- 当用户提到"我在吃XX"、"新开了XX"、"停了XX"等，调用 manage_medication_list
- 当用户添加新药到用药清单时，主动调用 check_interaction 检查新药与已有药物的交互
- 你可以在一次回复中调用多个工具
- 如果 search_drug 检索结果相似度分数偏低（<0.5），提醒用户核实药名

# 行为规范

## 身份边界
- 你是用药信息助手，不是医生
- 不做诊断、不推荐药物、不调整处方
- 不确定时诚实说"我不确定，建议咨询医生"

## 回复风格
- 使用通俗易懂的中文
- 药物信息用结构化格式展示（Markdown）
- 交互检查结果标注风险等级：🔴 严重 / 🟡 中度 / 🟢 轻度 / ⚪ 未发现
- 引用说明书内容时标注来源段落

## 数据透明
- 说明信息来源（"来自药品说明书"或"来自 FDA FAERS 数据库"）
- 展示 FDA 数据时，说明"报告数据不代表因果关系，报告数量≠发生概率"

## 免责提示
- 每次给出用药相关建议时，附上"⚕️ 以上信息仅供参考，请遵医嘱"

# 安全规则（最高优先级）

## 紧急情况处理
当用户描述以下任何情况时，立即停止回答用药问题，转而劝导就医：
- 严重的身体症状（胸痛、呼吸困难、大量出血、意识模糊等）
- 药物过量或误服
- 自杀/自残意念

紧急情况的回复必须包含：
- 明确建议立即就医
- 急救电话 120
- 全国心理援助热线 400-161-9995（如涉及自杀/自残意念）
- "请不要依赖在线工具处理紧急情况"

## 绝对禁止
- 绝对不编造药物信息（只使用工具返回的数据）
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
                "description": "从药品说明书中语义检索药物详细信息（用途、剂量、注意事项、禁忌症）。支持中文通用名、英文名和常见商品名。药物信息来自真实药品说明书原文。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "药物名称（中文通用名、英文名或商品名均可）",
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
                "description": "检查两种或多种药物之间的相互作用风险。通过检索药品说明书中关于配伍禁忌和药物相互作用的信息来评估风险。",
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
                        "drug_name": {"type": "string", "description": "药物名称"},
                        "top_n": {"type": "integer", "description": "返回前 N 个不良反应", "default": 10},
                    },
                    "required": ["drug_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "manage_medication_list",
                "description": "管理用户的个人用药清单。支持添加药物、移除药物和查看清单。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add", "remove", "list"]},
                        "drug_name": {"type": "string", "description": "药物名称，add/remove 时必填"},
                    },
                    "required": ["action"],
                },
            },
        },
    ]
```

### Step 17-18: `backend/agent/session.py` + `backend/agent/agent.py`

（与之前相同 — Session 管理 + Function Calling 循环）

### Step 19: `backend/main.py`

```python
"""MediMate 后端入口 — FastAPI 应用 + SSE 路由。"""
import json
import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from config import config
from db.postgres import init_pg, close_pg
from db.medlist_repo import MedListRepo
from rag.embedding import embedder
from agent.session import SessionStore
from agent.agent import Agent
from tools.registry import ToolRegistry
from tools.drug import search_drug
from tools.interaction import check_interaction
from tools.sideeffects import query_side_effects
from tools.medlist import manage_medication_list, set_medlist_repo
from models.types import ChatRequest

session_store = SessionStore()
agent: Agent | None = None
medlist_repo: MedListRepo | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, medlist_repo

    # 初始化
    await init_pg(config.supabase_db_url, vector_dim=embedder.dimension)
    medlist_repo = MedListRepo()
    set_medlist_repo(medlist_repo)

    registry = ToolRegistry()
    registry.register("search_drug", search_drug)
    registry.register("check_interaction", check_interaction)
    registry.register("query_side_effects", query_side_effects)
    registry.register("manage_medication_list", manage_medication_list)

    client = AsyncOpenAI(api_key=config.deepseek_api_key, base_url=config.deepseek_base_url)
    agent = Agent(client, config.deepseek_model, session_store, registry)

    cleanup_task = asyncio.create_task(session_store.cleanup_loop())
    yield
    cleanup_task.cancel()
    await close_pg()


app = FastAPI(title="MediMate API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or uuid.uuid4().hex[:12]

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'content': session_id})}\n\n"
        async for event in agent.chat_stream(session_id, request.message):
            data = json.dumps(event.model_dump(), ensure_ascii=False)
            yield f"data: {data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@app.get("/api/medications/{session_id}")
async def get_medications(session_id: str):
    meds = await medlist_repo.get_medications(session_id)
    return {"medications": [m.model_dump() for m in meds]}


@app.delete("/api/medications/{session_id}")
async def clear_medications(session_id: str):
    result = await medlist_repo.clear(session_id)
    return result.model_dump()


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "MediMate"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.port, reload=True)
```

---

## Phase 3: 前端

（与之前相同 — Vue 3 + Vite 前端，10 个组件，Pinia store，SSE 流式解析）

---

## Phase 4: 构建与联调

### Step 27: `Makefile`

```makefile
.PHONY: dev-backend dev-frontend dev init-data

# 首次运行：导入说明书数据
init-data:
	cd backend && python -m rag.pipeline --input_dir data/package_inserts

# 开发模式启动后端
dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

# 开发模式启动前端
dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "请在两个终端分别运行："
	@echo "  make dev-backend"
	@echo "  make dev-frontend"
```

### Step 28: 启动与验证

```bash
# 0. 首次运行：导入说明书数据
cd d:\MediMate\backend
cp .env.example .env    # 填入 DEEPSEEK_API_KEY 和 SUPABASE_DB_URL
python -m rag.pipeline --input_dir data/package_inserts

# 终端 1: 启动后端
uvicorn main:app --reload --port 8000

# 终端 2: 启动前端
cd d:\MediMate\frontend
npm run dev
```

### 验证清单

#### RAG 检索验证
- [ ] 输入"布洛芬怎么吃" → search_drug RAG 检索 → 返回说明书原文片段（标注来源）
- [ ] 输入"泰诺" → 语义匹配到对乙酰氨基酚说明书
- [ ] 输入"头孢呋辛和阿莫西林能一起吃吗" → check_interaction → RAG 检索相互作用

#### Function Calling 验证
- [ ] 输入"阿司匹林有什么副作用" → LLM 调用 query_side_effects → 展示 OpenFDA 数据条形图
- [ ] 输入"我在吃华法林" → LLM 调用 manage_medication_list(add)
- [ ] 输入"我新开了阿司匹林" → LLM 调用 add + check_interaction → RAG 增强交互检查

#### 流式 + 安全 + 上下文 + 边界
（与之前相同）

---

## 注意事项

1. **Python 3.11+** — 使用 `asyncio` 原生异步
2. **openai 库兼容 DeepSeek** — 修改 `base_url` 和 `api_key` 即可
3. **嵌入 API** — 推荐硅基流动 SiliconFlow 免费额度，BGE-M3 模型，1024 维
4. **Supabase pgvector** — 通过 SQL `CREATE EXTENSION IF NOT EXISTS vector` 启用
5. **IVFFlat 索引** — 数据超过 1000 条后生效；初期数据少时自动退化为全表扫描
6. **说明书数据** — 首次运行前需执行 `make init-data` 将说明书导入向量库
7. **Session 线程安全** — 使用 `asyncio.Lock`
8. **Vite 代理** — 开发环境通过 Vite proxy 转发 `/api` 到后端
9. **向量维度** — 需与 PostgreSQL vector(N) 声明匹配（当前 1024）
10. **嵌入服务可替换** — 兼容 OpenAI embedding 接口，改 .env 即切换
