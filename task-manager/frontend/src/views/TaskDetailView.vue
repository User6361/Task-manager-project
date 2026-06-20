<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const task = ref(null)
const comments = ref([])
const history = ref([])
const newComment = ref('')
const editing = ref(false)
const editForm = ref({})
const users = ref([])
const showAutoAssignResult = ref(null)
const loading = ref(true)

const STATUS_LABELS = {
  todo: 'К выполнению',
  in_progress: 'В работе',
  review: 'На проверке',
  done: 'Выполнено',
}

const taskId = computed(() => parseInt(route.params.id))

async function loadAll() {
  loading.value = true
  try {
    const [t, c, h, u] = await Promise.all([
      api.get(`/tasks/${taskId.value}`),
      api.get(`/tasks/${taskId.value}/comments`),
      api.get(`/tasks/${taskId.value}/history`),
      api.get('/users/'),
    ])
    task.value = t.data
    comments.value = c.data
    history.value = h.data
    users.value = u.data.filter((x) => x.is_active)
    editForm.value = {
      title: t.data.title,
      description: t.data.description,
      importance: t.data.importance,
      deadline: t.data.deadline ? t.data.deadline.slice(0, 16) : '',
      assignee_id: t.data.assignee_id,
    }
  } finally {
    loading.value = false
  }
}

async function changeStatus(newStatus) {
  await api.patch(`/tasks/${taskId.value}`, { status: newStatus })
  await loadAll()
}

async function saveEdit() {
  const payload = { ...editForm.value }
  if (payload.deadline) payload.deadline = new Date(payload.deadline).toISOString()
  else payload.deadline = null
  await api.patch(`/tasks/${taskId.value}`, payload)
  editing.value = false
  await loadAll()
}

async function addComment() {
  if (!newComment.value.trim()) return
  await api.post(`/tasks/${taskId.value}/comments`, { text: newComment.value })
  newComment.value = ''
  await loadAll()
}

async function runAutoAssign() {
  const { data } = await api.post(`/tasks/auto-assign/${taskId.value}`)
  showAutoAssignResult.value = data
  await loadAll()
}

async function deleteTask() {
  if (!confirm('Удалить задачу безвозвратно?')) return
  await api.delete(`/tasks/${taskId.value}`)
  router.push('/tasks')
}

function fmtDateTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ru-RU')
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

onMounted(loadAll)
</script>

