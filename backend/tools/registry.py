"""工具注册表 — 注册和分发 LLM 工具调用。"""
from typing import Any, Awaitable, Callable

ToolFunc = Callable[[str, dict[str, Any]], Awaitable[str]]


class ToolRegistry:
    """工具注册表，通过 dict 注册工具函数。"""

    def __init__(self):
        self._tools: dict[str, ToolFunc] = {}

    def register(self, name: str, func: ToolFunc):
        self._tools[name] = func

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, session_id: str, args: dict[str, Any]) -> str:
        """执行指定工具，返回 JSON 字符串结果（给 LLM 读）。"""
        if name not in self._tools:
            return '{"error": "未知工具: ' + name + '"}'
        try:
            return await self._tools[name](session_id, args)
        except Exception as e:
            return f'{{"error": "工具执行失败: {str(e)}"}}'
