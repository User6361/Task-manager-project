<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const props = defineProps({
  projects: { type: Array, required: true },
})

const emit = defineEmits(['close', 'created'])

const form = ref({
  title: '',
  description: '',
  importance: 2,
  deadline: '',
  project_id: props.projects[0]?.id || null,
  assignee_id: null,        // null → автораспределение
  tag_ids: [],
})

const users = ref([])
const tags = ref([])
const useAutoAssign = ref(true)
const error = ref('')
const loading = ref(false)

async function loadOptions() {
  const [u, t] = await Promise.all([api.get('/users/'), api.get('/tags/')])
  users.value = u.data.filter((x) => x.is_active)
  tags.value = t.data
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const payload = { ...form.value }
    if (useAutoAssign.value) payload.assignee_id = null
    if (!payload.deadline) payload.deadline = null
    else payload.deadline = new Date(payload.deadline).toISOString()

    await api.post('/tasks/', payload)
    emit('created')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка'
  } finally {
    loading.value = false
  }
}

function toggleTag(id) {
  const i = form.value.tag_ids.indexOf(id)
  if (i >= 0) form.value.tag_ids.splice(i, 1)
  else form.value.tag_ids.push(id)
}

onMounted(loadOptions)
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>Новая задача</h2>
        <button class="btn-close" @click="emit('close')">×</button>
      </div>

      <form @submit.prevent="submit">
        <div class="modal-body">
          <div class="field">
            <label class="label">Название</label>
            <input v-model="form.title" required class="input" placeholder="Краткое описание задачи" />
          </div>

          <div class="field">
            <label class="label">Описание</label>
            <textarea v-model="form.description" class="textarea" placeholder="Подробное описание (необязательно)" />
          </div>

          <div class="grid-2">
            <div class="field">
              <label class="label">Проект</label>
              <select v-model="form.project_id" required class="select">
                <option v-for="p in projects" :key="p.id" :value="p.id">
                  {{ p.name }}
                </option>
              </select>
            </div>

            <div class="field">
              <label class="label">Важность</label>
              <select v-model.number="form.importance" class="select">
                <option :value="1">1 — Низкая</option>
                <option :value="2">2 — Средняя</option>
                <option :value="3">3 — Высокая</option>
                <option :value="4">4 — Критическая</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label class="label">Крайний срок</label>
            <input v-model="form.deadline" type="datetime-local" class="input" />
            <div class="muted text-xs mt-2">
              Чем ближе срок, тем выше будет рассчитанный приоритет (срочность × важность)
            </div>
          </div>

          <div class="field">
            <label class="label">
              <input type="checkbox" v-model="useAutoAssign" />
              Автоматическое распределение исполнителя
            </label>
            <div v-if="useAutoAssign" class="auto-info muted text-xs">
              Алгоритм выберет наименее загруженного сотрудника по формуле
              W = α·N + β·P + γ·D
            </div>
            <select
              v-else
              v-model.number="form.assignee_id"
              class="select"
            >
              <option :value="null">— Выберите —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">
                {{ u.full_name }} ({{ u.role.name }})
              </option>
            </select>
          </div>

          <div class="field">
            <label class="label">Теги</label>
            <div class="tags-grid">
              <button
                v-for="t in tags"
                :key="t.id"
                type="button"
                class="tag-toggle"
                :class="{ active: form.tag_ids.includes(t.id) }"
                :style="{
                  background: form.tag_ids.includes(t.id) ? t.color : 'transparent',
                  borderColor: t.color,
                  color: form.tag_ids.includes(t.id) ? 'white' : t.color,
                }"
                @click="toggleTag(t.id)"
              >
                {{ t.name }}
              </button>
            </div>
          </div>

          <div v-if="error" class="error">{{ error }}</div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')">
            Отмена
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Создание...' : 'Создать задачу' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
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
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
  flex: 1;
}

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

.auto-info {
  background: #eff6ff;
  padding: 8px 12px;
  border-radius: var(--radius);
  margin-top: 6px;
  font-family: monospace;
}

.tags-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-toggle {
  border: 1px solid;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s;
}

.error {
  color: var(--color-danger);
  font-size: 13px;
  background: #fee2e2;
  padding: 8px 12px;
  border-radius: var(--radius);
  margin-top: 8px;
}
</style>
