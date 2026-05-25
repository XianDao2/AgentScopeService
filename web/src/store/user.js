import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password, tenantId) {
    const res = await loginApi({ username, password, tenant_id: tenantId })
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    userInfo.value = res.user
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('refreshToken', res.refresh_token)
    localStorage.setItem('userInfo', JSON.stringify(res.user))
    return res
  }

  async function fetchUserInfo() {
    const res = await getCurrentUser()
    userInfo.value = res
    localStorage.setItem('userInfo', JSON.stringify(res))
    return res
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('userInfo')
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    login,
    fetchUserInfo,
    logout
  }
})
