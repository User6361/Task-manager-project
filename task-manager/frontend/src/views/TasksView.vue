<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const tasks = ref([])
const projects = ref([])
const filters = ref({
  project_id: null,
  status: null,
  only_mine: false,
})

const STATUS_LABELS = {
  todo: 'К выполнению',
  in_progress: 'В работе',
  review: 'На проверке',
  done: 'Выполнено',
}

async function load() {
  const params = {}
  if (filters.value.project_id) params.project_id = filters.value.project_id
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.only_mine) params.only_mine = true

  const { data } = await api.get('/tasks/', { params })
  tasks.value = data
}

async function loadProjects() {
  const { data } = await api.get('/projects/')
  projects.value = data
}

watch(filters, load, { deep: true })

onMounted(async () => {
  await Promise.all([loadProjects(), load()])
})

function openTask(t) {
  router.push(`/tasks/${t.id}`)
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

function projectName(id) {
  return projects.value.find((p) => p.id === id)?.name || '—'
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Задачи</h1>
      <span class="muted">Всего: {{ tasks.length }}</span>
    </div>

    <div class="filters card">
      <div class="filter-field">
        <label class="label">Проект</label>
        <select v-model="filters.project_id" class="select">
          <option :value="null">Все</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>
      </div>

      <div class="filter-field">
        <label class="label">Статус</label>
        <select v-model="filters.status" class="select">
          <option :value="null">Все</option>
          <option value="todo">К выполнению</option>
          <option value="in_progress">В работе</option>
          <option value="review">На проверке</option>
          <option value="done">Выполнено</option>
        </select>
      </div>

      <div class="filter-field" v-if="auth.isManager">
        <label class="label">
          <input type="checkbox" v-model="filters.only_mine" />
          Только мои задачи
        </label>
      </div>
    </div>

    <div class="table-wrap card mt-4">
      <table>
        <thead>
          <tr>
            <th class="col-prio">Приор.</th>
            <th>Название</th>
            <th>Статус</th>
            <th>Проект</th>
            <th>Исполнитель</th>
            <th>Срок</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tasks" :key="t.id" @click="openTask(t)">
            <td>
              <span class="priority-badge" :class="`priority-${t.priority}`">
                P{{ t.priority }}
              </span>
            </td>
            <td>
              <div class="task-name">
                {{ t.title }}
                <span v-if="t.is_escalated" class="escalation">⚠</span>
              </div>
              <div v-if="t.tags?.length" class="task-tags">
                <span
                  v-for="tag in t.tags"
                  :key="tag.id"
                  class="tag"
                  :style="{ background: tag.color }"
                >{{ tag.name }}</span>
              </div>
            </td>
            <td>
              <span class="status" :class="`status-${t.status}`">
                {{ STATUS_LABELS[t.status] }}
              </span>
            </td>
            <td class="muted text-sm">{{ projectName(t.project_id) }}</td>
            <td class="muted text-sm">{{ t.assignee_name || '—' }}</td>
            <td class="muted text-sm">{{ fmtDate(t.deadline) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="tasks.length === 0" class="empty muted">
        Задачи не найдены
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
}

.filters {
  padding: 14px 16px;
  display: flex;
  gap: 16px;
  align-items: flex-end;
}

.filter-field {
  flex: 1;
  max-width: 240px;
}

.table-wrap {
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg);
}

th {
  text-align: left;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--color-border);
}

.col-prio { width: 70px; }

td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  vertical-align: top;
}

tbody tr {
  cursor: pointer;
  transition: background 0.1s;
}

tbody tr:hover {
  background: var(--color-bg);
}

tbody tr:last-child td {
  border-bottom: none;
}

.task-name {
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.escalation {
  color: var(--color-danger);
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  font-size: 10px;
  font-weight: 500;
  color: white;
  padding: 1px 7px;
  border-radius: 999px;
}

.status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.status-todo        { background: #f1f5f9; color: #475569; }
.status-in_progress { background: #dbeafe; color: #1e40af; }
.status-review      { background: #fef3c7; color: #854d0e; }
.status-done        { background: #d1fae5; color: #065f46; }

.empty {
  text-align: center;
  padding: 40px;
  font-size: 14px;
}
</style>
