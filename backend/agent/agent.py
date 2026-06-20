"""Agent 核心 — Function Calling 循环。

接收用户消息 → 调用 DeepSeek API（流式）→ 如果有 tool_calls 则执行 →
把结果送回 LLM → 循环直到 LLM 返回纯文本 → 流式推送给前端。
"""
import json
from openai import AsyncOpenAI
from models.types import SSEEvent
from agent.prompt import SYSTEM_PROMPT, get_tools_definition
from agent.session import SessionStore
from tools.registry import ToolRegistry


class Agent:
    """MediMate Agent 核心。

    职责：仅控制 Function Calling 循环，不包含任何业务逻辑。
    所有智能行为由 LLM 通过 System Prompt + Tools 自主完成。
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        session_store: SessionStore,
        tool_registry: ToolRegistry,
    ):
        self.client = client
        self.model = model
        self.sessions = session_store
        self.tools = tool_registry

    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
        max_rounds: int = 5,
    ):
        """异步生成器：逐 token 产出 SSEEvent。"""
        # 1. 获取/创建会话，添加用户消息
        session = await self.sessions.get_or_create(session_id)

        # 确保 System Prompt 在第一条（原子操作，避免并发重复插入）
        await session.ensure_system_prompt(SYSTEM_PROMPT)

        await session.add_message({"role": "user", "content": user_message})

        # 2. Function Calling 循环
        for round_num in range(max_rounds):
            messages = await session.get_messages()

            # 调用 DeepSeek API（流式）
            try:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=get_tools_definition(),
                    stream=True,
                )
            except Exception as e:
                yield SSEEvent(type="error", content=f"AI 服务暂时不可用：{str(e)}")
                return

            # 收集流式响应
            full_content = ""
            tool_calls: list[dict] = []
            finish_reason = None

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                # 文本内容 → 逐 token 推送
                if delta.content:
                    full_content += delta.content
                    yield SSEEvent(type="token", content=delta.content)

                # 工具调用 → 收集（流式分 chunk）
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        while len(tool_calls) <= idx:
                            tool_calls.append(
                                {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            )
                        if tc.id:
                            tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls[idx]["function"]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls[idx]["function"]["arguments"] += tc.function.arguments

            # 判断是否有工具调用
            has_tool_calls = any(tc["id"] for tc in tool_calls)
            if has_tool_calls:
                # 将 assistant 消息（含 tool_calls）加入历史
                openai_tool_calls = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": tc["function"],
                    }
                    for tc in tool_calls
                ]
                await session.add_message(
                    {
                        "role": "assistant",
                        "content": full_content or None,
                        "tool_calls": openai_tool_calls,
                    }
                )

                # 执行工具并发送事件
                for tc in tool_calls:
                    if not tc["id"]:
                        continue
                    name = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    yield SSEEvent(type="tool_call", name=name, args=args)
                    result = await self.tools.execute(name, session_id, args)
                    try:
                        result_obj = json.loads(result)
                    except json.JSONDecodeError:
                        result_obj = {"raw": result}
                    yield SSEEvent(type="tool_result", name=name, result=result_obj)

                    await session.add_message(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        }
                    )

                # 继续循环，让 LLM 基于工具结果生成回复
                continue

            # 没有工具调用，LLM 直接生成了回复
            await session.add_message(
                {"role": "assistant", "content": full_content}
            )
            break

        # 3. 循环耗尽但未生成最终回复（所有轮次都用于工具调用）
        else:
            # max_rounds exhausted with tool calls — force a final response
            try:
                messages = await session.get_messages()
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield SSEEvent(
                            type="token",
                            content=chunk.choices[0].delta.content,
                        )
            except Exception:
                yield SSEEvent(
                    type="error",
                    content="处理过程过于复杂，请简化您的问题",
                )

        # 4. 裁剪历史 + 完成
        await session.trim(20)
        yield SSEEvent(type="done")
