import request from '@/utils/request'

export function getSessions() {
  return request({
    url: '/chat/sessions',
    method: 'get'
  })
}

export function createSession(data) {
  return request({
    url: '/chat/sessions',
    method: 'post',
    params: data
  })
}

export function getMessages(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}/messages`,
    method: 'get'
  })
}

export function sendMessage(data) {
  return request({
    url: '/chat/',
    method: 'post',
    data
  })
}
