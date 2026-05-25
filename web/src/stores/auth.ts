import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/api/auth'
import { login as apiLogin, refreshToken as apiRefreshToken, logout as apiLogout } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshTokenVal = ref(localStorage.getItem('refreshToken') || '')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)
  const currentTenantId = computed(() => user.value?.tenant_id ?? '')
  const currentTenantName = computed(() => user.value?.tenant_name ?? '')

  async function login(username: string, password: string) {
    const res = await apiLogin({ username, password })
    token.value = res.data.access_token
    refreshTokenVal.value = res.data.refresh_token
    user.value = res.data.user
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('refreshToken', res.data.refresh_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  async function refresh() {
    const res = await apiRefreshToken(refreshTokenVal.value)
    token.value = res.data.access_token
    refreshTokenVal.value = res.data.refresh_token
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('refreshToken', res.data.refresh_token)
  }

  function logout() {
    apiLogout().catch(() => {})
    token.value = ''
    refreshTokenVal.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  }

  function loadUser() {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        user.value = JSON.parse(stored)
      } catch {
        user.value = null
      }
    }
  }

  loadUser()

  return {
    token,
    refreshToken: refreshTokenVal,
    user,
    isLoggedIn,
    isSuperuser,
    currentTenantId,
    currentTenantName,
    login,
    refresh,
    logout,
    loadUser,
  }
})
