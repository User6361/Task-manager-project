import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../views/AppLayout.vue'),
    children: [
      { path: '', redirect: '/board' },
      { path: 'board', component: () => import('../views/BoardView.vue') },
      { path: 'tasks', component: () => import('../views/TasksView.vue') },
      { path: 'tasks/:id', component: () => import('../views/TaskDetailView.vue') },
      { path: 'projects', component: () => import('../views/ProjectsView.vue') },
      { path: 'reports', component: () => import('../views/ReportsView.vue'), meta: { managerOnly: true } },
      { path: 'users', component: () => import('../views/UsersView.vue'), meta: { adminOnly: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Если есть токен но нет user — попробуем загрузить
  if (auth.token && !auth.user) {
    try {
      await auth.fetchMe()
    } catch (e) {
      auth.logout()
    }
  }

  if (!to.meta.public && !auth.isAuthenticated) {
    return { path: '/login' }
  }

  if (to.meta.managerOnly && !auth.isManager) {
    return { path: '/board' }
  }
  if (to.meta.adminOnly && !auth.isAdmin) {
    return { path: '/board' }
  }
})

export default router
