<script setup>
import { ref } from 'vue'
import ChatArea from './components/ChatArea.vue'
import MedList from './components/MedList.vue'
import ChatInput from './components/ChatInput.vue'
import QuickActions from './components/QuickActions.vue'
import { useChatStore } from './stores/chat'

const store = useChatStore()
const showSidebar = ref(true)
const disclaimerAccepted = ref(localStorage.getItem('medimate_disclaimer') === '1')

function acceptDisclaimer() {
  localStorage.setItem('medimate_disclaimer', '1')
  disclaimerAccepted.value = true
}
</script>

<template>
  <!-- Disclaimer Modal -->
  <div v-if="!disclaimerAccepted" class="disclaimer-overlay">
    <div class="disclaimer-modal glass">
      <h2>⚕️ 使用须知</h2>
      <p>MediMate 是一款 AI 用药信息查询工具。</p>
      <p>在使用前，请了解：</p>
      <ol>
        <li>本工具提供的信息仅供参考，不构成任何医疗建议、诊断或处方</li>
        <li>药物使用请严格遵循医生处方和药品说明书</li>
        <li>如出现任何不适症状，请立即就医</li>
        <li>本工具不收集任何个人身份信息</li>
      </ol>
      <button class="btn-accept" @click="acceptDisclaimer">我已了解，开始使用</button>
    </div>
  </div>

  <!-- Main Layout -->
  <div class="app-layout">
    <aside class="sidebar glass" :class="{ collapsed: !showSidebar }">
      <div class="sidebar-header">
        <h1>💊 MediMate</h1>
        <button class="btn-toggle" @click="showSidebar = !showSidebar">
          {{ showSidebar ? '✕' : '☰' }}
        </button>
      </div>
      <MedList />
    </aside>

    <main class="chat-main">
      <ChatArea />
      <QuickActions />
      <ChatInput />
    </main>
  </div>

  <footer class="disclaimer-footer">
    ⚕️ 本工具仅供健康参考，不构成医疗建议。用药请遵医嘱。
  </footer>
</template>

<style scoped>
.disclaimer-overlay {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.7);
}
.disclaimer-modal {
  max-width: 480px; padding: 32px; text-align: left;
}
.disclaimer-modal h2 { margin-bottom: 16px; color: var(--accent); }
.disclaimer-modal p, .disclaimer-modal ol { margin-bottom: 12px; color: var(--text-secondary); line-height: 1.6; }
.disclaimer-modal ol { padding-left: 20px; }
.disclaimer-modal ol li { margin-bottom: 8px; }
.btn-accept {
  margin-top: 16px; padding: 12px 24px; background: var(--accent);
  color: #fff; border: none; border-radius: 8px; cursor: pointer;
  font-size: 16px; width: 100%;
}
.btn-accept:hover { background: var(--accent-hover); }

.app-layout { display: flex; height: calc(100vh - 36px); }

.sidebar {
  width: 300px; min-width: 300px; border-radius: 0;
  display: flex; flex-direction: column; transition: all 0.3s;
  border-right: 1px solid var(--border-glass);
}
.sidebar.collapsed { min-width: 0; width: 48px; }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; padding: 16px; }
.sidebar-header h1 { font-size: 20px; }
.btn-toggle { background: none; border: none; color: var(--text-secondary); font-size: 18px; cursor: pointer; }

.chat-main {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0;
}

.disclaimer-footer {
  text-align: center; padding: 8px; font-size: 12px;
  color: var(--text-secondary); border-top: 1px solid var(--border-glass);
}

@media (max-width: 768px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 36px; z-index: 100; }
  .sidebar.collapsed { transform: translateX(-300px); min-width: 300px; }
  .chat-main { width: 100%; }
}
</style>
