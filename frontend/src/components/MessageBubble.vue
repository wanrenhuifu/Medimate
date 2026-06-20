<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'
import DrugCard from './DrugCard.vue'
import InteractionResult from './InteractionResult.vue'
import SideEffectsChart from './SideEffectsChart.vue'
import EmergencyAlert from './EmergencyAlert.vue'

const props = defineProps({
  message: { type: Object, required: true },
  isLast: { type: Boolean, default: false },
})

const isUser = computed(() => props.message.role === 'user')
const isAssistant = computed(() => props.message.role === 'assistant')

const renderedContent = computed(() => {
  if (isUser.value || !props.message.content) return ''
  return renderMarkdown(props.message.content)
})

function componentForResult(toolResult) {
  const name = toolResult.name
  const result = toolResult.result
  if (!result) return null
  if (name === 'search_drug' && result.found) return { component: DrugCard, props: { drug: result.drug } }
  if (name === 'check_interaction') return { component: InteractionResult, props: { data: result } }
  if (name === 'query_side_effects' && result.success) return { component: SideEffectsChart, props: { data: result } }
  return null
}

// Check if this message contains emergency content
const isEmergency = computed(() => {
  return isAssistant.value && props.message.content?.includes('🚨')
})
</script>

<template>
  <div class="message-row" :class="{ user: isUser, assistant: isAssistant }">
    <div class="message-bubble" :class="{ user: isUser, glass: isAssistant, emergency: isEmergency }">
      <!-- Tool Results (Cards/Charts) -->
      <div v-if="message.toolResults?.length" class="tool-results">
        <template v-for="(tr, i) in message.toolResults" :key="i">
          <DrugCard v-if="tr.name === 'search_drug' && tr.result?.found" :drug="tr.result.drug" />
          <InteractionResult v-if="tr.name === 'check_interaction'" :data="tr.result" />
          <SideEffectsChart v-if="tr.name === 'query_side_effects' && tr.result?.success" :data="tr.result" />
        </template>
      </div>

      <!-- Markdown Content -->
      <div v-if="message.content" class="content" :class="{ raw: isUser }" v-html="isUser ? message.content : renderedContent"></div>

      <!-- Streaming cursor -->
      <span v-if="isLast && message.role === 'assistant' && !message.content" class="cursor">|</span>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex; max-width: 80%;
}
.message-row.user { align-self: flex-end; }
.message-row.assistant { align-self: flex-start; }

.message-bubble {
  padding: 12px 16px; border-radius: var(--radius);
  line-height: 1.6; word-break: break-word;
}
.message-bubble.user {
  background: var(--accent); color: #fff;
}
.message-bubble.assistant {
  background: var(--bg-secondary); border: 1px solid var(--border-glass);
}
.message-bubble.emergency {
  border-color: var(--severity-severe); background: rgba(255, 71, 87, 0.08);
}

.content :deep(p) { margin: 4px 0; }
.content :deep(code) { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-size: 14px; }
.content :deep(strong) { color: var(--text-primary); }
.content.raw { white-space: pre-wrap; }

.tool-results { display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; }

.cursor { animation: blink 1s infinite; color: var(--accent); }

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

@media (max-width: 768px) {
  .message-row { max-width: 95%; }
}
</style>
