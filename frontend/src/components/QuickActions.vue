<script setup>
import { useChatStore } from '../stores/chat'

const store = useChatStore()

const actions = [
  { label: '💊 查询药物', text: '请帮我查一下 ' },
  { label: '⚠️ 检查交互', text: ' 和  能一起吃吗？' },
  { label: '📊 查副作用', text: ' 有什么副作用？' },
  { label: '📋 我的用药', text: '查看我的用药清单' },
]

function quickAction(text) {
  store.send(text)
}
</script>

<template>
  <div class="quick-actions">
    <button
      v-for="a in actions" :key="a.label"
      @click="quickAction(a.text)"
      :disabled="store.isLoading"
    >{{ a.label }}</button>
  </div>
</template>

<style scoped>
.quick-actions { display: flex; gap: 8px; padding: 4px 16px; flex-wrap: wrap; }
button {
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  color: var(--text-secondary); padding: 6px 14px; border-radius: 20px;
  font-size: 13px; cursor: pointer; transition: all 0.2s;
}
button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
button:disabled { opacity: 0.4; cursor: default; }
</style>
