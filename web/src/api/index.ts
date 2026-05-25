import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'

const http = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

http.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore()
    if (error.response?.status === 401) {
      if (authStore.refreshToken) {
        try {
          await authStore.refresh()
          return http(error.config)
        } catch {
          authStore.logout()
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
        }
      } else {
        authStore.logout()
        router.push('/login')
        ElMessage.error('请先登录')
      }
    }
    return Promise.reject(error)
  },
)

export default http
