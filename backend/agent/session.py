"""会话管理 — 内存存储 + 过期清理。"""
import time
import asyncio
from asyncio import Lock


class Session:
    """单个会话，包含对话历史和最近活跃时间。"""

    def __init__(self):
        self.messages: list[dict] = []
        self.last_active: float = time.time()
        self.lock = Lock()

    async def add_message(self, msg: dict):
        async with self.lock:
            self.messages.append(msg)
            self.last_active = time.time()

    async def get_messages(self) -> list[dict]:
        async with self.lock:
            return list(self.messages)

    async def ensure_system_prompt(self, prompt: str):
        """Atomically check and insert system prompt if missing. Returns True if inserted."""
        async with self.lock:
            if not self.messages or self.messages[0].get("role") != "system":
                self.messages.insert(0, {"role": "system", "content": prompt})
                self.last_active = time.time()
                return True
            return False

    async def trim(self, max_turns: int = 20):
        """滑动窗口裁剪历史消息。

        保留 System Prompt + 最近 max_turns 轮对话。
        一轮 = user + assistant（含 tool_calls）+ tool messages。
        """
        async with self.lock:
            if len(self.messages) <= 1 + max_turns * 2:
                return

            system_msg = (
                self.messages[0]
                if self.messages[0].get("role") == "system"
                else None
            )
            rest = self.messages[1:] if system_msg else self.messages

            user_indices = [
                i for i, m in enumerate(rest) if m.get("role") == "user"
            ]
            if len(user_indices) <= max_turns:
                return

            cutoff = user_indices[-max_turns]
            trimmed = rest[cutoff:]
            self.messages = [system_msg] + trimmed if system_msg else trimmed


class SessionStore:
    """会话管理器，使用 dict + Lock 存储会话。

    后台任务定期清理超过 30 分钟未活跃的会话。
    """

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    async def get_or_create(self, session_id: str) -> Session:
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session()
            return self._sessions[session_id]

    async def cleanup_loop(self, idle_timeout: int = 1800, interval: int = 300):
        """后台清理循环：每 `interval` 秒清理超过 `idle_timeout` 秒未活跃的会话。"""
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            async with self._lock:
                expired = [
                    sid
                    for sid, s in self._sessions.items()
                    if now - s.last_active > idle_timeout
                ]
                for sid in expired:
                    del self._sessions[sid]
