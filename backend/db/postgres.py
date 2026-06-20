"""Supabase PostgreSQL 连接池 + pgvector 扩展 + 建表。"""
import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pg(dsn: str, vector_dim: int = 512) -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)

    async with _pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

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

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_drug_chunks_name
                ON drug_chunks USING gin (aliases)
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                drug_id TEXT NOT NULL,
                name_cn TEXT NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(session_id, drug_id)
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
