<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import MessageBubble from './MessageBubble.vue'
import LoadingDots from './LoadingDots.vue'

const store = useChatStore()
const chatRef = ref(null)

// Scroll to bottom on new messages, tool results, or content updates
watch(
  () => [
    store.messages.length,
    store.currentToolCall,
    ...store.messages.map(m => (m.role === 'assistant' ? m.content?.length ?? 0 : 0)),
  ],
  async () => {
    await nextTick()
    chatRef.value?.scrollTo({ top: chatRef.value.scrollHeight, behavior: 'smooth' })
  }
)
</script>

<template>
  <div class="chat-area" ref="chatRef">
    <!-- Welcome Message -->
    <div v-if="store.messages.length === 0" class="welcome">
      <h2>👋 你好，我是 MediMate</h2>
      <p>你的智能用药助手</p>
      <div class="welcome-features">
        <span>💊 查询药物信息</span>
        <span>⚠️ 检查药物相互作用</span>
        <span>📊 查看不良反应数据</span>
        <span>📋 管理用药清单</span>
      </div>
      <p class="welcome-hint">你可以直接用自然语言问我，比如：<br>"布洛芬和阿司匹林能一起吃吗？"</p>
    </div>

    <!-- Messages -->
    <MessageBubble
      v-for="(msg, i) in store.messages"
      :key="i"
      :message="msg"
      :is-last="i === store.messages.length - 1"
    />

    <!-- Loading -->
    <LoadingDots v-if="store.isLoading && store.currentToolCall" :tool-name="store.currentToolCall.name" />
  </div>
</template>

<style scoped>
.chat-area {
  flex: 1; overflow-y: auto; padding: 24px;
  display: flex; flex-direction: column; gap: 16px;
}
.welcome {
  text-align: center; padding: 60px 20px;
}
.welcome h2 { font-size: 28px; margin-bottom: 8px; }
.welcome p { color: var(--text-secondary); margin-bottom: 24px; }
.welcome-features {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-bottom: 24px;
}
.welcome-features span {
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  padding: 8px 16px; border-radius: 20px; font-size: 14px;
}
.welcome-hint { font-size: 14px; color: var(--text-secondary); line-height: 1.8; }
</style>
