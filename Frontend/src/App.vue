<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  getOptions,
  analyze,
  getExamples,
  getExamplesSummary
} from './api'

import AnalysisForm from './components/AnalysisForm.vue'
import SummaryCards from './components/SummaryCards.vue'
import AnalysisChart from './components/AnalysisChart.vue'
import ModeDescription from './components/ModeDescription.vue'
import FooterCredits from './components/FooterCredits.vue'

const loadingOptions = ref(false)
const loadingAnalysis = ref(false)
const loadingExamples = ref(false)

const error = ref('')

const options = ref(null)
const result = ref(null)

const selectedChartSelection = ref(null)
const selectedChartLabel = ref('')

const authorSummary = ref([])
const selectedAuthor = ref(null)

const examples = ref([])
const examplesTotal = ref(0)
const examplesOffset = ref(0)

const EXAMPLES_LIMIT = 10

const form = ref({
  lemma: '',
  metric: '',
  metric_min: null,
  metric_max: null,
  authors: [],
  documents: [],
  genres: [],
  year_from: null,
  year_to: null,

  graph_mode: 'distribution',
  group_by: 'none',
  entity_type: 'author'
})

onMounted(async () => {
  loadingOptions.value = true
  error.value = ''

  try {
    options.value = await getOptions()

    if (options.value.metrics.length > 0) {
      form.value.metric = options.value.metrics[0].name
    }

    if (options.value.year_min) {
      form.value.year_from = options.value.year_min
    }

    if (options.value.year_max) {
      form.value.year_to = options.value.year_max
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loadingOptions.value = false
  }
})

const selectedMetricLabel = computed(() => {
  if (!options.value) {
    return ''
  }

  const metric = options.value.metrics.find(
    item => item.name === form.value.metric
  )

  return metric ? metric.label : form.value.metric
})

const chartTitle = computed(() => {
  if (!result.value) {
    return ''
  }

  if (result.value.chart_type === 'histogram') {
    return 'Распределение значений метрики'
  }

  if (result.value.chart_type === 'bar') {
    return 'Сравнение по группам'
  }

  if (result.value.chart_type === 'line') {
    return 'Динамика по десятилетиям'
  }

  if (result.value.chart_type === 'entity_timeline') {
    return 'Объекты во времени'
  }

  return 'График'
})

const shouldShowAuthorSummary = computed(() => {
  if (form.value.graph_mode === 'entity_timeline') {
    return form.value.entity_type === 'genre'
  }

  return ['none', 'genre', 'decade', 'year'].includes(form.value.group_by)
})
const hasExamplesBlock = computed(() => {
  return (
    selectedChartSelection.value ||
    loadingExamples.value ||
    authorSummary.value.length > 0 ||
    selectedAuthor.value ||
    examples.value.length > 0
  )
})

const canLoadPreviousPage = computed(() => {
  return examplesOffset.value > 0
})

const canLoadNextPage = computed(() => {
  return examplesOffset.value + EXAMPLES_LIMIT < examplesTotal.value
})

function buildBasePayload() {
  return {
    lemma: form.value.lemma ? form.value.lemma.trim() : null,
    metric: form.value.metric,
    metric_min: form.value.metric_min === '' ? null : form.value.metric_min,
    metric_max: form.value.metric_max === '' ? null : form.value.metric_max,
    authors: form.value.authors,
    documents: form.value.documents,
    genres: form.value.genres,
    year_from: form.value.year_from === '' ? null : form.value.year_from,
    year_to: form.value.year_to === '' ? null : form.value.year_to,

    graph_mode: form.value.graph_mode,
    group_by: form.value.group_by,
    entity_type: form.value.entity_type
  }
}

function getChartLabel(selection) {
  const item = selection?.item

  if (!item) {
    return ''
  }

  if (selection?.chart_type === 'entity_timeline') {
    return [item.entity_name, item.period].filter(Boolean).join(' — ')
  }

  return item.label || item.group || item.period || ''
}

function buildSelectionPayload(selection) {
  const item = selection?.item || {}

  const payload = {
    ...buildBasePayload(),

    selected_value: null,
    bin_start: null,
    bin_end: null,
    group_value: null,
    decade: null,
    target_value: null,

    entity_type: null,
    entity_id: null,
    entity_name: null,

    selection: {
      label: item.label || null,
      value: null,
      bin_start: null,
      bin_end: null,
      group: null,
      group_id: null,
      decade: null,

      entity_type: null,
      entity_id: null,
      entity_name: null,
      target_value: null
    }
  }

  if (selection?.chart_type === 'histogram') {
    if (item.value !== undefined && item.value !== null) {
      payload.selected_value = item.value
      payload.selection.value = item.value
    } else {
      payload.bin_start = item.bin_start
      payload.bin_end = item.bin_end
      payload.selection.bin_start = item.bin_start
      payload.selection.bin_end = item.bin_end
    }
  }

  if (selection?.chart_type === 'bar') {
    payload.group_value = item.group || null
    payload.selection.group = item.group || null
    payload.selection.group_id =
      item.group_id ||
      item.author_id ||
      item.doc_id ||
      null
  }

  if (selection?.chart_type === 'line') {
    payload.decade = item.decade
    payload.selection.decade = item.decade
  }

  if (selection?.chart_type === 'entity_timeline') {
    payload.entity_type = item.entity_type || form.value.entity_type
    payload.entity_id = item.entity_id || null
    payload.entity_name = item.entity_name || null
    payload.decade = item.decade || null
    payload.target_value =
      item.mean !== undefined && item.mean !== null
        ? Number(item.mean)
        : null

    payload.selection.entity_type = payload.entity_type
    payload.selection.entity_id = payload.entity_id
    payload.selection.entity_name = payload.entity_name
    payload.selection.decade = payload.decade
    payload.selection.target_value = payload.target_value
  }

  if (
    selection?.chart_type !== 'histogram' &&
    selection?.chart_type !== 'entity_timeline' &&
    item.mean !== undefined &&
    item.mean !== null
  ) {
    payload.target_value = Number(item.mean)
  }

  return payload
}

function resetExamplesState() {
  selectedChartSelection.value = null
  selectedChartLabel.value = ''
  authorSummary.value = []
  selectedAuthor.value = null
  examples.value = []
  examplesTotal.value = 0
  examplesOffset.value = 0
}

function normalizeAuthor(author) {
  return {
    author_id: author.author_id || author.id || null,
    author_name: author.author_name || author.name || 'Автор не указан',
    count: author.count || author.examples_count || 0,
    year_min: author.year_min || null,
    year_max: author.year_max || null,
    mean: author.mean ?? null
  }
}

function normalizeSummaryResponse(response) {
  let items = []

  if (Array.isArray(response)) {
    items = response
  } else {
    items = response.items || response.summary || response.authors || []
  }

  return items.map(normalizeAuthor)
}

function normalizeExamplesResponse(response) {
  return {
    items: response.items || response.examples || [],
    total: response.total || response.count || 0,
    offset: response.offset || 0
  }
}

function getExampleText(example) {
  return example.text || example.sentence_text || example.sent_text || ''
}

function isAuthorOpen(author) {
  if (!selectedAuthor.value) {
    return false
  }

  const currentId = selectedAuthor.value.author_id
  const authorId = author.author_id || author.id || null

  if (currentId !== null && authorId !== null) {
    return currentId === authorId
  }

  return selectedAuthor.value.author_name === (author.author_name || author.name)
}

async function runAnalysis() {
  error.value = ''
  result.value = null
  resetExamplesState()
  loadingAnalysis.value = true

  try {
    result.value = await analyze(buildBasePayload())
  } catch (e) {
    error.value = e.message
  } finally {
    loadingAnalysis.value = false
  }
}

async function handleChartSelect(selection) {
  if (!result.value || !selection || !selection.item) {
    return
  }

  error.value = ''
  resetExamplesState()

  selectedChartSelection.value = selection
  selectedChartLabel.value = getChartLabel(selection)

  if (shouldShowAuthorSummary.value) {
    await loadAuthorSummary(selection)
  } else {
    await loadExamplesDirect(selection)
  }
}

async function loadAuthorSummary(selection) {
  loadingExamples.value = true

  try {
    const payload = buildSelectionPayload(selection)
    const response = await getExamplesSummary(payload)
    authorSummary.value = normalizeSummaryResponse(response)
  } catch (e) {
    error.value = e.message
  } finally {
    loadingExamples.value = false
  }
}

async function loadExamplesDirect(selection) {
  const item = selection.item

  if (selection.chart_type === 'entity_timeline') {
    selectedAuthor.value = {
      author_id: item.entity_type === 'author' ? item.entity_id : null,
      author_name: item.entity_name || 'Выбранный объект',
      count: item.count || null,
      year_min: item.year_min || null,
      year_max: item.year_max || null,
      mean: item.mean ?? null
    }

    await loadExamplesForCurrentSelection(0)
    return
  }

  const isAuthorGroup = form.value.group_by === 'author'

  selectedAuthor.value = {
    author_id: isAuthorGroup
      ? item.group_id || item.author_id || null
      : null,
    author_name: item.group || 'Выбранная группа',
    count: item.count || null,
    year_min: item.year_min || null,
    year_max: item.year_max || null,
    mean: item.mean ?? null
  }

  await loadExamplesForCurrentSelection(0)
}

async function selectAuthor(author) {
  selectedAuthor.value = normalizeAuthor(author)
  await loadExamplesForCurrentSelection(0)
}

async function loadExamplesForCurrentSelection(offset = 0) {
  if (!selectedChartSelection.value) {
    return
  }

  loadingExamples.value = true
  examples.value = []

  try {
    const payload = {
      ...buildSelectionPayload(selectedChartSelection.value),
      author_id: selectedAuthor.value?.author_id || null,
      limit: EXAMPLES_LIMIT,
      offset
    }

    const response = await getExamples(payload)
    const normalized = normalizeExamplesResponse(response)

    examples.value = normalized.items
    examplesTotal.value = normalized.total
    examplesOffset.value = normalized.offset
  } catch (e) {
    error.value = e.message
  } finally {
    loadingExamples.value = false
  }
}

async function loadPreviousExamplesPage() {
  const newOffset = Math.max(0, examplesOffset.value - EXAMPLES_LIMIT)
  await loadExamplesForCurrentSelection(newOffset)
}

async function loadNextExamplesPage() {
  const newOffset = examplesOffset.value + EXAMPLES_LIMIT
  await loadExamplesForCurrentSelection(newOffset)
}

function resetForm() {
  form.value.lemma = ''
  form.value.metric_min = null
  form.value.metric_max = null
  form.value.authors = []
  form.value.documents = []
  form.value.genres = []

  if (options.value) {
    form.value.year_from = options.value.year_min
    form.value.year_to = options.value.year_max
  }

  form.value.graph_mode = 'distribution'
  form.value.group_by = 'none'
  form.value.entity_type = 'author'

  result.value = null
  resetExamplesState()
  error.value = ''
}
</script>

<template>
  <v-app>
    <v-main>
      <v-container class="py-8" style="max-width: 1200px;">
        <v-card
          class="pa-6 mb-6 page-hero"
          style="background-color: rgb(55, 75, 155); color: white;"
        >
          <h1
            class="text-h4 mb-2"
            style="color: white;"
          >
            Синтаксический анализ корпуса
          </h1>
        </v-card>

        <v-alert
          v-if="error"
          type="error"
          class="mb-6"
        >
          {{ error }}
        </v-alert>

        <v-card
          v-if="loadingOptions"
          class="pa-6 mb-6"
          rounded="lg"
        >
          <v-progress-circular indeterminate />
          <span class="ml-3">Загрузка параметров...</span>
        </v-card>

        <AnalysisForm
          v-if="options"
          :form="form"
          :options="options"
          :loading-analysis="loadingAnalysis"
          @analyze="runAnalysis"
          @reset="resetForm"
        />

        <v-card
          v-if="result"
          class="pa-6 mb-6"
          rounded="lg"
        >
          <h2 class="text-h6 mb-4">
            Результаты
          </h2>

          <SummaryCards :summary="result.summary" />

          <v-divider class="my-6" />

          <h3 class="text-subtitle-1 mb-4">
            {{ chartTitle }}: {{ selectedMetricLabel }}
          </h3>

          <p class="text-body-2 mb-4 examples-help">
            Нажмите на столбец или точку графика, чтобы посмотреть примеры предложений из выбранного фрагмента.
          </p>

          <AnalysisChart
            :result="result"
            :metric-label="selectedMetricLabel"
            @select="handleChartSelect"
          />

          <v-card
            v-if="hasExamplesBlock"
            class="pa-4 mt-6 examples-block"
            variant="tonal"
            rounded="lg"
          >
            <h3 class="text-subtitle-1 mb-3">
              Примеры
              <span v-if="selectedChartLabel">
                — {{ selectedMetricLabel }}: {{ selectedChartLabel }}
              </span>
            </h3>

            <v-progress-linear
              v-if="loadingExamples && !selectedAuthor"
              indeterminate
              class="mb-4"
            />

            <template v-if="shouldShowAuthorSummary && authorSummary.length">
              <p class="text-body-2 mb-3">
                Показана сводка по авторам. Нажмите на автора, чтобы раскрыть примеры предложений.
                Для сгруппированных графиков примеры отсортированы по близости к среднему значению выбранной группы.
              </p>

              <div class="author-summary-list">
                <v-card
                  v-for="author in authorSummary"
                  :key="author.author_id || author.author_name"
                  class="pa-3 mb-3 author-summary-card"
                  variant="flat"
                  rounded="lg"
                >
                  <div
                    class="author-summary-header"
                    @click="selectAuthor(author)"
                  >
                    <div>
                      <div class="author-summary-title">
                        {{ author.author_name }}
                        — {{ Number(author.count).toLocaleString('ru-RU') }} примеров
                      </div>

                      <div class="author-summary-subtitle">
                        <span v-if="author.year_min && author.year_max">
                          {{ author.year_min }}–{{ author.year_max }}
                        </span>

                        <span v-else>
                          период не указан
                        </span>

                        <span v-if="author.mean !== null && author.mean !== undefined">
                          · среднее значение: {{ Number(author.mean).toFixed(3) }}
                        </span>
                      </div>
                    </div>

                    <v-icon>
                      {{ isAuthorOpen(author) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                    </v-icon>
                  </div>

                  <div
                    v-if="isAuthorOpen(author)"
                    class="author-examples mt-4"
                  >
                    <v-progress-linear
                      v-if="loadingExamples"
                      indeterminate
                      class="mb-4"
                    />

                    <div v-if="examples.length">
                      <v-card
                        v-for="example in examples"
                        :key="example.sentence_id"
                        class="pa-4 mb-3"
                        variant="tonal"
                        rounded="lg"
                      >
                        <p class="text-body-2 mb-2 example-text">
                          {{ getExampleText(example) }}
                        </p>

                        <p class="text-caption text-medium-emphasis">
                          {{ example.author_name }}
                          <span v-if="example.title"> — {{ example.title }}</span>
                          <span v-if="example.year">, {{ example.year }}</span>
                          <span v-if="example.genre">, {{ example.genre }}</span>
                          <span v-if="example.metric_value !== undefined">
                            | {{ selectedMetricLabel }}: {{ example.metric_value }}
                          </span>
                        </p>
                      </v-card>

                      <div class="d-flex ga-3 mt-4">
                        <v-btn
                          variant="outlined"
                          :disabled="!canLoadPreviousPage || loadingExamples"
                          @click.stop="loadPreviousExamplesPage"
                        >
                          Предыдущая страница
                        </v-btn>

                        <v-btn
                          color="primary"
                          :disabled="!canLoadNextPage || loadingExamples"
                          @click.stop="loadNextExamplesPage"
                        >
                          Следующая страница
                        </v-btn>
                      </div>
                    </div>

                    <v-alert
                      v-else-if="!loadingExamples"
                      type="info"
                      variant="tonal"
                    >
                      Для выбранного автора примеры не найдены.
                    </v-alert>
                  </div>
                </v-card>
              </div>
            </template>

            <template v-if="!shouldShowAuthorSummary && selectedAuthor">
              <v-divider class="my-4" />

              <h4 class="text-subtitle-2 mb-3">
                {{ selectedAuthor.author_name }}
                <span v-if="examplesTotal">
                  — {{ Number(examplesTotal).toLocaleString('ru-RU') }} примеров
                </span>
              </h4>

              <p
                v-if="selectedChartSelection && selectedChartSelection.chart_type !== 'histogram'"
                class="text-body-2 mb-3"
              >
                Показаны предложения, значения метрики которых ближе всего к среднему значению выбранной группы.
              </p>

              <v-progress-linear
                v-if="loadingExamples"
                indeterminate
                class="mb-4"
              />

              <div
                v-if="examples.length"
                class="examples-list"
              >
                <v-card
                  v-for="example in examples"
                  :key="example.sentence_id"
                  class="pa-4 mb-3"
                  variant="flat"
                  rounded="lg"
                >
                  <p class="text-body-2 mb-2 example-text">
                    {{ getExampleText(example) }}
                  </p>

                  <p class="text-caption text-medium-emphasis">
                    {{ example.author_name }}
                    <span v-if="example.title"> — {{ example.title }}</span>
                    <span v-if="example.year">, {{ example.year }}</span>
                    <span v-if="example.genre">, {{ example.genre }}</span>
                    <span v-if="example.metric_value !== undefined">
                      | {{ selectedMetricLabel }}: {{ example.metric_value }}
                    </span>
                  </p>
                </v-card>

                <div class="d-flex ga-3 mt-4">
                  <v-btn
                    variant="outlined"
                    :disabled="!canLoadPreviousPage || loadingExamples"
                    @click="loadPreviousExamplesPage"
                  >
                    Предыдущая страница
                  </v-btn>

                  <v-btn
                    color="primary"
                    :disabled="!canLoadNextPage || loadingExamples"
                    @click="loadNextExamplesPage"
                  >
                    Следующая страница
                  </v-btn>
                </div>
              </div>

              <v-alert
                v-else-if="!loadingExamples"
                type="info"
                variant="tonal"
              >
                Для выбранной группы примеры не найдены.
              </v-alert>
            </template>

            <v-alert
              v-if="!loadingExamples && shouldShowAuthorSummary && selectedChartSelection && !authorSummary.length"
              type="info"
              variant="tonal"
            >
              Для выбранного фрагмента графика авторы не найдены.
            </v-alert>
          </v-card>
        </v-card>

        <ModeDescription />

        <FooterCredits />
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
.examples-help,
.examples-block,
.examples-list {
  text-align: left;
}

.author-summary-list {
  text-align: left;
}

.author-summary-card {
  border: 1px solid rgba(29, 181, 232, 0.18);
}

.author-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  cursor: pointer;
}

.author-summary-title {
  font-weight: 600;
  color: #1F2937;
}

.author-summary-subtitle {
  margin-top: 4px;
  font-size: 14px;
  color: #6B7280;
}

.author-examples {
  border-top: 1px solid rgba(29, 181, 232, 0.18);
  padding-top: 16px;
}

.example-text {
  line-height: 1.6;
}
</style>