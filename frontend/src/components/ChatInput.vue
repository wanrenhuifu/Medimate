<script setup>
import { ref } from 'vue'
import { useChatStore } from '../stores/chat'

const store = useChatStore()
const input = ref('')

function send() {
  if (!input.value.trim() || store.isLoading) return
  store.send(input.value)
  input.value = ''
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="chat-input glass">
    <textarea
      v-model="input"
      @keydown="onKeydown"
      placeholder="输入用药问题... (Enter 发送, Shift+Enter 换行)"
      :disabled="store.isLoading"
      rows="1"
    ></textarea>
    <button @click="send" :disabled="!input.trim() || store.isLoading">
      <span v-if="store.isLoading">⏳</span>
      <span v-else>➤</span>
    </button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex; align-items: flex-end; gap: 8px;
  padding: 12px 16px; margin: 12px 16px 16px;
}
textarea {
  flex: 1; background: none; border: none; color: var(--text-primary);
  font-size: 15px; resize: none; outline: none; font-family: inherit;
  line-height: 1.5; max-height: 120px;
}
textarea::placeholder { color: var(--text-secondary); }
textarea:disabled { opacity: 0.5; }
button {
  background: var(--accent); color: #fff; border: none;
  width: 36px; height: 36px; border-radius: 50%; cursor: pointer;
  font-size: 16px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
button:disabled { opacity: 0.4; cursor: default; }
button:hover:not(:disabled) { background: var(--accent-hover); }
</style>
