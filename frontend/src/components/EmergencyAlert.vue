<script setup>
// Emergency alert is handled within MessageBubble when it detects 🚨 in content.
// This component is for standalone emergency alerts.
defineProps({
  message: { type: String, default: '' }
})
</script>

<template>
  <div class="emergency-alert">
    <div class="emergency-icon">🚨</div>
    <div class="emergency-content">
      <strong>紧急提醒</strong>
      <p>{{ message || '您描述的症状可能需要立即就医。请不要依赖任何在线工具，立即就医。' }}</p>
      <div class="emergency-actions">
        <span>📞 急救电话：120</span>
        <span>🏥 请前往最近的医院急诊科</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.emergency-alert {
  display: flex; gap: 12px; padding: 16px; margin: 8px 0;
  background: rgba(255, 71, 87, 0.1); border: 2px solid var(--severity-severe);
  border-radius: var(--radius);
}
.emergency-icon { font-size: 32px; }
.emergency-content strong { display: block; color: var(--severity-severe); margin-bottom: 8px; font-size: 16px; }
.emergency-content p { font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.6; }
.emergency-actions { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
</style>
