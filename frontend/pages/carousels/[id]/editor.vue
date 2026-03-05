<script setup lang="ts">
const api = useApi()
const route = useRoute()
const carouselId = route.params.id as string

const carousel = ref<any>(null)
const slides = ref<any[]>([])
const currentSlide = ref(0)
const loading = ref(true)
const generating = ref(false)
const generationId = ref('')
const generationStatus = ref('')
const tokensEst = ref(0)
const exporting = ref(false)
const exportId = ref('')
const exportStatus = ref('')
const exportUrl = ref('')
const error = ref('')
const savingSlide = ref(false)
const savingDesign = ref(false)
const uploadingBg = ref(false)
const activePanel = ref('template')
const showHistory = ref(false)
const generations = ref<any[]>([])
const showDeleteConfirm = ref(false)
const dragIndex = ref<number | null>(null)

const design = ref({
  template: 'classic',
  bg_color: '#ffffff',
  bg_asset_id: null as string | null,
  bg_dim: 0,
  padding: 40,
  align_h: 'left',
  align_v: 'top',
  header_enabled: false,
  header_text: '',
  footer_enabled: false,
  footer_text: '',
})

const statusMap: Record<string, string> = {
  queued: 'в очереди',
  running: 'генерация...',
  done: 'готово',
  failed: 'ошибка',
  'starting...': 'запуск...',
}

