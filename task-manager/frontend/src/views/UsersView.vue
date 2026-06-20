<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const users = ref([])
const roles = ref([])
const showCreateModal = ref(false)
const form = ref({
  login: '',
  password: '',
  full_name: '',
  email: '',
  role_id: null,
})
const error = ref('')
const submitting = ref(false)

async function loadAll() {
  const [u, r] = await Promise.all([
    api.get('/users/'),
    api.get('/users/roles/'),
  ])
  users.value = u.data
  roles.value = r.data
  if (!form.value.role_id && r.data.length > 0) {
    // По умолчанию — исполнитель
    const exec = r.data.find((x) => x.code === 'executor')
    form.value.role_id = exec?.id || r.data[0].id
  }
}

async function createUser() {
  error.value = ''
  submitting.value = true
  try {
    await api.post('/users/', form.value)
    showCreateModal.value = false
    form.value = {
      login: '', password: '', full_name: '', email: '',
      role_id: roles.value.find((x) => x.code === 'executor')?.id,
    }
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка'
  } finally {
    submitting.value = false
  }
}

async function toggleActive(user) {
  await api.patch(`/users/${user.id}`, { is_active: !user.is_active })
  await loadAll()
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}

onMounted(loadAll)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Пользователи</h1>
        <div class="muted text-sm">Всего: {{ users.length }}</div>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        + Добавить пользователя
      </button>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Сотрудник</th>
            <th>Логин</th>
            <th>Email</th>
            <th>Роль</th>
            <th>Статус</th>
            <th>Создан</th>
            <th class="text-right">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>
              <div class="user-cell">
                <div class="avatar">{{ u.full_name.charAt(0) }}</div>
                <strong>{{ u.full_name }}</strong>
              </div>
            </td>
            <td><code>{{ u.login }}</code></td>
            <td class="muted">{{ u.email || '—' }}</td>
            <td>
              <span class="role-tag" :class="`role-${u.role.code}`">
                {{ u.role.name }}
              </span>
            </td>
            <td>
              <span v-if="u.is_active" class="status-active">● Активен</span>
              <span v-else class="status-inactive">○ Заблокирован</span>
            </td>
            <td class="muted text-sm">{{ fmtDate(u.created_at) }}</td>
            <td class="text-right">
              <button
                class="btn btn-secondary btn-sm"
                @click="toggleActive(u)"
              >
                {{ u.is_active ? 'Заблокировать' : 'Разблокировать' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка создания -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Новый пользователь</h2>
          <button class="btn-close" @click="showCreateModal = false">×</button>
        </div>
        <form @submit.prevent="createUser">
          <div class="modal-body">
            <div class="grid-2">
              <div class="field">
                <label class="label">Логин</label>
                <input v-model="form.login" required class="input" placeholder="ivanov" />
              </div>
              <div class="field">
                <label class="label">Пароль</label>
                <input v-model="form.password" type="password" required class="input" placeholder="мин. 4 символа" />
              </div>
            </div>

            <div class="field">
              <label class="label">ФИО</label>
              <input v-model="form.full_name" required class="input" placeholder="Иванов Иван Петрович" />
            </div>

            <div class="grid-2">
              <div class="field">
                <label class="label">Email</label>
                <input v-model="form.email" type="email" class="input" placeholder="user@example.com" />
              </div>
              <div class="field">
                <label class="label">Роль</label>
                <select v-model.number="form.role_id" required class="select">
                  <option v-for="r in roles" :key="r.id" :value="r.id">
                    {{ r.name }}
                  </option>
                </select>
              </div>
            </div>

            <div v-if="error" class="error-msg">{{ error }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Создание...' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 4px;
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 12px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

th.text-right, td.text-right { text-align: right; }

td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  vertical-align: middle;
}

tbody tr:last-child td { border-bottom: none; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

code {
  background: var(--color-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
}

.role-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}

.role-admin    { background: #fef3c7; color: #854d0e; }
.role-manager  { background: #ddd6fe; color: #5b21b6; }
.role-executor { background: #dbeafe; color: #1e40af; }

.status-active   { color: var(--color-success); font-size: 12px; }
.status-inactive { color: var(--color-text-muted); font-size: 12px; }

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  font-size: 17px;
  font-weight: 600;
}

.btn-close {
  font-size: 24px;
  width: 28px;
  height: 28px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.btn-close:hover { background: var(--color-bg); }

.modal-body { padding: 20px; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.error-msg {
  color: var(--color-danger);
  background: #fee2e2;
  padding: 8px 12px;
  border-radius: var(--radius);
  font-size: 13px;
  margin-top: 8px;
}
</style>
