<script setup lang="ts">
const api = useApi()

const carousels = ref<any[]>([])
const loading = ref(true)
const filterStatus = ref('')
const filterLang = ref('')

async function load() {
  loading.value = true
  try {
    let path = '/carousels?'
    if (filterStatus.value) path += `status=${filterStatus.value}&`
    if (filterLang.value) path += `lang=${filterLang.value}&`
    carousels.value = await api.get(path)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([filterStatus, filterLang], load)

const statusLabels: Record<string, string> = {
  draft: 'Черновик',
  generating: 'Генерация',
  ready: 'Готова',
  failed: 'Ошибка',
}

function statusColor(s: string) {
  const map: Record<string, string> = {
    draft: '#6e6e73',
    generating: '#ff9f0a',
    ready: '#34c759',
    failed: '#ff3b30',
  }
  return map[s] || '#999'
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function slidesWord(n: number) {
  if (n % 10 === 1 && n % 100 !== 11) return `${n} слайд`
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return `${n} слайда`
  return `${n} слайдов`
}

const deleteId = ref<string | null>(null)
const deleteTitle = ref('')

function confirmDelete(c: any) {
  deleteId.value = c.id
  deleteTitle.value = c.title
}

async function doDelete() {
  if (!deleteId.value) return
  try {
    await api.del(`/carousels/${deleteId.value}`)
    deleteId.value = null
    await load()
  } catch (e) {
    console.error(e)
    deleteId.value = null
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Мои карусели</h1>
      <NuxtLink to="/carousels/new" class="btn btn-primary">+ Создать</NuxtLink>
    </div>

    <div class="filters">
      <select v-model="filterStatus" class="select">
        <option value="">Все статусы</option>
        <option value="draft">Черновик</option>
        <option value="generating">Генерация</option>
        <option value="ready">Готова</option>
        <option value="failed">Ошибка</option>
      </select>
      <select v-model="filterLang" class="select">
        <option value="">Все языки</option>
        <option value="ru">RU</option>
        <option value="en">EN</option>
      </select>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <div v-else-if="carousels.length === 0" class="empty">
      <p>Каруселей пока нет</p>
      <NuxtLink to="/carousels/new" class="btn btn-primary">Создать первую</NuxtLink>
    </div>

    <div v-else class="grid">
      <div v-for="c in carousels" :key="c.id" class="card">
        <div class="card-preview">
          <div class="card-preview-placeholder">
            <span>{{ slidesWord(c.slides_count) }}</span>
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-title">{{ c.title }}</h3>
          <div class="card-meta">
            <span class="badge" :style="{ background: statusColor(c.status) }">{{ statusLabels[c.status] || c.status }}</span>
            <span class="badge badge-outline">{{ c.language.toUpperCase() }}</span>
            <span class="card-date">{{ formatDate(c.created_at) }}</span>
          </div>
        </div>
        <div class="card-actions">
          <NuxtLink
            :to="`/carousels/${c.id}/editor`"
            class="btn btn-small"
          >
            {{ c.status === 'draft' ? 'Продолжить' : 'Открыть' }}
          </NuxtLink>
          <button class="btn btn-small btn-del" @click.stop="confirmDelete(c)">Удалить</button>
        </div>
      </div>
    </div>

    <!-- Подтверждение удаления -->
    <div v-if="deleteId" class="confirm-overlay" @click.self="deleteId = null">
      <div class="confirm-dialog">
        <p>Удалить карусель «{{ deleteTitle }}»?</p>
        <p class="confirm-sub">Все данные будут утеряны.</p>
        <div class="confirm-actions">
          <button @click="deleteId = null" class="btn btn-small">Отмена</button>
          <button @click="doDelete" class="btn btn-danger">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--card);
  color: var(--text);
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty .btn {
  margin-top: 16px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

.card-preview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-preview-placeholder {
  color: rgba(255,255,255,0.8);
  font-size: 16px;
  font-weight: 500;
}

.card-body {
  padding: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.badge-outline {
  background: transparent !important;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.card-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-actions {
  padding: 0 16px 16px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
  text-decoration: none;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.btn-small {
  padding: 6px 14px;
  font-size: 13px;
  background: var(--bg);
  color: var(--text);
}

.btn-small:hover {
  background: var(--border);
}

.btn-del {
  background: transparent; color: var(--danger); border: 1px solid var(--danger);
}
.btn-del:hover { background: #fff0f0; }

.btn-danger { background: #e74c3c; color: white; border: none; padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn-danger:hover { background: #c0392b; }

.confirm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.confirm-dialog {
  background: var(--card); border-radius: 12px; padding: 28px;
  max-width: 400px; width: 90%; box-shadow: var(--shadow-lg);
}
.confirm-dialog p { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.confirm-sub { font-size: 14px; color: var(--text-secondary); font-weight: 400 !important; margin-bottom: 20px !important; }
.confirm-actions { display: flex; gap: 10px; justify-content: flex-end; }

.card-actions { display: flex; gap: 8px; align-items: center; }

@media (max-width: 640px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .page-header h1 {
    font-size: 22px;
  }
}
</style>
