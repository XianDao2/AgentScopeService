import { ref, computed } from 'vue'
import { useSSE, type AgentEvent } from './useSSE'
import { getSessions, createSession, deleteSession, type AgentSession } from '@/api/agent'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
  toolCalls?: ToolCallInfo[]
  status: 'pending' | 'streaming' | 'completed' | 'failed'
  createdAt: string
}

export interface ToolCallInfo {
  id: string
  name: string
  arguments: string
  result?: string
  status: 'calling' | 'completed' | 'failed'
}

export function useChat() {
  const { events, isConnected, connect, disconnect, clearEvents } = useSSE()
  const messages = ref<ChatMessage[]>([])
  const sessions = ref<AgentSession[]>([])
  const currentSessionId = ref<string>('')
  const isStreaming = ref(false)

  const sortedMessages = computed(() =>
    [...messages.value].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()),
  )

  async function loadSessions(agentId?: string) {
    const res = await getSessions({ agent_id: agentId })
    sessions.value = res.data.items
  }

  async function startSession(agentId: string, title?: string) {
    const res = await createSession({ agent_id: agentId, title })
    sessions.value.unshift(res.data)
    currentSessionId.value = res.data.id
    messages.value = []
    return res.data
  }

  async function removeSession(id: string) {
    await deleteSession(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = ''
      messages.value = []
    }
  }

  async function sendMessage(content: string, agentId: string) {
    if (!currentSessionId.value) {
      const session = await startSession(agentId, content.slice(0, 50))
      currentSessionId.value = session.id
    }

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      status: 'completed',
      createdAt: new Date().toISOString(),
    }
    messages.value.push(userMsg)

    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      thinking: '',
      toolCalls: [],
      status: 'streaming',
      createdAt: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)
    isStreaming.value = true

    clearEvents()

    await connect('/chat', {
      session_id: currentSessionId.value,
      agent_id: agentId,
      message: content,
    })

    processEvents(assistantMsg.id)
  }

  function processEvents(assistantMsgId: string) {
    const unwatch = watch(
      () => events.value.length,
      () => {
        const msg = messages.value.find((m) => m.id === assistantMsgId)
        if (!msg) return

        for (const event of events.value) {
          switch (event.event_type) {
            case 'text_delta':
              msg.content += event.data?.delta || event.data?.text || ''
              break
            case 'thinking_delta':
              msg.thinking = (msg.thinking || '') + (event.data?.delta || event.data?.text || '')
              break
            case 'tool_call_start': {
              const toolCall: ToolCallInfo = {
                id: event.data?.id || `tool-${Date.now()}`,
                name: event.data?.name || '',
                arguments: '',
                status: 'calling',
              }
              msg.toolCalls = msg.toolCalls || []
              msg.toolCalls.push(toolCall)
              break
            }
            case 'tool_call_delta': {
              const tc = msg.toolCalls?.find((t) => t.id === event.data?.id)
              if (tc) {
                tc.arguments += event.data?.delta || ''
              }
              break
            }
            case 'tool_call_end': {
              const tcEnd = msg.toolCalls?.find((t) => t.id === event.data?.id)
              if (tcEnd) {
                tcEnd.status = 'completed'
                tcEnd.result = event.data?.result
              }
              break
            }
            case 'tool_call_error': {
              const tcErr = msg.toolCalls?.find((t) => t.id === event.data?.id)
              if (tcErr) {
                tcErr.status = 'failed'
              }
              break
            }
            case 'message_end':
              msg.status = 'completed'
              isStreaming.value = false
              unwatch()
              break
            case 'error':
              msg.status = 'failed'
              msg.content += `\n\n错误: ${event.data?.message || '未知错误'}`
              isStreaming.value = false
              unwatch()
              break
          }
        }
      },
    )
  }

  function watch(source: () => number, callback: () => void) {
    const wrapped = () => {
      callback()
    }
    const interval = setInterval(() => {
      wrapped()
    }, 100)
    return () => clearInterval(interval)
  }

  function stopStreaming() {
    disconnect()
    const streamingMsg = messages.value.find((m) => m.status === 'streaming')
    if (streamingMsg) {
      streamingMsg.status = 'completed'
    }
    isStreaming.value = false
  }

  function clearChat() {
    messages.value = []
    clearEvents()
  }

  return {
    messages,
    sortedMessages,
    sessions,
    currentSessionId,
    isStreaming,
    isConnected,
    events,
    loadSessions,
    startSession,
    removeSession,
    sendMessage,
    stopStreaming,
    clearChat,
  }
}
