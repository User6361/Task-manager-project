import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)

  const isAuthenticated = computed(() => !!token.value)
  const role = computed(() => user.value?.role?.code)

  const isManager = computed(() => ['manager', 'admin'].includes(role.value))
  const isAdmin = computed(() => role.value === 'admin')

  async function login(loginVal, password) {
    const { data } = await api.post('/auth/login', { login: loginVal, password })
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    await fetchMe()
  }

  async function fetchMe() {
    if (!token.value) return
    const { data } = await api.get('/auth/me')
    user.value = data
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  return {
    user, token, isAuthenticated, role, isManager, isAdmin,
    login, fetchMe, logout,
  }
})
