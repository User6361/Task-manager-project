<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const projects = ref([])
const projectStats = ref({})  // { project_id: { total, completed, in_progress } }
const loading = ref(true)
const showCreateModal = ref(false)
const form = ref({ name: '', description: '' })
const error = ref('')
const submitting = ref(false)

async function loadProjects() {
  loading.value = true
  try {
    const { data } = await api.get('/projects/')
    projects.value = data

    // Подгрузим статистику по задачам каждого проекта
    const allTasks = await api.get('/tasks/')
    const stats = {}
    for (const p of data) {
      const projTasks = allTasks.data.filter((t) => t.project_id === p.id)
      stats[p.id] = {
        total: projTasks.length,
        completed: projTasks.filter((t) => t.status === 'done').length,
        in_progress: projTasks.filter((t) => t.status === 'in_progress').length,
        overdue: projTasks.filter(
          (t) => t.deadline && new Date(t.deadline) < new Date() && t.status !== 'done'
        ).length,
      }
    }
    projectStats.value = stats
  } finally {
    loading.value = false
  }
}

async function createProject() {
  error.value = ''
  submitting.value = true
  try {
    await api.post('/projects/', form.value)
    showCreateModal.value = false
    form.value = { name: '', description: '' }
    await loadProjects()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка создания'
  } finally {
    submitting.value = false
  }
}

function openProject(p) {
  router.push({ path: '/tasks', query: { project_id: p.id } })
}

function progress(p) {
  const s = projectStats.value[p.id]
  if (!s || s.total === 0) return 0
  return Math.round((s.completed / s.total) * 100)
}

onMounted(loadProjects)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Проекты</h1>
        <div class="muted text-sm">Всего проектов: {{ projects.length }}</div>
      </div>
      <button
        v-if="auth.isManager"
        class="btn btn-primary"
        @click="showCreateModal = true"
      >
        + Новый проект
      </button>
    </div>

    <div v-if="loading" class="muted">Загрузка...</div>

    <div v-else class="projects-grid">
      <div
        v-for="p in projects"
        :key="p.id"
        class="project-card"
        @click="openProject(p)"
      >
        <div class="project-header">
          <div class="project-icon">◇</div>
          <div class="project-info">
            <div class="project-name">{{ p.name }}</div>
            <div class="project-desc muted text-sm">
              {{ p.description || 'Без описания' }}
            </div>
          </div>
        </div>

        <div class="project-stats" v-if="projectStats[p.id]">
          <div class="stat">
            <div class="stat-value">{{ projectStats[p.id].total }}</div>
            <div class="stat-label muted text-xs">всего</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ projectStats[p.id].in_progress }}</div>
            <div class="stat-label muted text-xs">в работе</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ projectStats[p.id].completed }}</div>
            <div class="stat-label muted text-xs">готово</div>
          </div>
          <div class="stat" v-if="projectStats[p.id].overdue > 0">
            <div class="stat-value overdue">{{ projectStats[p.id].overdue }}</div>
            <div class="stat-label muted text-xs">просрочено</div>
          </div>
        </div>

        <div v-if="projectStats[p.id]" class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progress(p) + '%' }"
          ></div>
        </div>
        <div class="muted text-xs mt-2">Выполнено: {{ progress(p) }}%</div>
      </div>

      <div v-if="projects.length === 0" class="empty muted card">
        Проектов пока нет
      </div>
    </div>

    <!-- Модалка создания -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Новый проект</h2>
          <button class="btn-close" @click="showCreateModal = false">×</button>
        </div>
        <form @submit.prevent="createProject">
          <div class="modal-body">
            <div class="field">
              <label class="label">Название проекта</label>
              <input v-model="form.name" required class="input" placeholder="Например, Корпоративный портал" />
            </div>
            <div class="field">
              <label class="label">Описание</label>
              <textarea v-model="form.description" class="textarea" rows="4" placeholder="Краткое описание проекта" />
            </div>
            <div v-if="error" class="error-msg">{{ error }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Создание...' : 'Создать проект' }}
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

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all 0.15s;
}

.project-card:hover {
  box-shadow: var(--shadow);
  border-color: #cbd5e1;
}

.project-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.project-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.project-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.project-desc {
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.stat-value.overdue {
  color: var(--color-danger);
}

.progress-bar {
  height: 6px;
  background: var(--color-bg);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-success);
  transition: width 0.3s;
}

.empty {
  padding: 60px;
  text-align: center;
  font-size: 15px;
}

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
  max-width: 480px;
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

.btn-close:hover {
  background: var(--color-bg);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
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
