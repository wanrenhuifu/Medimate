<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'

const store = useChatStore()
const medications = ref([])
const error = ref('')

async function loadMeds() {
  if (!store.sessionId) return
  try {
    const res = await fetch(`/api/medications/${store.sessionId}`)
    const data = await res.json()
    medications.value = data.medications || []
  } catch (e) {
    error.value = '加载失败'
  }
}

async function clearAll() {
  if (!store.sessionId) return
  await fetch(`/api/medications/${store.sessionId}`, { method: 'DELETE' })
  medications.value = []
}

// Reload when session changes or messages update
import { watch } from 'vue'
watch(() => store.sessionId, loadMeds)
watch(() => store.messages.length, loadMeds)

onMounted(loadMeds)
</script>

<template>
  <div class="med-list">
    <div class="list-header">
      <span>📋 用药清单</span>
      <button v-if="medications.length" class="btn-clear" @click="clearAll" title="清空">清空</button>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!medications.length && !error" class="empty">
      暂无用药记录<br>告诉我你在吃什么药吧
    </div>
    <ul v-if="medications.length">
      <li v-for="med in medications" :key="med.drug_id">
        <span class="pill">💊</span>
        <span>{{ med.name_cn }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.med-list { flex: 1; overflow-y: auto; padding: 0 16px 16px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 600; }
.btn-clear {
  background: none; border: 1px solid var(--border-glass); color: var(--text-secondary);
  padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer;
}
.btn-clear:hover { border-color: var(--severity-severe); color: var(--severity-severe); }
.empty { text-align: center; color: var(--text-secondary); font-size: 13px; padding: 24px 0; line-height: 1.8; }
.error { color: var(--severity-severe); font-size: 13px; }
ul { list-style: none; display: flex; flex-direction: column; gap: 6px; }
li { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 14px; }
.pill { font-size: 16px; }
</style>
