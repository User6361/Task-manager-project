<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import TaskCard from '../components/TaskCard.vue'
import TaskFormModal from '../components/TaskFormModal.vue'

const auth = useAuthStore()
const board = ref({ todo: [], in_progress: [], review: [], done: [] })
const projects = ref([])
const selectedProject = ref(null)
const showCreateModal = ref(false)
const loading = ref(true)

const COLUMNS = [
  { key: 'todo',        title: 'К выполнению' },
  { key: 'in_progress', title: 'В работе'      },
  { key: 'review',      title: 'На проверке'   },
  { key: 'done',        title: 'Выполнено'     },
]

const totalTasks = computed(() =>
  Object.values(board.value).reduce((sum, arr) => sum + arr.length, 0)
)

async function loadBoard() {
  loading.value = true
  const params = selectedProject.value ? { project_id: selectedProject.value } : {}
  try {
    const { data } = await api.get('/tasks/board/view', { params })
    board.value = data
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  const { data } = await api.get('/projects/')
  projects.value = data
}

async function changeStatus(task, newStatus) {
  await api.patch(`/tasks/${task.id}`, { status: newStatus })
  await loadBoard()
}

function onCreated() {
  showCreateModal.value = false
  loadBoard()
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadBoard()])
})
</script>

<template>
  <div class="board-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Канбан-доска</h1>
        <div class="page-subtitle muted">
          Всего задач: {{ totalTasks }}
        </div>
      </div>

      <div class="header-actions">
        <select
          v-model="selectedProject"
          @change="loadBoard"
          class="select"
          style="min-width: 220px"
        >
          <option :value="null">Все проекты</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>

        <button
          v-if="auth.isManager"
          class="btn btn-primary"
          @click="showCreateModal = true"
        >
          + Новая задача
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading muted">Загрузка...</div>

    <div v-else class="kanban">
      <div
        v-for="col in COLUMNS"
        :key="col.key"
        class="column"
      >
        <div class="column-header">
          <span class="column-title">{{ col.title }}</span>
          <span class="column-count">{{ board[col.key].length }}</span>
        </div>

        <div class="column-body">
          <TaskCard
            v-for="task in board[col.key]"
            :key="task.id"
            :task="task"
            @status-change="changeStatus(task, $event)"
          />
          <div v-if="board[col.key].length === 0" class="column-empty muted">
            Пусто
          </div>
        </div>
      </div>
    </div>

    <TaskFormModal
      v-if="showCreateModal"
      :projects="projects"
      @close="showCreateModal = false"
      @created="onCreated"
    />
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.kanban {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  height: calc(100vh - 200px);
}

.column {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.column-header {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.column-title {
  font-weight: 600;
  font-size: 14px;
}

.column-count {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 1px 10px;
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.column-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.column-empty {
  text-align: center;
  font-size: 13px;
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 60px;
}
</style>
