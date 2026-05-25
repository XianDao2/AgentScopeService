<template>
  <div class="chat-container">
    <el-container class="chat-layout">
      <el-aside width="280px" class="chat-sessions">
        <div class="sessions-header">
          <el-button type="primary" @click="createNewSession" style="width: 100%">
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
        </div>
        <el-scrollbar class="sessions-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSessionId === session.id }"
            @click="selectSession(session.id)"
          >
            <el-icon><ChatLineRound /></el-icon>
            <span class="session-title">{{ session.title || '新对话' }}</span>
          </div>
        </el-scrollbar>
      </el-aside>

      <el-main class="chat-main">
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <el-icon size="80" color="#ddd"><ChatDotRound /></el-icon>
            <p>开始一段新的对话吧</p>
          </div>

          <div v-else class="messages-list">
            <div v-for="(msg, index) in messages" :key="msg.id || index" class="message-item">
              <div class="message-avatar" :class="msg.role">
                <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                <el-icon v-else><Cpu /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-role">
                  {{ msg.role === 'user' ? '用户' : '智能助手' }}
                </div>
                <div class="message-text" v-html="formatMessage(msg.content)"></div>

                <div v-if="msg.thinking" class="thinking-block">
                  <div class="thinking-header">
                    <el-icon><Promotion /></el-icon>
                    <span>思考过程</span>
                  </div>
                  <div class="thinking-content">{{ msg.thinking }}</div>
                </div>

                <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-calls">
                  <div v-for="(tool, idx) in msg.toolCalls" :key="idx" class="tool-call-item">
                    <div class="tool-call-header">
                      <el-icon><Tools /></el-icon>
                      <span>调用工具：{{ tool.name }}</span>
                    </div>
                    <div v-if="tool.args" class="tool-call-args">
                      参数：{{ JSON.stringify(tool.args, null, 2) }}
                    </div>
                    <div v-if="tool.result" class="tool-call-result">
                      结果：{{ tool.result }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="isGenerating" class="message-item assistant">
              <div class="message-avatar">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-role">智能助手</div>
                <div class="message-text" v-html="formatMessage(currentContent)"></div>

                <div v-if="currentThinking" class="thinking-block">
                  <div class="thinking-header">
                    <el-icon><Promotion /></el-icon>
                    <span>思考过程</span>
                  </div>
                  <div class="thinking-content">{{ currentThinking }}</div>
                </div>

                <div v-if="currentToolCalls.length > 0" class="tool-calls">
                  <div v-for="(tool, idx) in currentToolCalls" :key="idx" class="tool-call-item">
                    <div class="tool-call-header">
                      <el-icon><Tools /></el-icon>
                      <span>调用工具：{{ tool.name }}</span>
                      <el-tag v-if="tool.status === 'calling'" type="warning" size="small">调用中</el-tag>
                      <el-tag v-else-if="tool.status === 'success'" type="success" size="small">成功</el-tag>
                      <el-tag v-else-if="tool.status === 'error'" type="danger" size="small">失败</el-tag>
                    </div>
                    <div v-if="tool.args" class="tool-call-args">
                      参数：{{ JSON.stringify(tool.args, null, 2) }}
                    </div>
                    <div v-if="tool.result" class="tool-call-result">
                      结果：{{ tool.result }}
                    </div>
                  </div>
                </div>

                <div v-if="modelCallInfo" class="model-call-info">
                  <div class="model-call-header">
                    <el-icon><Cpu /></el-icon>
                    <span>模型调用</span>
                    <el-tag type="info" size="small">{{ modelCallInfo.model }}</el-tag>
                  </div>
                  <div class="model-call-details">
                    <span>输入 tokens: {{ modelCallInfo.inputTokens || 0 }}</span>
                    <span>输出 tokens: {{ modelCallInfo.outputTokens || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <div class="input-box">
            <el-input
              v-model="inputContent"
              type="textarea"
              :rows="3"
              placeholder="输入消息..."
              @keydown.ctrl.enter="sendMessage"
              :disabled="isGenerating"
            />
            <div class="input-actions">
              <span class="hint">Ctrl + Enter 发送</span>
              <el-button
                type="primary"
                @click="sendMessage"
                :loading="isGenerating"
                :disabled="!inputContent.trim()"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, ChatLineRound, ChatDotRound, User, Cpu, Promotion, Tools } from '@element-plus/icons-vue'
import { getSessions, getMessages } from '@/api/chat'
import { useUserStore } from '@/store/user'
import { marked } from 'marked'

const userStore = useUserStore()
const messagesContainer = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const inputContent = ref('')
const isGenerating = ref(false)
const currentContent = ref('')
const currentThinking = ref('')
const currentToolCalls = ref([])
const currentToolResults = ref([])
const modelCallInfo = ref(null)

onMounted(() => {
  loadSessions()
})

async function loadSessions() {
  try {
    const res = await getSessions()
    sessions.value = res || []
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

async function selectSession(sessionId) {
  currentSessionId.value = sessionId
  try {
    const res = await getMessages(sessionId)
    messages.value = res || []
    scrollToBottom()
  } catch (error) {
    console.error('Failed to load messages:', error)
  }
}

function createNewSession() {
  currentSessionId.value = null
  messages.value = []
  currentContent.value = ''
  currentThinking.value = ''
  currentToolCalls.value = []
  currentToolResults.value = []
  modelCallInfo.value = null
  inputContent.value = ''
}

function formatMessage(text) {
  if (!text) return ''
  return marked(text)
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function sendMessage() {
  if (!inputContent.value.trim() || isGenerating.value) return

  const content = inputContent.value
  inputContent.value = ''
  isGenerating.value = true
  currentContent.value = ''
  currentThinking.value = ''
  currentToolCalls.value = []
  currentToolResults.value = []
  modelCallInfo.value = null

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: content
  })

  scrollToBottom()

  try {
    const token = userStore.token
    const response = await fetch('/api/v2/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: content,
        session_id: currentSessionId.value,
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error('Request failed')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          try {
            const data = JSON.parse(dataStr)
            handleSSEEvent(data)
          } catch (e) {
            continue
          }
        }
      }
      scrollToBottom()
    }

    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: currentContent.value,
      thinking: currentThinking.value,
      toolCalls: currentToolCalls.value,
      modelCallInfo: modelCallInfo.value
    })

    await loadSessions()
  } catch (error) {
    console.error('Failed to send message:', error)
    ElMessage.error('发送消息失败')
  } finally {
    isGenerating.value = false
    currentContent.value = ''
    currentThinking.value = ''
    currentToolCalls.value = []
    currentToolResults.value = []
    modelCallInfo.value = null
    scrollToBottom()
  }
}

