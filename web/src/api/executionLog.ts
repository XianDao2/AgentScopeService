import http from './index'

export interface ExecutionLog {
  id: string
  session_id: string
  agent_id: string
  agent_name: string
  user_id: string
  event_type: string
  input_tokens: number
  output_tokens: number
  duration_ms: number
  status: string
  error_message: string
  created_at: string
}

export function getExecutionLogs(params?: {
  page?: number
  page_size?: number
  agent_id?: string
  session_id?: string
  status?: string
  start_date?: string
  end_date?: string
}) {
  return http.get<{ items: ExecutionLog[]; total: number }>('/execution-logs', { params })
}

export function getExecutionLog(id: string) {
  return http.get<ExecutionLog>(`/execution-logs/${id}`)
}

export function getExecutionStats(params?: { agent_id?: string; start_date?: string; end_date?: string }) {
  return http.get<{
    total_calls: number
    total_input_tokens: number
    total_output_tokens: number
    avg_duration_ms: number
    success_rate: number
  }>('/execution-logs/stats', { params })
}
