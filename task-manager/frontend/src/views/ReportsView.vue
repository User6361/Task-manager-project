<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const report = ref(null)
const loading = ref(true)
const days = ref(30)

async function loadReport() {
  loading.value = true
  try {
    const { data } = await api.get('/tasks/reports/by-user', {
      params: { days: days.value },
    })
    report.value = data
  } finally {
    loading.value = false
  }
}

const sortedItems = computed(() => {
  if (!report.value) return []
  return [...report.value.items].sort(
    (a, b) => b.completion_rate - a.completion_rate
  )
})

const totals = computed(() => {
  if (!report.value) return { total: 0, completed: 0, overdue: 0 }
  return report.value.items.reduce(
    (acc, i) => ({
      total: acc.total + i.total_tasks,
      completed: acc.completed + i.completed_tasks,
      overdue: acc.overdue + i.overdue_tasks,
    }),
    { total: 0, completed: 0, overdue: 0 }
  )
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}

function progressClass(rate) {
  if (rate >= 75) return 'good'
  if (rate >= 40) return 'medium'
  return 'low'
}

onMounted(loadReport)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Отчёт по производительности</h1>
        <div class="muted text-sm" v-if="report">
          Период: {{ fmtDate(report.period_start) }} — {{ fmtDate(report.period_end) }}
        </div>
      </div>

      <div class="header-actions">
        <select v-model.number="days" @change="loadReport" class="select">
          <option :value="7">За неделю</option>
          <option :value="14">За 2 недели</option>
          <option :value="30">За месяц</option>
          <option :value="90">За квартал</option>
          <option :value="365">За год</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="muted">Загрузка...</div>

    <div v-else-if="report" class="report-content">
      <!-- Общая сводка -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-label muted text-sm">Всего задач за период</div>
          <div class="summary-value">{{ totals.total }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label muted text-sm">Выполнено</div>
          <div class="summary-value good">{{ totals.completed }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label muted text-sm">Просрочено</div>
          <div class="summary-value bad">{{ totals.overdue }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label muted text-sm">Средний % выполнения</div>
          <div class="summary-value">
            {{ totals.total > 0 ? Math.round(totals.completed / totals.total * 100) : 0 }}%
          </div>
        </div>
      </div>

      <!-- Таблица по сотрудникам -->
      <div class="card mt-4">
        <h2 class="card-title">По сотрудникам</h2>
        <table>
          <thead>
            <tr>
              <th>Сотрудник</th>
              <th class="text-right">Всего</th>
              <th class="text-right">Выполнено</th>
              <th class="text-right">Просрочено</th>
              <th>Эффективность</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedItems" :key="item.user_id">
              <td>
                <div class="user-cell">
                  <div class="avatar">{{ item.user_name.charAt(0) }}</div>
                  <span>{{ item.user_name }}</span>
                </div>
              </td>
              <td class="text-right">{{ item.total_tasks }}</td>
              <td class="text-right good">{{ item.completed_tasks }}</td>
              <td class="text-right" :class="{ bad: item.overdue_tasks > 0 }">
                {{ item.overdue_tasks }}
              </td>
              <td>
                <div class="rate-row">
                  <div class="rate-bar">
                    <div
                      class="rate-fill"
                      :class="progressClass(item.completion_rate)"
                      :style="{ width: item.completion_rate + '%' }"
                    ></div>
                  </div>
                  <span class="rate-value" :class="progressClass(item.completion_rate)">
                    {{ item.completion_rate }}%
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="sortedItems.length === 0" class="empty muted">
          Нет данных за выбранный период
        </div>
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

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.summary-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
}

.summary-label {
  margin-bottom: 6px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
}

.summary-value.good { color: var(--color-success); }
.summary-value.bad { color: var(--color-danger); }

.card {
  padding: 16px 20px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--color-border);
}

th.text-right, td.text-right { text-align: right; }

td {
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
}

tbody tr:last-child td { border-bottom: none; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.good { color: var(--color-success); font-weight: 500; }
.bad { color: var(--color-danger); font-weight: 500; }

.rate-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rate-bar {
  flex: 1;
  height: 8px;
  background: var(--color-bg);
  border-radius: 999px;
  overflow: hidden;
  max-width: 200px;
}

.rate-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s;
}

.rate-fill.good { background: var(--color-success); }
.rate-fill.medium { background: var(--color-warning); }
.rate-fill.low { background: var(--color-danger); }

.rate-value {
  font-size: 13px;
  font-weight: 600;
  min-width: 40px;
}

.rate-value.good { color: var(--color-success); }
.rate-value.medium { color: var(--color-warning); }
.rate-value.low { color: var(--color-danger); }

.empty {
  padding: 30px;
  text-align: center;
  font-size: 14px;
}
</style>
