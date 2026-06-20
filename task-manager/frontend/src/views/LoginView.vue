<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const login = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(login.value, password.value)
    router.push('/board')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}

function fillDemo(l, p) {
  login.value = l
  password.value = p
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <div class="brand-logo">МЗ</div>
        <h1 class="brand-name">Менеджер задач</h1>
        <p class="brand-tagline muted">Информационная система управления задачами проектного подразделения</p>
      </div>

      <form @submit.prevent="submit">
        <div class="field">
          <label class="label">Логин</label>
          <input v-model="login" class="input" required autofocus placeholder="например, manager" />
        </div>

        <div class="field">
          <label class="label">Пароль</label>
          <input v-model="password" type="password" class="input" required />
        </div>

        <div v-if="error" class="error mb-3">{{ error }}</div>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти в систему' }}
        </button>
      </form>

      <div class="demo-block">
        <div class="demo-title muted text-xs">Демонстрационные учётные записи:</div>
        <div class="demo-list">
          <button type="button" class="demo-item" @click="fillDemo('admin', 'admin123')">
            <strong>admin</strong> <span class="muted">/ admin123</span>
            <span class="role-tag">Администратор</span>
          </button>
          <button type="button" class="demo-item" @click="fillDemo('manager', 'manager123')">
            <strong>manager</strong> <span class="muted">/ manager123</span>
            <span class="role-tag">Руководитель</span>
          </button>
          <button type="button" class="demo-item" @click="fillDemo('ivanov', 'executor123')">
            <strong>ivanov</strong> <span class="muted">/ executor123</span>
            <span class="role-tag">Исполнитель</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 36px;
}

.brand {
  text-align: center;
  margin-bottom: 28px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 14px;
  background: var(--color-primary);
  color: white;
  font-weight: 700;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-name {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 6px;
}

.brand-tagline {
  font-size: 13px;
  line-height: 1.4;
}

.login-btn {
  width: 100%;
  justify-content: center;
  padding: 10px;
  font-size: 15px;
}

.error {
  color: var(--color-danger);
  font-size: 13px;
  background: #fee2e2;
  padding: 8px 12px;
  border-radius: var(--radius);
}

.demo-block {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.demo-title {
  margin-bottom: 8px;
}

.demo-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.demo-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-bg);
  border-radius: var(--radius);
  text-align: left;
  font-size: 13px;
  transition: background 0.15s;
}

.demo-item:hover {
  background: #e5e7eb;
}

.role-tag {
  margin-left: auto;
  font-size: 11px;
  background: var(--color-surface);
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
</style>
