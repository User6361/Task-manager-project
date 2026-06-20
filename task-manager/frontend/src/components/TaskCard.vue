<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['status-change'])
const router = useRouter()

const STATUS_FLOW = {
  todo:        { next: 'in_progress', nextLabel: 'Взять в работу' },
  in_progress: { next: 'review',      nextLabel: 'На проверку' },
  review:      { next: 'done',        nextLabel: 'Завершить' },
  done:        { next: null,          nextLabel: null },
}

const flow = computed(() => STATUS_FLOW[props.task.status])

const deadlineInfo = computed(() => {
  if (!props.task.deadline) return null
  const d = new Date(props.task.deadline)
  const now = new Date()
  const diffMs = d - now
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  let label, cls
  if (diffMs < 0) {
    label = `Просрочено на ${Math.abs(days)} дн.`
    cls = 'overdue'
  } else if (days === 0) {
    label = 'Сегодня'
    cls = 'urgent'
  } else if (days <= 3) {
    label = `Через ${days} дн.`
    cls = 'urgent'
  } else if (days <= 7) {
    label = `Через ${days} дн.`
    cls = 'soon'
  } else {
    label = d.toLocaleDateString('ru-RU')
    cls = ''
  }
  return { label, cls }
})

function openTask() {
  router.push(`/tasks/${props.task.id}`)
}

function advance() {
  if (flow.value?.next) {
    emit('status-change', flow.value.next)
  }
}
</script>

<template>
  <div class="task-card" @click="openTask">
    <div class="task-top">
      <span class="priority-badge" :class="`priority-${task.priority}`">
        P{{ task.priority }}
      </span>
      <span v-if="task.is_escalated" class="escalation-mark" title="Эскалирована">⚠</span>
    </div>

    <div class="task-title">{{ task.title }}</div>

    <div v-if="task.tags?.length" class="task-tags">
      <span
        v-for="tag in task.tags"
        :key="tag.id"
        class="tag-chip"
        :style="{ background: tag.color }"
      >
        {{ tag.name }}
      </span>
    </div>

    <div class="task-meta">
      <div v-if="task.assignee_name" class="task-assignee">
        <span class="meta-icon">◉</span>
        {{ task.assignee_name.split(' ')[0] }}
        {{ task.assignee_name.split(' ')[1]?.charAt(0) }}.
      </div>

      <div v-if="deadlineInfo" class="task-deadline" :class="deadlineInfo.cls">
        <span class="meta-icon">⏱</span>
        {{ deadlineInfo.label }}
      </div>
    </div>

    <button
      v-if="flow?.next"
      class="advance-btn"
      @click.stop="advance"
    >
      → {{ flow.nextLabel }}
    </button>
  </div>
</template>

<style scoped>
.task-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.task-card:hover {
  box-shadow: var(--shadow);
  border-color: #cbd5e1;
}

.task-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.escalation-mark {
  color: var(--color-danger);
  font-size: 14px;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  margin-bottom: 8px;
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.tag-chip {
  font-size: 10px;
  font-weight: 500;
  color: white;
  padding: 1px 7px;
  border-radius: 999px;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.task-meta > div {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-icon {
  opacity: 0.6;
}

.task-deadline.urgent { color: #ea580c; font-weight: 500; }
.task-deadline.overdue { color: var(--color-danger); font-weight: 600; }
.task-deadline.soon { color: var(--color-warning); }

.advance-btn {
  width: 100%;
  padding: 5px 8px;
  font-size: 11px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  font-weight: 500;
  transition: all 0.15s;
  margin-top: 4px;
}

.advance-btn:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}
</style>
