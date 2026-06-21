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

# 启动时检查配置
_config_warnings = config.validate()
if _config_warnings:
    print("=" * 50)
    print("⚠️  配置警告：")
    for w in _config_warnings:
        print(f"  - {w}")
    print("=" * 50)

session_store = SessionStore()
agent: Agent | None = None
medlist_repo: MedListRepo | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, medlist_repo

    await init_pg(config.supabase_db_url, vector_dim=embedder.dimension)
    medlist_repo = MedListRepo()
    set_medlist_repo(medlist_repo)

    registry = ToolRegistry()
    registry.register("search_drug", search_drug)
    registry.register("check_interaction", check_interaction)
    registry.register("query_side_effects", query_side_effects)
    registry.register("manage_medication_list", manage_medication_list)

    client = AsyncOpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )
    agent = Agent(client, config.deepseek_model, session_store, registry)

    cleanup_task = asyncio.create_task(session_store.cleanup_loop())
    yield
    cleanup_task.cancel()
    await close_pg()


app = FastAPI(title="MediMate API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or uuid.uuid4().hex[:12]

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'content': session_id})}\n\n"
        async for event in agent.chat_stream(session_id, request.message):
            data = json.dumps(event.model_dump(), ensure_ascii=False)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
