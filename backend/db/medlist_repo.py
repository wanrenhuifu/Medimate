"""用药清单 Repository — 基于 Supabase PostgreSQL 持久化存储。"""
import asyncpg
from models.types import Medication, MedListResult
from db.postgres import get_pool


class MedListRepo:
    """用药清单 Repository。

    通过 asyncpg 连接池操作 Supabase PostgreSQL。
    """

    async def get_medications(self, session_id: str) -> list[Medication]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT drug_id, name_cn FROM medications WHERE session_id = $1 ORDER BY added_at",
                session_id,
            )
        return [
            Medication(drug_id=row["drug_id"], name_cn=row["name_cn"]) for row in rows
        ]

    async def add_medication(
        self, session_id: str, drug_id: str, name_cn: str
    ) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # 检查是否已存在
            existing = await conn.fetchval(
                "SELECT id FROM medications WHERE session_id = $1 AND drug_id = $2",
                session_id,
                drug_id,
            )
            if existing:
                meds = await self.get_medications(session_id)
                return MedListResult(
                    medications=meds,
                    changed=False,
                    message=f"药物「{name_cn}」已在您的用药清单中",
                )

            await conn.execute(
                "INSERT INTO medications (session_id, drug_id, name_cn) VALUES ($1, $2, $3) "
                "ON CONFLICT (session_id, drug_id) DO NOTHING",
                session_id,
                drug_id,
                name_cn,
            )
            meds = await self.get_medications(session_id)
            return MedListResult(
                medications=meds,
                changed=True,
                message=f"已将「{name_cn}」添加到您的用药清单",
            )

    async def remove_medication(
        self, session_id: str, drug_id: str
    ) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            name_cn = await conn.fetchval(
                "SELECT name_cn FROM medications WHERE session_id = $1 AND drug_id = $2",
                session_id,
                drug_id,
            )
            if not name_cn:
                meds = await self.get_medications(session_id)
                return MedListResult(
                    medications=meds,
                    changed=False,
                    message="未在清单中找到该药物",
                )

            await conn.execute(
                "DELETE FROM medications WHERE session_id = $1 AND drug_id = $2",
                session_id,
                drug_id,
            )
            meds = await self.get_medications(session_id)
            return MedListResult(
                medications=meds,
                changed=True,
                message=f"已将「{name_cn}」从用药清单中移除",
            )

    async def clear(self, session_id: str) -> MedListResult:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM medications WHERE session_id = $1",
                session_id,
            )
            return MedListResult(
                medications=[], changed=True, message="用药清单已清空"
            )