function handleSSEEvent(event) {
  switch (event.type) {
    case 'reply_start':
      currentContent.value = ''
      currentThinking.value = ''
      currentToolCalls.value = []
      currentToolResults.value = []
      modelCallInfo.value = null
      break

    case 'text_delta':
    case 'text_block_delta':
      currentContent.value += event.content || event.delta || ''
      break

    case 'text_block_start':
    case 'text_block_end':
      break

    case 'thinking_delta':
    case 'thinking_block_delta':
      currentThinking.value += event.content || event.delta || ''
      break

    case 'thinking_block_start':
    case 'thinking_block_end':
      break

    case 'tool_call_start':
      currentToolCalls.value.push({
        id: event.tool_call_id,
        name: event.tool_call_name,
        status: 'calling',
        args: null
      })
      break

    case 'tool_call_delta':
      const idx = currentToolCalls.value.findIndex(t => t.id === event.tool_call_id)
      if (idx >= 0) {
        if (event.delta) {
          const oldArgs = currentToolCalls.value[idx].args || ''
          currentToolCalls.value[idx].args = oldArgs + event.delta
        }
      }
      break

    case 'tool_call_end':
      const endIdx = currentToolCalls.value.findIndex(t => t.id === event.tool_call_id)
      if (endIdx >= 0) {
        currentToolCalls.value[endIdx].status = 'called'
      }
      break

    case 'tool_result_start':
      const resStartIdx = currentToolCalls.value.findIndex(t => t.id === event.tool_call_id)
      if (resStartIdx >= 0) {
        currentToolCalls.value[resStartIdx].status = 'calling'
      }
      break

    case 'tool_result_text_delta':
      const resDeltaIdx = currentToolCalls.value.findIndex(t => t.id === event.tool_call_id)
      if (resDeltaIdx >= 0) {
        const oldResult = currentToolCalls.value[resDeltaIdx].result || ''
        currentToolCalls.value[resDeltaIdx].result = oldResult + event.delta
      }
      break

    case 'tool_result_end':
      const resEndIdx = currentToolCalls.value.findIndex(t => t.id === event.tool_call_id)
      if (resEndIdx >= 0) {
        currentToolCalls.value[resEndIdx].status = 'success'
      }
      break

    case 'model_call_start':
      modelCallInfo.value = {
        model: event.model_name || 'unknown',
        inputTokens: 0,
        outputTokens: 0
      }
      break

    case 'model_call_end':
      if (modelCallInfo.value) {
        modelCallInfo.value.inputTokens = event.input_tokens || 0
        modelCallInfo.value.outputTokens = event.output_tokens || 0
      }
      break

    case 'exceed_max_iters':
      ElMessage.warning('已达到最大推理迭代次数')
      break

    case 'require_user_confirm':
      ElMessage.info('需要用户确认工具调用')
      break

    case 'require_external_execution':
      ElMessage.info('需要外部执行工具')
      break

    case 'reply_end':
      break
  }
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
}