function statusRu(s: string) {
  return statusMap[s] || s
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

let genEventSource: EventSource | null = null
let expEventSource: EventSource | null = null

function closeSSE() {
  genEventSource?.close()
  genEventSource = null
  expEventSource?.close()
  expEventSource = null
}

const defaultDesign = () => ({
  template: 'classic',
  bg_color: '#ffffff',
  bg_asset_id: null as string | null,
  bg_dim: 0,
  padding: 40,
  align_h: 'left',
  align_v: 'top',
  header_enabled: false,
  header_text: '',
  footer_enabled: false,
  footer_text: '',
})

function syncDesignFromSlide() {
  const s = slides.value[currentSlide.value]
  const carouselDesign = carousel.value?.design || {}
  const slideDesign = s?.design || {}
  Object.assign(design.value, defaultDesign(), carouselDesign, slideDesign)
}

async function loadData() {
  loading.value = true
  try {
    carousel.value = await api.get(`/carousels/${carouselId}`)
    slides.value = await api.get(`/carousels/${carouselId}/slides`)
    if (slides.value.length > 0) {
      syncDesignFromSlide()
    } else {
      Object.assign(design.value, defaultDesign(), carousel.value?.design || {})
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function generate() {
  generating.value = true
  generationStatus.value = 'starting...'
  error.value = ''
  try {
    const gen = await api.post('/generations', { carousel_id: carouselId })
    generationId.value = gen.id
    tokensEst.value = gen.tokens_est
    generationStatus.value = gen.status
    startGenSSE(gen.id)
  } catch (e: any) {
    error.value = e.message
    generating.value = false
  }
}

function startGenSSE(id: string) {
  genEventSource?.close()
  const url = `${api.baseURL}/generations/${id}/stream`
  genEventSource = new EventSource(url)

  genEventSource.onmessage = async (event) => {
    const data = JSON.parse(event.data)
    generationStatus.value = data.status
    if (data.status === 'done') {
      generating.value = false
      genEventSource?.close()
      genEventSource = null
      await loadData()
    } else if (data.status === 'failed' || data.status === 'error') {
      error.value = data.error || 'Генерация не удалась'
      generating.value = false
      genEventSource?.close()
      genEventSource = null
    }
  }

  genEventSource.onerror = () => {
    genEventSource?.close()
    genEventSource = null
    pollGeneration()
  }
}

async function pollGeneration() {
  const id = generationId.value
  const poll = async () => {
    try {
      const gen = await api.get(`/generations/${id}`)
      generationStatus.value = gen.status
      if (gen.status === 'done') {
        generating.value = false
        await loadData()
        return
      }
      if (gen.status === 'failed') {
        error.value = gen.error || 'Генерация не удалась'
        generating.value = false
        return
      }
      setTimeout(poll, 2000)
    } catch {
      setTimeout(poll, 3000)
    }
  }
  setTimeout(poll, 2000)
}

async function saveSlide() {
  if (!slides.value[currentSlide.value]) return
  savingSlide.value = true
  try {
    const s = slides.value[currentSlide.value]
    await api.patch(`/carousels/${carouselId}/slides/${s.id}`, {
      title: s.title,
      body: s.body,
      footer: s.footer,
    })
  } catch (e: any) {
    error.value = e.message
  } finally {
    savingSlide.value = false
  }
}

async function saveDesign() {
  const s = slides.value[currentSlide.value]
  if (!s) return
  savingDesign.value = true
  try {
    await api.patch(`/carousels/${carouselId}/slides/${s.id}`, {
      design: { ...design.value },
    })
    if (slides.value[currentSlide.value]) {
      slides.value[currentSlide.value].design = { ...design.value }
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    savingDesign.value = false
  }
}

async function startExport() {
  exporting.value = true
  exportStatus.value = 'starting...'
  exportUrl.value = ''
  error.value = ''
  try {
    const exp = await api.post('/exports', { carousel_id: carouselId })
    exportId.value = exp.id
    exportStatus.value = exp.status
    startExpSSE(exp.id)
  } catch (e: any) {
    error.value = e.message
    exporting.value = false
  }
}

function startExpSSE(id: string) {
  expEventSource?.close()
  const url = `${api.baseURL}/exports/${id}/stream`
  expEventSource = new EventSource(url)

  expEventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    exportStatus.value = data.status
    if (data.status === 'done') {
      exporting.value = false
      exportUrl.value = data.url || ''
      expEventSource?.close()
      expEventSource = null
    } else if (data.status === 'failed' || data.status === 'error') {
      error.value = data.error || 'Экспорт не удался'
      exporting.value = false
      expEventSource?.close()
      expEventSource = null
    }
  }

  expEventSource.onerror = () => {
    expEventSource?.close()
    expEventSource = null
    pollExport()
  }
}

async function pollExport() {
  const id = exportId.value
  const poll = async () => {
    try {
      const exp = await api.get(`/exports/${id}`)
      exportStatus.value = exp.status
      if (exp.status === 'done') {
        exporting.value = false
        exportUrl.value = exp.url || ''
        return
      }
      if (exp.status === 'failed') {
        error.value = exp.error || 'Экспорт не удался'
        exporting.value = false
        return
      }
      setTimeout(poll, 3000)
    } catch {
      setTimeout(poll, 4000)
    }
  }
  setTimeout(poll, 3000)
}

async function uploadBg(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const fd = new FormData()
  fd.append('file', input.files[0])
  uploadingBg.value = true
  error.value = ''
  try {
    const res = await api.upload<any>('/assets/upload', fd)
    design.value.bg_asset_id = res.id
    await saveDesign()
  } catch (err: any) {
    error.value = err.message
  } finally {
    uploadingBg.value = false
    input.value = ''
  }
}

async function removeBg() {
  design.value.bg_asset_id = null
  await saveDesign()
}

async function loadHistory() {
  try {
    generations.value = await api.get(`/generations/by-carousel/${carouselId}`)
    showHistory.value = true
  } catch (e: any) {
    error.value = e.message
  }
}

async function addSlide() {
  try {
    const newSlide = await api.post(`/carousels/${carouselId}/slides`, {
      title: 'Новый слайд',
      body: '',
      footer: '',
    })
    slides.value.push(newSlide)
    currentSlide.value = slides.value.length - 1
  } catch (e: any) {
    error.value = e.message
  }
}

async function removeSlide(index: number) {
  const slide = slides.value[index]
  if (!slide) return
  try {
    await api.del(`/carousels/${carouselId}/slides/${slide.id}`)
    slides.value.splice(index, 1)
    if (currentSlide.value >= slides.value.length) {
      currentSlide.value = Math.max(0, slides.value.length - 1)
    }
  } catch (e: any) {
    error.value = e.message
  }
}

function onDragStart(index: number) {
  dragIndex.value = index
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

async function onDrop(targetIndex: number) {
  if (dragIndex.value === null || dragIndex.value === targetIndex) {
    dragIndex.value = null
    return
  }

  const moved = slides.value.splice(dragIndex.value, 1)[0]
  slides.value.splice(targetIndex, 0, moved)
  currentSlide.value = targetIndex
  dragIndex.value = null

  const ids = slides.value.map((s: any) => s.id)
  try {
    slides.value = await api.post(`/carousels/${carouselId}/slides/reorder`, { slide_ids: ids })
    currentSlide.value = targetIndex
  } catch (e: any) {
    error.value = e.message
    await loadData()
  }
}

async function deleteCarousel() {
  try {
    await api.del(`/carousels/${carouselId}`)
    navigateTo('/carousels')
  } catch (e: any) {
    error.value = e.message
  }
}

const currentSlideData = computed(() => slides.value[currentSlide.value] || null)

const previewStyle = computed(() => {
  const d = design.value
  const style: Record<string, string> = {
    backgroundColor: d.bg_color,
    padding: `${d.padding}px`,
    textAlign: d.align_h,
  }
  if (d.bg_asset_id) {
    style.backgroundImage = `url(${api.baseURL}/assets/${d.bg_asset_id})`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
  }
  return style
})

const previewBodyStyle = computed(() => {
  const d = design.value
  return {
    justifyContent: d.align_v === 'top' ? 'flex-start' : d.align_v === 'center' ? 'center' : 'flex-end',
  }
})

const templateNames: Record<string, string> = {
  classic: 'Классический',
  bold: 'Жирный',
  minimal: 'Минимальный',
}

const alignHLabels: Record<string, string> = {
  left: 'Лево',
  center: 'Центр',
  right: 'Право',
}

const alignVLabels: Record<string, string> = {
  top: 'Верх',
  center: 'Центр',
  bottom: 'Низ',
}

watch(currentSlide, () => {
  if (slides.value.length > 0) syncDesignFromSlide()
})

onMounted(loadData)
onUnmounted(closeSSE)
</script>

<template>
  <div class="editor-page">
    <div v-if="loading" class="loading">Загрузка редактора...</div>

    <template v-else>
      <div class="editor-toolbar">
        <div class="toolbar-left">
          <NuxtLink to="/carousels" class="back-link">&larr;</NuxtLink>
          <h2>{{ carousel?.title }}</h2>
        </div>
        <div class="toolbar-actions">
          <button v-if="slides.length === 0" @click="generate" :disabled="generating" class="btn btn-primary">
            {{ generating ? `Генерация (${statusRu(generationStatus)})...` : 'Сгенерировать слайды' }}
          </button>
          <button v-if="slides.length > 0" @click="generate" :disabled="generating" class="btn btn-outline">
            {{ generating ? `${statusRu(generationStatus)}...` : 'Перегенерировать' }}
          </button>
          <button @click="loadHistory" class="btn btn-outline btn-sm">История</button>
          <button v-if="slides.length > 0" @click="startExport" :disabled="exporting" class="btn btn-primary">
            {{ exporting ? `Экспорт (${statusRu(exportStatus)})...` : 'Экспорт PNG' }}
          </button>
          <button @click="showDeleteConfirm = true" class="btn btn-danger btn-sm">Удалить</button>
        </div>
      </div>

      <div v-if="tokensEst && generating" class="info-bar">
        Примерный расход токенов: ~{{ tokensEst }}
      </div>

      <div v-if="exportUrl" class="success-bar">
        Экспорт готов! <a :href="exportUrl" target="_blank" class="download-link">Скачать ZIP</a>
      </div>

      <div v-if="error" class="error-bar">
        {{ error }}
        <button @click="error = ''" class="error-close">&times;</button>
      </div>

      <!-- История генераций -->
      <div v-if="showHistory" class="history-panel">
        <div class="history-header">
          <h3>История генераций</h3>
          <button @click="showHistory = false" class="error-close">&times;</button>
        </div>
        <div v-if="generations.length === 0" class="history-empty">Нет генераций</div>
        <div v-for="g in generations" :key="g.id" class="history-item">
          <span :class="['history-status', `st-${g.status}`]">{{ statusRu(g.status) }}</span>
          <span class="history-date">{{ formatDate(g.created_at) }}</span>
          <span class="history-model">{{ g.model }}</span>
          <span v-if="g.tokens_used" class="history-tokens">{{ g.tokens_used }} токенов</span>
          <span v-if="g.error" class="history-error">{{ g.error }}</span>
        </div>
      </div>

      <!-- Подтверждение удаления -->
      <div v-if="showDeleteConfirm" class="confirm-overlay" @click.self="showDeleteConfirm = false">
        <div class="confirm-dialog">
          <p>Удалить карусель «{{ carousel?.title }}»?</p>
          <p class="confirm-sub">Все слайды и данные будут утеряны.</p>
          <div class="confirm-actions">
            <button @click="showDeleteConfirm = false" class="btn btn-outline">Отмена</button>
            <button @click="deleteCarousel" class="btn btn-danger">Удалить</button>
          </div>
        </div>
      </div>

      <div v-if="slides.length === 0 && !generating" class="empty-state">
        <p>Слайдов пока нет. Нажмите «Сгенерировать слайды», чтобы создать контент с помощью AI.</p>
      </div>

      <div v-if="slides.length > 0" class="editor-layout">
        <div class="slides-nav">
          <button
            v-for="(s, i) in slides"
            :key="s.id"
            :class="['slide-thumb', i === currentSlide && 'active']"
            :draggable="true"
            @click="currentSlide = i"
            @dragstart="onDragStart(i)"
            @dragover="onDragOver"
            @drop="onDrop(i)"
          >
            <span class="thumb-num">{{ i + 1 }}</span>
            <span class="thumb-title">{{ s.title || 'Без названия' }}</span>
            <button class="thumb-del" @click.stop="removeSlide(i)" title="Удалить слайд">&times;</button>
          </button>
          <button class="slide-thumb add-slide" @click="addSlide">
            <span class="thumb-num">+</span>
            <span class="thumb-title">Добавить слайд</span>
          </button>
        </div>

        <div class="editor-center">
          <div class="preview-container">
            <div class="preview" :style="previewStyle">
              <div v-if="design.bg_dim > 0" class="preview-dim" :style="{ opacity: design.bg_dim }"></div>
              <div class="preview-content" :class="`tpl-${design.template}`">
                <div v-if="design.header_enabled && design.header_text" class="preview-header">
                  {{ design.header_text }}
                </div>
                <div class="preview-body" :style="previewBodyStyle">
                  <div class="preview-title">{{ currentSlideData?.title }}</div>
                  <div class="preview-text">{{ currentSlideData?.body }}</div>
                  <div v-if="currentSlideData?.footer" class="preview-footer-text">
                    {{ currentSlideData.footer }}
                  </div>
                </div>
                <div v-if="design.footer_enabled && design.footer_text" class="preview-footer">
                  {{ design.footer_text }}
                </div>
                <div class="preview-number">{{ currentSlide + 1 }}/{{ slides.length }}</div>
              </div>
            </div>
          </div>

          <div class="slide-editor">
            <div class="field">
              <label>Заголовок</label>
              <input v-if="currentSlideData" v-model="currentSlideData.title" class="input" @blur="saveSlide" />
            </div>
            <div class="field">
              <label>Текст</label>
              <textarea v-if="currentSlideData" v-model="currentSlideData.body" class="textarea" rows="4" @blur="saveSlide"></textarea>
            </div>
            <div class="field">
              <label>Подпись</label>
              <input v-if="currentSlideData" v-model="currentSlideData.footer" class="input" @blur="saveSlide" />
            </div>
            <div v-if="savingSlide" class="save-indicator">Сохранение...</div>
          </div>
        </div>

        <div class="editor-panel">
          <div class="panel-hint">Настройки для слайда {{ currentSlide + 1 }}</div>
          <div class="panel-tabs">
            <button :class="['ptab', activePanel === 'template' && 'ptab-active']" @click="activePanel = 'template'">Шаблон</button>
            <button :class="['ptab', activePanel === 'bg' && 'ptab-active']" @click="activePanel = 'bg'">Фон</button>
            <button :class="['ptab', activePanel === 'layout' && 'ptab-active']" @click="activePanel = 'layout'">Раскладка</button>
            <button :class="['ptab', activePanel === 'hf' && 'ptab-active']" @click="activePanel = 'hf'">Шапка/Подвал</button>
          </div>

          <div class="panel-body">
            <div v-if="activePanel === 'template'" class="panel-section">
              <div class="template-grid">
                <button
                  v-for="t in ['classic', 'bold', 'minimal']"
                  :key="t"
                  :class="['tpl-btn', design.template === t && 'tpl-active']"
                  @click="design.template = t; saveDesign()"
                >{{ templateNames[t] }}</button>
              </div>
            </div>

            <div v-if="activePanel === 'bg'" class="panel-section">
              <div class="field">
                <label>Цвет</label>
                <input type="color" v-model="design.bg_color" @change="saveDesign" class="color-input" />
              </div>
              <div class="field">
                <label>Изображение</label>
                <input type="file" accept="image/*" @change="uploadBg" :disabled="uploadingBg" class="file-input" />
                <span v-if="uploadingBg" class="upload-status">Загрузка...</span>
                <span v-else-if="design.bg_asset_id" class="upload-status upload-ok">Фон загружен</span>
                <button v-if="design.bg_asset_id" type="button" class="btn-remove-bg" @click="removeBg">Убрать фон</button>
              </div>
              <div class="field">
                <label>Затемнение: {{ design.bg_dim.toFixed(1) }}</label>
                <input type="range" v-model.number="design.bg_dim" min="0" max="0.7" step="0.1" @change="saveDesign" />
              </div>
            </div>

            <div v-if="activePanel === 'layout'" class="panel-section">
              <div class="field">
                <label>Отступы: {{ design.padding }}px</label>
                <input type="range" v-model.number="design.padding" min="10" max="100" step="5" @change="saveDesign" />
              </div>
              <div class="field">
                <label>По горизонтали</label>
                <div class="btn-group">
                  <button v-for="a in ['left','center','right']" :key="a"
                    :class="['gbtn', design.align_h === a && 'gbtn-active']"
                    @click="design.align_h = a; saveDesign()">{{ alignHLabels[a] }}</button>
                </div>
              </div>
              <div class="field">
                <label>По вертикали</label>
                <div class="btn-group">
                  <button v-for="a in ['top','center','bottom']" :key="a"
                    :class="['gbtn', design.align_v === a && 'gbtn-active']"
                    @click="design.align_v = a; saveDesign()">{{ alignVLabels[a] }}</button>
                </div>
              </div>
            </div>

            <div v-if="activePanel === 'hf'" class="panel-section">
              <div class="field">
                <label>
                  <input type="checkbox" v-model="design.header_enabled" @change="saveDesign" />
                  Показать шапку
                </label>
                <input v-if="design.header_enabled" v-model="design.header_text" class="input" placeholder="Текст шапки" @blur="saveDesign" />
              </div>
              <div class="field">
                <label>
                  <input type="checkbox" v-model="design.footer_enabled" @change="saveDesign" />
                  Показать подвал
                </label>
                <input v-if="design.footer_enabled" v-model="design.footer_text" class="input" placeholder="Текст подвала" @blur="saveDesign" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.editor-page { max-width: 100%; }

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-link {
  font-size: 22px;
  text-decoration: none;
  color: var(--text-secondary);
  line-height: 1;
}

.editor-toolbar h2 { font-size: 22px; font-weight: 700; }

.toolbar-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.info-bar {
  background: #fff8e6; color: #856404; padding: 10px 16px;
  border-radius: 8px; margin-bottom: 12px; font-size: 14px;
}

.success-bar {
  background: #e6f9ed; color: #155724; padding: 10px 16px;
  border-radius: 8px; margin-bottom: 12px; font-size: 14px;
}

.download-link { font-weight: 600; text-decoration: underline; }

.error-bar {
  background: #fff0f0; color: var(--danger); padding: 10px 16px;
  border-radius: 8px; margin-bottom: 12px; font-size: 14px;
  display: flex; justify-content: space-between; align-items: center;
}

.error-close {
  background: none; border: none; font-size: 20px; cursor: pointer;
  color: inherit; line-height: 1; padding: 0 4px;
}

.empty-state {
  text-align: center; padding: 80px 20px;
  color: var(--text-secondary); font-size: 16px;
}

/* История генераций */
.history-panel {
  background: var(--card); border-radius: var(--radius); padding: 16px;
  margin-bottom: 16px; box-shadow: var(--shadow);
}

.history-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}

.history-header h3 { font-size: 16px; font-weight: 600; }

.history-empty { color: var(--text-secondary); font-size: 14px; }

.history-item {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 0; border-bottom: 1px solid var(--border);
  font-size: 13px; flex-wrap: wrap;
}

.history-item:last-child { border-bottom: none; }

.history-status {
  padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600;
}

.st-done { background: #e6f9ed; color: #155724; }
.st-failed { background: #fff0f0; color: #c0392b; }
.st-queued, .st-running { background: #fff8e6; color: #856404; }

.history-date { color: var(--text-secondary); }
.history-model { color: var(--text-secondary); font-style: italic; }
.history-tokens { font-weight: 500; }
.history-error { color: var(--danger); font-size: 12px; }

/* Подтверждение удаления */
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

/* Редактор */
.editor-layout {
  display: grid; grid-template-columns: 180px 1fr 260px; gap: 16px; align-items: start;
}

.slides-nav { display: flex; flex-direction: column; gap: 6px; }

.slide-thumb {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  border: 1px solid var(--border); border-radius: 8px;
  background: var(--card); font-size: 13px; text-align: left;
  transition: all 0.2s; cursor: grab; position: relative;
}

.slide-thumb.active { border-color: var(--accent); background: #f0f7ff; }

.slide-thumb:hover .thumb-del { opacity: 1; }

.add-slide {
  border-style: dashed; color: var(--text-secondary); cursor: pointer;
}

.add-slide:hover { border-color: var(--accent); color: var(--accent); }

.thumb-num {
  background: var(--bg); width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; flex-shrink: 0;
}

.thumb-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }

.thumb-del {
  opacity: 0; background: none; border: none; font-size: 18px;
  color: var(--danger); cursor: pointer; padding: 0 2px; line-height: 1;
  transition: opacity .2s;
}

.editor-center { display: flex; flex-direction: column; gap: 16px; }

.preview-container { display: flex; justify-content: center; }

.preview {
  width: 100%; max-width: 432px; aspect-ratio: 4/5;
  border-radius: 8px; box-shadow: var(--shadow-lg); position: relative;
  overflow: hidden; display: flex; flex-direction: column;
}

.preview-dim {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: #000; pointer-events: none;
}

.preview-content {
  position: relative; z-index: 1; flex: 1;
  display: flex; flex-direction: column; padding: 16px;
}

.preview-header { font-size: 11px; opacity: 0.6; margin-bottom: 8px; }
.preview-body { flex: 1; display: flex; flex-direction: column; }

.preview-title {
  font-size: 20px; font-weight: 700; margin-bottom: 12px; line-height: 1.2;
}

.preview-text { font-size: 14px; line-height: 1.5; color: #444; }

.preview-footer-text {
  font-size: 12px; color: #888; margin-top: 12px; font-style: italic;
}

.preview-footer { font-size: 11px; opacity: 0.5; margin-top: auto; }

.preview-number {
  position: absolute; bottom: 8px; right: 12px; font-size: 10px; opacity: 0.4;
}

.tpl-bold .preview-title {
  font-weight: 900; color: #1a1a2e;
}
.tpl-bold .preview-text { font-weight: 700; color: #1a1a2e; }
.tpl-bold .preview-footer-text { font-weight: 700; color: #333; }
.tpl-minimal .preview-title { font-weight: 300; font-size: 20px; }
.tpl-minimal .preview-text { font-weight: 300; line-height: 1.7; }

.slide-editor {
  background: var(--card); border-radius: var(--radius);
  padding: 16px; box-shadow: var(--shadow);
}

.field { margin-bottom: 14px; }

.field label {
  display: block; font-size: 13px; font-weight: 500;
  margin-bottom: 4px; color: var(--text-secondary);
}

.input, .textarea {
  width: 100%; padding: 8px 12px; border: 1px solid var(--border);
  border-radius: 6px; font-size: 14px; font-family: inherit; background: var(--bg);
}
.textarea { resize: vertical; }
.input:focus, .textarea:focus { outline: none; border-color: var(--accent); }

.save-indicator { font-size: 12px; color: var(--text-secondary); }

.editor-panel {
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden;
}

.panel-hint {
  font-size: 12px; color: var(--text-secondary); padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.panel-tabs {
  display: flex; border-bottom: 1px solid var(--border); overflow-x: auto;
}

.ptab {
  padding: 10px 12px; border: none; background: none;
  font-size: 12px; font-weight: 500; color: var(--text-secondary);
  white-space: nowrap; border-bottom: 2px solid transparent; transition: all 0.2s;
}

.ptab-active { color: var(--accent); border-bottom-color: var(--accent); }

.panel-body { padding: 16px; }
.panel-section .field { margin-bottom: 16px; }
.template-grid { display: flex; flex-direction: column; gap: 8px; }

.tpl-btn {
  padding: 12px; border: 2px solid var(--border); border-radius: 8px;
  background: var(--bg); font-size: 14px; font-weight: 500; transition: all 0.2s;
}

.tpl-active { border-color: var(--accent); background: #f0f7ff; }

.color-input {
  width: 60px; height: 36px; border: 1px solid var(--border);
  border-radius: 6px; cursor: pointer;
}

.file-input { font-size: 13px; display: block; margin-top: 4px; }
.upload-status { font-size: 12px; color: var(--text-secondary); display: block; margin-top: 4px; }
.upload-ok { color: #34c759; }
.btn-remove-bg { margin-top: 8px; padding: 4px 10px; font-size: 12px; background: #fff0f0; color: #c0392b; border: 1px solid #f0d0d0; border-radius: 6px; cursor: pointer; }
.btn-remove-bg:hover { background: #ffe0e0; }

.btn-group {
  display: flex; gap: 0; border: 1px solid var(--border);
  border-radius: 6px; overflow: hidden;
}

.gbtn {
  flex: 1; padding: 6px 8px; border: none; background: var(--card);
  font-size: 12px; transition: all 0.2s;
}

.gbtn-active { background: var(--accent); color: white; }

.btn {
  display: inline-flex; align-items: center; padding: 8px 18px;
  border: none; border-radius: 8px; font-size: 14px;
  font-weight: 600; transition: all 0.2s; text-decoration: none; cursor: pointer;
}

.btn-sm { padding: 6px 14px; font-size: 13px; }

.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.6; }

.btn-outline {
  background: transparent; border: 1px solid var(--border); color: var(--text);
}
.btn-outline:hover:not(:disabled) { background: var(--bg); }

.btn-danger { background: #e74c3c; color: white; }
.btn-danger:hover { background: #c0392b; }

.loading {
  text-align: center; padding: 60px; color: var(--text-secondary);
}

@media (max-width: 900px) {
  .editor-layout { grid-template-columns: 1fr; }
  .slides-nav { flex-direction: row; overflow-x: auto; padding-bottom: 8px; }
  .slide-thumb { min-width: 100px; }
}

@media (max-width: 640px) {
  .toolbar-actions { flex-wrap: wrap; }
}
</style>
