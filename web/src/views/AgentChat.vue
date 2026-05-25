<template>
  <div class="agent-chat">
    <el-row :gutter="16" style="height: calc(100vh - 120px)">
      <el-col :span="5">
        <el-card class="session-panel" style="height: 100%">
          <template #header>
            <div class="session-header">
              <span>会话列表</span>
              <el-button type="primary" size="small" @click="handleNewSession">新建</el-button>
            </div>
          </template>
          <div class="session-list">
            <div
              v-for="s in sessions"
              :key="s.id"
              class="session-item"
              :class="{ active: s.id === currentSessionId }"
              @click="selectSession(s.id)"
            >
              <div class="session-title">{{ s.title || '新会话' }}</div>
              <div class="session-time">{{ formatDate(s.created_at) }}</div>
              <el-button
                class="session-delete"
                link
                type="danger"
                size="small"
                @click.stop="handleDeleteSession(s.id)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-empty v-if="!sessions.length" description="暂无会话" :image-size="60" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="19">
        <el-card class="chat-panel" style="height: 100%; display: flex; flex-direction: column">
          <template #header>
            <div class="chat-header">
              <span>{{ agentName }}</span>
              <el-tag v-if="isStreaming" type="warning" size="small" effect="dark">流式输出中</el-tag>
            </div>
          </template>
          <div class="chat-messages" ref="messagesRef">
            <div v-for="msg in sortedMessages" :key="msg.id" class="message-item" :class="msg.role">
              <div class="message-avatar">
                <el-avatar :size="32" :style="{ background: msg.role === 'user' ? '#409eff' : '#67c23a' }">
                  {{ msg.role === 'user' ? 'U' : 'A' }}
                </el-avatar>
              </div>
              <div class="message-body">
                <ThinkingBlock v-if="msg.thinking" :content="msg.thinking" />
                <ToolCallBlock
                  v-for="tc in msg.toolCalls"
                  :key="tc.id"
                  :name="tc.name"
                  :arguments="tc.arguments"
                  :result="tc.result"
                  :status="tc.status"
                />
                <div class="message-content" v-if="msg.content">
                  <div v-html="renderMarkdown(msg.content)"></div>
                  <span v-if="msg.status === 'streaming'" class="cursor-blink">▌</span>
                </div>
              </div>
            </div>
            <el-empty v-if="!messages.length" description="开始对话吧" :image-size="80" />
          </div>
          <div class="chat-input">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入消息..."
              resize="none"
              @keydown.enter.exact.prevent="handleSend"
            />
            <div class="input-actions">
              <el-button
                v-if="isStreaming"
                type="danger"
                @click="stopStreaming"
              >
                停止
              </el-button>
              <el-button
                type="primary"
                :disabled="!inputText.trim() || isStreaming"
                @click="handleSend"
              >
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChat } from '@/composables/useChat'
import { getAgent } from '@/api/agent'
import ThinkingBlock from '@/components/ThinkingBlock.vue'
import ToolCallBlock from '@/components/ToolCallBlock.vue'
import { Delete } from '@element-plus/icons-vue'

const route = useRoute()
const agentId = route.params.id as string
const agentName = ref('Agent')
const inputText = ref('')
const messagesRef = ref<HTMLElement>()

const {
  messages,
  sortedMessages,
  sessions,
  currentSessionId,
  isStreaming,
  loadSessions,
  startSession,
  removeSession,
  sendMessage,
  stopStreaming,
  clearChat,
} = useChat()

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

function renderMarkdown(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return
  inputText.value = ''
  await sendMessage(text, agentId)
  scrollToBottom()
}

async function handleNewSession() {
  await startSession(agentId, '新会话')
}

function selectSession(sessionId: string) {
  currentSessionId.value = sessionId
  clearChat()
}

async function handleDeleteSession(sessionId: string) {
  await removeSession(sessionId)
}

watch(() => messages.value.length, () => {
  scrollToBottom()
})

onMounted(async () => {
  try {
    const res = await getAgent(agentId)
    agentName.value = res.data.name
  } catch {}
  await loadSessions(agentId)
})
</script>

<style scoped>
.session-panel :deep(.el-card__body) {
  padding: 0;
  overflow-y: auto;
  flex: 1;
}
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.session-list {
  padding: 8px;
}
.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}
.session-item:hover {
  background: #f5f7fa;
}
.session-item.active {
  background: #ecf5ff;
}
.session-title {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-left: 8px;
  white-space: nowrap;
}
.session-delete {
  margin-left: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.session-item:hover .session-delete {
  opacity: 1;
}
.chat-panel :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message-item.user {
  flex-direction: row-reverse;
}
.message-avatar {
  flex-shrink: 0;
}
.message-body {
  max-width: 70%;
  min-width: 0;
}
.message-item.user .message-body {
  text-align: right;
}
.message-content {
  display: inline-block;
  text-align: left;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.message-item.user .message-content {
  background: #409eff;
  color: #fff;
}
.message-item.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
}
.message-item.assistant .message-content :deep(code) {
  background: #e4e7ed;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.cursor-blink {
  animation: blink 1s infinite;
  color: #409eff;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.chat-input :deep(.el-textarea) {
  flex: 1;
}
.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
