<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const severityConfig = {
  severe: { label: '严重', color: 'var(--severity-severe)', icon: '🔴' },
  moderate: { label: '中度', color: 'var(--severity-moderate)', icon: '🟡' },
  mild: { label: '轻度', color: 'var(--severity-mild)', icon: '🟢' },
}

const results = computed(() => props.data.results || [])
const notFound = computed(() => props.data.not_found || [])
const notChecked = computed(() => props.data.not_checked || [])

function config(severity) {
  return severityConfig[severity] || { label: '未知', color: '#999', icon: '⚪' }
}
</script>

<template>
  <div class="interaction-result glass">
    <div v-if="results.length" class="results">
      <div v-for="(r, i) in results" :key="i" class="result-item">
        <div class="pair">
          <span class="drug-name">{{ r.drug_a_cn }}</span>
          <span class="times">×</span>
          <span class="drug-name">{{ r.drug_b_cn }}</span>
        </div>
        <div class="severity" :style="{ color: config(r.severity).color }">
          {{ config(r.severity).icon }} {{ config(r.severity).label }}
        </div>
        <p class="desc">{{ r.description }}</p>
        <p class="advice" v-if="r.advice">💡 {{ r.advice }}</p>
      </div>
    </div>
    <div v-if="notFound.length" class="note">
      ⚠️ 未找到：{{ notFound.join('、') }}
    </div>
    <div v-if="notChecked.length" class="note safe">
      ⚪ 未发现已知交互：{{ notChecked.join('、') }}
    </div>
    <div v-if="data.duplicate_hint" class="note hint">{{ data.duplicate_hint }}</div>
  </div>
</template>

<style scoped>
.interaction-result { padding: 16px; }
.results { display: flex; flex-direction: column; gap: 12px; }
.result-item { border-bottom: 1px solid var(--border-glass); padding-bottom: 12px; }
.result-item:last-child { border-bottom: none; padding-bottom: 0; }
.pair { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.drug-name { font-weight: 600; }
.times { color: var(--text-secondary); }
.severity { font-weight: 600; margin-bottom: 4px; font-size: 14px; }
.desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; line-height: 1.5; }
.advice { font-size: 14px; margin-top: 4px; }
.note { font-size: 13px; padding: 8px; border-radius: 6px; margin-top: 8px; }
.note.safe { background: rgba(46, 213, 115, 0.08); color: var(--severity-mild); }
.note.hint { background: rgba(108, 92, 231, 0.08); color: var(--accent); font-size: 12px; }
</style>
