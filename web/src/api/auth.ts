import http from './index'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfo
}

export interface UserInfo {
  id: string
  username: string
  email: string
  tenant_id: string
  tenant_name: string
  roles: string[]
  is_superuser: boolean
}

export function login(data: LoginParams) {
  return http.post<LoginResult>('/users/login', data)
}

export function logout() {
  return http.post('/users/logout')
}

export function refreshToken(refresh_token: string) {
  return http.post<{ access_token: string; refresh_token: string }>('/users/refresh', {
    refresh_token,
  })
}

export function getCurrentUser() {
  return http.get<UserInfo>('/users/me')
}
