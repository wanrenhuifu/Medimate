<script setup>
defineProps({
  drug: { type: Object, required: true }
})
</script>

<template>
  <div class="drug-card glass">
    <div class="card-header">
      <span class="emoji">💊</span>
      <div>
        <h3>{{ drug.name_cn }}</h3>
        <span class="en-name">{{ drug.name_en }}</span>
      </div>
    </div>
    <div class="card-body">
      <div class="field" v-if="drug.category">
        <span class="label">📂 分类</span>
        <span>{{ drug.category }}</span>
      </div>
      <div class="field" v-if="drug.indications?.length">
        <span class="label">🎯 用途</span>
        <span>{{ drug.indications.join(' · ') }}</span>
      </div>
      <div class="field" v-if="drug.dosage_adult">
        <span class="label">💉 常用剂量</span>
        <span>{{ drug.dosage_adult }}</span>
        <span v-if="drug.dosage_max" class="sub">最大：{{ drug.dosage_max }}</span>
        <span v-if="drug.dosage_route" class="sub">途径：{{ drug.dosage_route }}</span>
        <span v-if="drug.dosage_timing" class="sub">服用时间：{{ drug.dosage_timing }}</span>
      </div>
      <div class="field" v-if="drug.precautions?.length">
        <span class="label">⚠️ 注意事项</span>
        <ul><li v-for="p in drug.precautions" :key="p">{{ p }}</li></ul>
      </div>
      <div class="field" v-if="drug.contraindications?.length">
        <span class="label">🚫 禁忌</span>
        <ul><li v-for="c in drug.contraindications" :key="c">{{ c }}</li></ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drug-card { padding: 16px; }
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.card-header .emoji { font-size: 28px; }
.card-header h3 { font-size: 18px; }
.en-name { font-size: 13px; color: var(--text-secondary); }
.card-body { display: flex; flex-direction: column; gap: 8px; }
.field { display: flex; flex-direction: column; gap: 2px; }
.label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.sub { font-size: 12px; color: var(--text-secondary); padding-left: 8px; }
ul { padding-left: 16px; margin: 2px 0; font-size: 14px; }
li { margin-bottom: 2px; }
</style>
