<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const reactions = computed(() => props.data.reactions || [])
const maxCount = computed(() => Math.max(...reactions.value.map(r => r.count), 1))
</script>

<template>
  <div class="side-effects glass">
    <div class="chart-header">
      <span>📊 {{ data.drug_name_cn }} — FDA 不良反应数据</span>
      <span class="total">总报告数：{{ data.total_reports?.toLocaleString() || 'N/A' }}</span>
    </div>
    <div class="chart">
      <div v-for="r in reactions" :key="r.term_en" class="bar-row">
        <span class="bar-label">{{ r.term_cn }}</span>
        <div class="bar-track">
          <div
            class="bar-fill"
            :style="{ width: (r.count / maxCount * 100) + '%' }"
          ></div>
        </div>
        <span class="bar-count">{{ r.count?.toLocaleString() }}</span>
      </div>
    </div>
    <div class="chart-footer">
      📌 数据来源：FDA FAERS &nbsp;|&nbsp; ⚠️ 报告数量 ≠ 发生概率，不代表因果关系
    </div>
  </div>
</template>

<style scoped>
.side-effects { padding: 16px; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 4px; }
.chart-header .total { font-size: 12px; color: var(--text-secondary); }
.chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 100px; font-size: 13px; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 18px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.5s ease; min-width: 2px; }
.bar-count { width: 60px; font-size: 12px; color: var(--text-secondary); text-align: right; }
.chart-footer { margin-top: 12px; font-size: 11px; color: var(--text-secondary); text-align: center; }
</style>
