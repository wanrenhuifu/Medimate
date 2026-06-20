<script setup>
defineProps({
  toolName: { type: String, default: '' }
})

const toolNames = {
  search_drug: '🔍 正在查询药物信息...',
  check_interaction: '⚠️ 正在检查药物相互作用...',
  query_side_effects: '📊 正在获取 FDA 数据...',
  manage_medication_list: '📋 正在更新用药清单...',
}
</script>

<template>
  <div class="loading-dots">
    <span>{{ toolNames[toolName] || '处理中...' }}</span>
    <span class="dots"><i>.</i><i>.</i><i>.</i></span>
  </div>
</template>

<style scoped>
.loading-dots { display: flex; align-items: center; gap: 8px; padding: 8px 16px; font-size: 14px; color: var(--text-secondary); }
.dots i { animation: dot-bounce 1.4s infinite; font-style: normal; }
.dots i:nth-child(2) { animation-delay: 0.2s; }
.dots i:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }
</style>