.chat-layout {
  height: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.chat-sessions {
  background: #f5f7fa;
  border-right: 1px solid #e6e6e6;
}

.sessions-header {
  padding: 16px;
  border-bottom: 1px solid #e6e6e6;
}

.sessions-list {
  height: calc(100% - 70px);
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: #e6e6e6;
}

.session-item.active {
  background: #409EFF;
  color: #fff;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.empty-state p {
  margin-top: 16px;
}

.messages-list {
  max-width: 900px;
  margin: 0 auto;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.message-avatar.user {
  background: #67C23A;
}

.message-content {
  flex: 1;
}

.message-role {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.message-text {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
}

.message-text :deep(p) {
  margin: 8px 0;
}

.message-text :deep(code) {
  background: #e6e6e6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message-text :deep(pre) {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.thinking-block {
  margin-top: 12px;
  background: #fff9e6;
  border: 1px solid #e6a23c;
  border-radius: 8px;
  padding: 12px;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #e6a23c;
  font-weight: 500;
  margin-bottom: 8px;
}

.thinking-content {
  color: #666;
  font-size: 14px;
}

.tool-calls {
  margin-top: 12px;
}

.tool-call-item {
  background: #f0f9ff;
  border: 1px solid #91d5ff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #1890ff;
  font-weight: 500;
  margin-bottom: 8px;
}

.tool-call-args,
.tool-call-result {
  color: #666;
  font-size: 13px;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  margin-top: 4px;
  white-space: pre-wrap;
}

.model-call-info {
  margin-top: 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 12px;
}

.model-call-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #52c41a;
  font-weight: 500;
  margin-bottom: 8px;
}

.model-call-details {
  display: flex;
  gap: 24px;
  color: #666;
  font-size: 13px;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e6e6e6;
  background: #fafafa;
}

.input-box {
  max-width: 900px;
  margin: 0 auto;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.hint {
  color: #999;
  font-size: 12px;
}
</style>
