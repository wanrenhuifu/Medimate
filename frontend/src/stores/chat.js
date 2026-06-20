import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendMessage } from '../api/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const sessionId = ref('')
  const isLoading = ref(false)
  const currentToolCall = ref(null)

  function addUserMessage(text) {
    messages.value.push({ role: 'user', content: text })
  }

  async function send(text) {
    if (!text.trim() || isLoading.value) return
    addUserMessage(text)
    isLoading.value = true

    const assistantMsg = { role: 'assistant', content: '', toolResults: [] }
    messages.value.push(assistantMsg)

    await sendMessage(text, sessionId.value, {
      onSession(id) {
        sessionId.value = id
      },
      onToken(token) {
        assistantMsg.content += token
      },
      onToolCall(name, args) {
        currentToolCall.value = { name, args }
      },
      onToolResult(name, result) {
        assistantMsg.toolResults.push({ name, result })
        currentToolCall.value = null
      },
      onDone() {
        isLoading.value = false
      },
      onError(err) {
        if (!assistantMsg.content) {
          assistantMsg.content = `出错了：${err}`
        }
        isLoading.value = false
      },
    })
  }

  function clearMessages() {
    messages.value = []
  }

  return { messages, sessionId, isLoading, currentToolCall, send, addUserMessage, clearMessages }
})
