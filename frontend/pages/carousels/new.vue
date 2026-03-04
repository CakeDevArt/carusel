<script setup lang="ts">
const api = useApi()
const router = useRouter()

const sourceType = ref<'text' | 'video'>('text')
const title = ref('')
const sourceText = ref('')
const videoLink = ref('')
const videoAssetId = ref('')
const slidesCount = ref(6)
const language = ref('ru')
const styleHint = ref('')
const saving = ref(false)
const error = ref('')

async function uploadVideo(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const fd = new FormData()
  fd.append('file', input.files[0])
  try {
    const res = await api.upload<any>('/assets/upload', fd)
    videoAssetId.value = res.id
  } catch (err: any) {
    error.value = err.message
  }
}

async function save() {
  if (!title.value.trim()) {
    error.value = 'Название обязательно'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload: any = {}
    if (sourceType.value === 'text') {
      payload.text = sourceText.value
    } else {
      payload.video_link = videoLink.value
      if (videoAssetId.value) payload.asset_id = videoAssetId.value
    }

    const carousel = await api.post('/carousels', {
      title: title.value,
      source_type: sourceType.value,
      source_payload: payload,
      format: {
        slides_count: slidesCount.value,
        language: language.value,
        style_hint: styleHint.value || null,
      },
    })
    router.push(`/carousels/${carousel.id}/editor`)
  } catch (err: any) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>Создать карусель</h1>

    <div class="form-section">
      <label class="label">Название</label>
      <input v-model="title" class="input" placeholder="Моя крутая карусель" />
    </div>

    <div class="form-section">
      <label class="label">Источник</label>
      <div class="tabs">
        <button
          :class="['tab', sourceType === 'text' && 'tab-active']"
          @click="sourceType = 'text'"
        >Текст</button>
        <button
          :class="['tab', sourceType === 'video' && 'tab-active']"
          @click="sourceType = 'video'"
        >Видео</button>
      </div>

      <div v-if="sourceType === 'text'" class="source-input">
        <textarea v-model="sourceText" class="textarea" rows="8"
          placeholder="Вставьте текст для генерации слайдов..."></textarea>
      </div>

      <div v-else class="source-input">
        <input v-model="videoLink" class="input" placeholder="Ссылка на видео (необязательно)" />
        <div class="upload-area">
          <label class="upload-label">
            <input type="file" accept="video/*" @change="uploadVideo" class="upload-input" />
            <span>{{ videoAssetId ? 'Видео загружено' : 'Загрузить видеофайл' }}</span>
          </label>
        </div>
      </div>
    </div>

    <div class="form-section">
      <label class="label">Формат</label>
      <div class="form-row">
        <div class="form-field">
          <label class="label-sm">Кол-во слайдов</label>
          <select v-model.number="slidesCount" class="select">
            <option v-for="n in [6,7,8,9,10]" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
        <div class="form-field">
          <label class="label-sm">Язык</label>
          <select v-model="language" class="select">
            <option value="ru">Русский</option>
            <option value="en">Английский</option>
          </select>
        </div>
      </div>
    </div>

    <div class="form-section">
      <label class="label">Пример стиля (необязательно)</label>
      <textarea v-model="styleHint" class="textarea" rows="3"
        placeholder="Вставьте пример поста, стиль которого хотите повторить..."></textarea>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="form-actions">
      <NuxtLink to="/carousels" class="btn btn-ghost">Отмена</NuxtLink>
      <button @click="save" :disabled="saving" class="btn btn-primary">
        {{ saving ? 'Сохранение...' : 'Сохранить и открыть редактор' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 700px; }

h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 28px;
}

.form-section {
  margin-bottom: 24px;
}

.label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}

.label-sm {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--text-secondary);
}

.input, .textarea, .select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--card);
  color: var(--text);
  font-family: inherit;
}

.textarea {
  resize: vertical;
}

.input:focus, .textarea:focus, .select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0,113,227,0.1);
}

.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: var(--card);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.tab-active {
  background: var(--accent);
  color: white;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-field {
  flex: 1;
}

.upload-area {
  margin-top: 12px;
}

.upload-label {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 2px dashed var(--border);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: border-color 0.2s;
}

.upload-label:hover {
  border-color: var(--accent);
}

.upload-input {
  display: none;
}

.error {
  background: #fff0f0;
  color: var(--danger);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
}

.btn {
  display: inline-flex;
  align-items: center;
  padding: 10px 24px;
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

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg);
}

@media (max-width: 640px) {
  .form-row {
    flex-direction: column;
  }
}
</style>
