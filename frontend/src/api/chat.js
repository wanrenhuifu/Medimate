/** SSE 流式对话 API */
export async function sendMessage(message, sessionId, callbacks) {
  const { onSession, onToken, onToolCall, onToolResult, onDone, onError } = callbacks

  let response
  try {
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
  } catch (e) {
    onError?.('网络连接失败，请检查后端服务是否启动')
    return
  }

  if (!response.ok) {
    onError?.(`HTTP ${response.status}`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        onDone?.()
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          switch (data.type) {
            case 'session': onSession?.(data.content); break
            case 'token': onToken?.(data.content); break
            case 'tool_call': onToolCall?.(data.name, data.args); break
            case 'tool_result': onToolResult?.(data.name, data.result); break
            case 'done': onDone?.(); break
            case 'error': onError?.(data.content); break
          }
        } catch (e) {
          // skip malformed JSON lines
        }
      }
    }
  } catch (e) {
    onError?.('连接中断，请重试')
  }
}
