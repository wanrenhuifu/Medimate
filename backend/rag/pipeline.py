"""RAG 数据流水线：药品说明书 → 切片 → 嵌入 → 入库。

用法:  python -m rag.pipeline --input_dir data/package_inserts
"""
import os
import glob
import argparse
from rag.chunker import chunk_document
from rag.embedding import embedder
from db.postgres import init_pg, get_pool, close_pg
from config import config


async def index_documents(input_dir: str, batch_size: int = 32):
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
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embedder.embed_batch(texts)

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
    main()
