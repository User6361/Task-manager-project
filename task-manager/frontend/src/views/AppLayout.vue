<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const unreadCount = ref(0)
const showNotifications = ref(false)
const notifications = ref([])

const navItems = computed(() => {
  const items = [
    { path: '/board', label: 'Канбан-доска', icon: '◫' },
    { path: '/tasks', label: 'Задачи', icon: '☰' },
    { path: '/projects', label: 'Проекты', icon: '◇' },
  ]
  if (auth.isManager) {
    items.push({ path: '/reports', label: 'Отчёты', icon: '⊞' })
  }
  if (auth.isAdmin) {
    items.push({ path: '/users', label: 'Пользователи', icon: '◉' })
  }
  return items
})

async function loadNotifications() {
  try {
    const { data } = await api.get('/notifications/?only_unread=true')
    notifications.value = data
    unreadCount.value = data.length
  } catch (e) {
    // тихо игнорируем
  }
}

async function markRead(id) {
  await api.post(`/notifications/${id}/read`)
  await loadNotifications()
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(loadNotifications)
</script>

<template>
  <div class="layout">
    <!-- Боковое меню -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">МЗ</div>
        <span class="brand-text">Менеджер задач</span>
      </div>

      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path.startsWith(item.path) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <div class="user-card">
          <div class="user-avatar">
            {{ auth.user?.full_name?.charAt(0) || '?' }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ auth.user?.full_name }}</div>
            <div class="user-role muted">{{ auth.user?.role?.name }}</div>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm logout-btn" @click="logout">
          Выйти
        </button>
      </div>
    </aside>

    <!-- Основной контент -->
    <main class="main">
      <header class="topbar">
        <div class="topbar-spacer"></div>
        <button
          class="notif-btn"
          @click="showNotifications = !showNotifications"
          :title="`Уведомлений: ${unreadCount}`"
        >
          <span class="notif-icon">⊜</span>
          <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount }}</span>
        </button>
      </header>

      <!-- Выпадающий список уведомлений -->
      <div v-if="showNotifications" class="notif-dropdown">
        <div class="notif-header">
          <strong>Уведомления</strong>
          <button class="btn-close" @click="showNotifications = false">×</button>
        </div>
        <div v-if="notifications.length === 0" class="notif-empty muted">
          Новых уведомлений нет
        </div>
        <div v-else class="notif-list">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="notif-item"
          >
            <div class="notif-message">{{ n.message }}</div>
            <div class="notif-meta">
              <span class="muted text-xs">
                {{ new Date(n.created_at).toLocaleString('ru-RU') }}
              </span>
              <button class="link" @click="markRead(n.id)">Прочитано</button>
            </div>
          </div>
        </div>
      </div>

      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 240px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--color-primary);
  color: white;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  font-weight: 600;
  font-size: 15px;
}

.nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius);
  color: var(--color-text);
  text-decoration: none;
  font-size: 14px;
  transition: background 0.15s;
}

.nav-item:hover {
  background: var(--color-bg);
  text-decoration: none;
}

.nav-item.active {
  background: #eff6ff;
  color: var(--color-primary);
  font-weight: 500;
}

.nav-icon {
  width: 20px;
  text-align: center;
  font-size: 16px;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--color-border);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  margin-bottom: 8px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
}

.logout-btn {
  width: 100%;
  justify-content: center;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.topbar {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.topbar-spacer {
  flex: 1;
}

.notif-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: background 0.15s;
}

.notif-btn:hover {
  background: var(--color-bg);
}

.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 700;
  border-radius: 999px;
  padding: 1px 5px;
  min-width: 16px;
  text-align: center;
}

.notif-dropdown {
  position: absolute;
  top: 60px;
  right: 24px;
  width: 360px;
  max-height: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  overflow: hidden;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.btn-close {
  font-size: 22px;
  line-height: 1;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--color-text-muted);
}

.btn-close:hover {
  background: var(--color-bg);
}

.notif-empty {
  padding: 20px;
  text-align: center;
}

.notif-list {
  max-height: 340px;
  overflow-y: auto;
}

.notif-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.notif-item:last-child {
  border-bottom: none;
}

.notif-message {
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 6px;
}

.notif-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.link {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
