import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: 'tenants',
          name: 'TenantManagement',
          component: () => import('@/views/TenantManagement.vue'),
          meta: { requiresSuperuser: true },
        },
        {
          path: 'users',
          name: 'UserManagement',
          component: () => import('@/views/UserManagement.vue'),
        },
        {
          path: 'roles',
          name: 'RoleManagement',
          component: () => import('@/views/RoleManagement.vue'),
        },
        {
          path: 'models',
          name: 'ModelManagement',
          component: () => import('@/views/ModelManagement.vue'),
        },
        {
          path: 'tool-groups',
          name: 'ToolGroupManagement',
          component: () => import('@/views/ToolGroupManagement.vue'),
        },
        {
          path: 'agents',
          name: 'AgentManagement',
          component: () => import('@/views/AgentManagement.vue'),
        },
        {
          path: 'agents/:id/chat',
          name: 'AgentChat',
          component: () => import('@/views/AgentChat.vue'),
        },
        {
          path: 'knowledge',
          name: 'KnowledgeBase',
          component: () => import('@/views/KnowledgeBase.vue'),
        },
        {
          path: 'knowledge/:id/documents',
          name: 'KnowledgeDocument',
          component: () => import('@/views/KnowledgeDocument.vue'),
        },
        {
          path: 'execution-logs',
          name: 'ExecutionLog',
          component: () => import('@/views/ExecutionLog.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresSuperuser && !authStore.isSuperuser) {
    next({ name: 'Dashboard' })
    return
  }

  if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