<template>
  <div v-if="loading" class="muted">Загрузка...</div>
  <div v-else-if="task" class="task-detail">
    <div class="back-link">
      <router-link to="/tasks">← Все задачи</router-link>
    </div>

    <div class="grid">
      <!-- Левая колонка: основная информация -->
      <div class="main-col">
        <div class="card task-header">
          <div class="task-meta-top">
            <span class="priority-badge" :class="`priority-${task.priority}`">
              Приоритет {{ task.priority }}
            </span>
            <span class="status" :class="`status-${task.status}`">
              {{ STATUS_LABELS[task.status] }}
            </span>
            <span v-if="task.is_escalated" class="escalation-tag">
              ⚠ Эскалирована руководителю
            </span>
          </div>

          <h1 v-if="!editing" class="task-title">{{ task.title }}</h1>
          <input v-else v-model="editForm.title" class="input title-input" />

          <div class="task-tags" v-if="task.tags?.length">
            <span
              v-for="tag in task.tags"
              :key="tag.id"
              class="tag"
              :style="{ background: tag.color }"
            >{{ tag.name }}</span>
          </div>

          <div class="description-block">
            <div class="label">Описание</div>
            <div v-if="!editing" class="task-description">
              {{ task.description || 'Нет описания' }}
            </div>
            <textarea v-else v-model="editForm.description" class="textarea" />
          </div>

          <div v-if="auth.isManager" class="task-actions">
            <template v-if="!editing">
              <button class="btn btn-secondary btn-sm" @click="editing = true">
                ✎ Редактировать
              </button>
              <button class="btn btn-secondary btn-sm" @click="runAutoAssign">
                ⚙ Автораспределение
              </button>
              <button class="btn btn-danger btn-sm" @click="deleteTask">
                Удалить
              </button>
            </template>
            <template v-else>
              <button class="btn btn-primary btn-sm" @click="saveEdit">
                Сохранить
              </button>
              <button class="btn btn-secondary btn-sm" @click="editing = false">
                Отмена
              </button>
            </template>
          </div>

          <!-- Кнопки изменения статуса -->
          <div class="status-actions">
            <button
              v-if="task.status !== 'todo'"
              class="status-btn"
              @click="changeStatus('todo')"
            >→ К выполнению</button>
            <button
              v-if="task.status !== 'in_progress'"
              class="status-btn"
              @click="changeStatus('in_progress')"
            >→ В работу</button>
            <button
              v-if="task.status !== 'review'"
              class="status-btn"
              @click="changeStatus('review')"
            >→ На проверку</button>
            <button
              v-if="task.status !== 'done'"
              class="status-btn done-btn"
              @click="changeStatus('done')"
            >✓ Завершить</button>
          </div>
        </div>

        <!-- Результат автораспределения (debug-инфо) -->
        <div v-if="showAutoAssignResult" class="card autodist-result">
          <div class="card-title">
            <strong>Результат автораспределения</strong>
            <button class="link" @click="showAutoAssignResult = null">скрыть</button>
          </div>
          <div class="autodist-summary">
            Выбран: <strong>{{ showAutoAssignResult.assignee_name }}</strong>
            (вес W = {{ showAutoAssignResult.weight }})
          </div>
          <table class="autodist-table">
            <thead>
              <tr>
                <th>Кандидат</th>
                <th>N (задач)</th>
                <th>P (приор.)</th>
                <th>D (срочн.)</th>
                <th>W</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in showAutoAssignResult.candidates"
                :key="c.user_id"
                :class="{ chosen: c.is_chosen }"
              >
                <td>
                  {{ c.user_name }}
                  <span v-if="c.is_chosen" class="chosen-mark">✓</span>
                </td>
                <td>{{ c.active_tasks_count }}</td>
                <td>{{ c.total_priority }}</td>
                <td>{{ c.deadline_pressure }}</td>
                <td><strong>{{ c.weight }}</strong></td>
              </tr>
            </tbody>
          </table>
          <div class="autodist-formula muted text-xs mt-2">
            Формула: W = α·N + β·P + γ·D, где α=1.0, β=0.5, γ=2.0
          </div>
        </div>

        <!-- Комментарии -->
        <div class="card comments-block">
          <h3 class="card-title">Комментарии ({{ comments.length }})</h3>

          <div class="comments-list">
            <div v-for="c in comments" :key="c.id" class="comment">
              <div class="comment-author">
                <div class="avatar">{{ c.author_name?.charAt(0) }}</div>
                <strong>{{ c.author_name }}</strong>
                <span class="muted text-xs">{{ fmtDateTime(c.created_at) }}</span>
              </div>
              <div class="comment-text">{{ c.text }}</div>
            </div>

            <div v-if="comments.length === 0" class="muted">
              Комментариев пока нет
            </div>
          </div>

          <div class="comment-form">
            <textarea
              v-model="newComment"
              class="textarea"
              placeholder="Написать комментарий..."
              rows="2"
            />
            <button class="btn btn-primary" @click="addComment" :disabled="!newComment.trim()">
              Отправить
            </button>
          </div>
        </div>
      </div>

      <!-- Правая колонка: метаданные и история -->
      <div class="side-col">
        <div class="card info-block">
          <h3 class="card-title">Информация</h3>
          <div class="info-row" v-if="!editing">
            <span class="info-label">Исполнитель</span>
            <span>{{ task.assignee_name || 'Не назначен' }}</span>
          </div>
          <div class="info-row" v-else>
            <span class="info-label">Исполнитель</span>
            <select v-model.number="editForm.assignee_id" class="select select-sm">
              <option :value="null">— Авто —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">
                {{ u.full_name }}
              </option>
            </select>
          </div>

          <div class="info-row">
            <span class="info-label">Автор</span>
            <span>{{ task.author_name }}</span>
          </div>

          <div class="info-row" v-if="!editing">
            <span class="info-label">Важность</span>
            <span>{{ task.importance }} / 4</span>
          </div>
          <div class="info-row" v-else>
            <span class="info-label">Важность</span>
            <select v-model.number="editForm.importance" class="select select-sm">
              <option :value="1">1 — Низкая</option>
              <option :value="2">2 — Средняя</option>
              <option :value="3">3 — Высокая</option>
              <option :value="4">4 — Критическая</option>
            </select>
          </div>

          <div class="info-row" v-if="!editing">
            <span class="info-label">Крайний срок</span>
            <span>{{ fmtDate(task.deadline) }}</span>
          </div>
          <div class="info-row" v-else>
            <span class="info-label">Крайний срок</span>
            <input v-model="editForm.deadline" type="datetime-local" class="input input-sm" />
          </div>

          <div class="info-row">
            <span class="info-label">Создано</span>
            <span>{{ fmtDateTime(task.created_at) }}</span>
          </div>

          <div class="info-row">
            <span class="info-label">Обновлено</span>
            <span>{{ fmtDateTime(task.updated_at) }}</span>
          </div>
        </div>

        <div class="card history-block">
          <h3 class="card-title">История изменений ({{ history.length }})</h3>
          <div v-if="history.length === 0" class="muted text-sm">Нет изменений</div>
          <div v-else class="history-list">
            <div v-for="h in history" :key="h.id" class="history-item">
              <div class="history-line">
                <strong>{{ h.user_name }}</strong>
                изменил <em>{{ h.field }}</em>:
              </div>
              <div class="history-change">
                <span class="old-val">{{ h.old_value || '—' }}</span>
                →
                <span class="new-val">{{ h.new_value || '—' }}</span>
              </div>
              <div class="muted text-xs">{{ fmtDateTime(h.changed_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.back-link {
  margin-bottom: 12px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
}

.task-header {
  padding: 20px;
}

.task-meta-top {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.task-title {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 8px;
}

.title-input {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.tag {
  font-size: 11px;
  font-weight: 500;
  color: white;
  padding: 2px 9px;
  border-radius: 999px;
}

.description-block {
  margin-bottom: 16px;
}

.task-description {
  white-space: pre-wrap;
  line-height: 1.5;
  color: var(--color-text);
}

.task-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.status-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.status-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  font-size: 12px;
  font-weight: 500;
}

.status-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.status-btn.done-btn:hover {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.status {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.status-todo        { background: #f1f5f9; color: #475569; }
.status-in_progress { background: #dbeafe; color: #1e40af; }
.status-review      { background: #fef3c7; color: #854d0e; }
.status-done        { background: #d1fae5; color: #065f46; }

.escalation-tag {
  background: #fee2e2;
  color: var(--color-danger);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.autodist-result {
  padding: 16px 20px;
  background: #fffbeb;
  border-color: #fde68a;
}

.autodist-summary {
  font-size: 14px;
  margin-bottom: 12px;
}

.autodist-table {
  width: 100%;
  font-size: 12px;
  border-collapse: collapse;
}

.autodist-table th,
.autodist-table td {
  padding: 6px 10px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.autodist-table th {
  background: rgba(255,255,255,0.5);
  font-weight: 600;
}

.autodist-table tr.chosen {
  background: rgba(34,197,94,0.1);
}

.chosen-mark {
  color: var(--color-success);
  font-weight: 700;
  margin-left: 6px;
}

.autodist-formula {
  font-family: monospace;
}

.comments-block {
  padding: 16px 20px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.comment {
  padding: 10px 12px;
  background: var(--color-bg);
  border-radius: var(--radius);
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.comment-text {
  font-size: 13px;
  line-height: 1.4;
  white-space: pre-wrap;
}

.comment-form {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.comment-form .textarea {
  flex: 1;
}

.info-block, .history-block {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--color-text-muted);
  font-size: 12px;
}

.input-sm, .select-sm {
  padding: 4px 8px;
  font-size: 12px;
  max-width: 60%;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  font-size: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-border);
}

.history-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.history-line {
  margin-bottom: 4px;
}

.history-change {
  margin: 4px 0;
}

.old-val {
  color: var(--color-danger);
  text-decoration: line-through;
}

.new-val {
  color: var(--color-success);
}

.link {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
}
</style>
