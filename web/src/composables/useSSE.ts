import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export interface AgentEvent {
  event_id: string
  event_type: string
  data: any
  timestamp: string
}

export function useSSE() {
  const events = ref<AgentEvent[]>([])
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  const lastEventId = ref<string>('')
  let abortController: AbortController | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  async function connect(url: string, body: Record<string, any>) {
    disconnect()
    abortController = new AbortController()
    isConnected.value = true
    error.value = null

    const authStore = useAuthStore()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    }
    if (lastEventId.value) {
      headers['Last-Event-ID'] = lastEventId.value
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No readable stream')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent: Partial<AgentEvent> = {}

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent.event_type = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              currentEvent.data = JSON.parse(line.slice(6))
            } catch {
              currentEvent.data = line.slice(6)
            }
          } else if (line.startsWith('id: ')) {
            currentEvent.event_id = line.slice(4).trim()
            lastEventId.value = currentEvent.event_id
          } else if (line === '') {
            if (currentEvent.event_type) {
              const event: AgentEvent = {
                event_id: currentEvent.event_id || '',
                event_type: currentEvent.event_type,
                data: currentEvent.data,
                timestamp: new Date().toISOString(),
              }
              events.value.push(event)
            }
            currentEvent = {}
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        error.value = e.message
        scheduleReconnect(url, body)
      }
    } finally {
      isConnected.value = false
    }
  }

  function scheduleReconnect(url: string, body: Record<string, any>) {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      connect(url, body)
    }, 3000)
  }

  function disconnect() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    isConnected.value = false
  }

  function clearEvents() {
    events.value = []
    lastEventId.value = ''
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    events,
    isConnected,
    error,
    lastEventId,
    connect,
    disconnect,
    clearEvents,
  }
}
