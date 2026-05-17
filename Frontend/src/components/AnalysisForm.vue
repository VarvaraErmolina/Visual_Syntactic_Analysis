<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  form: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    required: true
  },
  loadingAnalysis: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['analyze', 'reset'])

const graphModeOptions = computed(() => {
  return props.options.graph_mode_options || [
    { name: 'distribution', label: 'Распределение' },
    { name: 'grouped_mean', label: 'Средние по группам' },
    { name: 'entity_timeline', label: 'Объекты во времени' }
  ]
})

const groupByOptions = computed(() => {
  return (props.options.group_by_options || []).filter(
    item => item.name !== 'none'
  )
})

const entityTypeOptions = computed(() => {
  return props.options.entity_type_options || [
    { name: 'author', label: 'Авторы' },
    { name: 'genre', label: 'Жанры' },
    { name: 'document', label: 'Произведения' }
  ]
})

watch(
  () => props.form.graph_mode,
  (newMode) => {
    if (newMode === 'distribution') {
      props.form.group_by = 'none'
    }

    if (newMode === 'grouped_mean') {
      if (!props.form.group_by || props.form.group_by === 'none') {
        props.form.group_by = 'author'
      }
    }

    if (newMode === 'entity_timeline') {
      props.form.group_by = 'none'

      if (!props.form.entity_type) {
        props.form.entity_type = 'author'
      }
    }
  }
)
</script>

<template>
  <v-card class="pa-6 mb-6" rounded="lg">
    <h2 class="text-h6 mb-4">
      Параметры анализа
    </h2>

    <v-row>
      <v-col cols="12" md="4">
        <v-text-field
          v-model="props.form.lemma"
          label="Лемма"
          placeholder="например: быть"
          variant="outlined"
          clearable
        />
      </v-col>

      <v-col cols="12" md="4">
        <v-select
          v-model="props.form.metric"
          label="Метрика"
          :items="props.options.metrics"
          item-title="label"
          item-value="name"
          variant="outlined"
        />
      </v-col>

      <v-col cols="12" md="4">
        <v-select
          v-model="props.form.graph_mode"
          label="Режим графика"
          :items="graphModeOptions"
          item-title="label"
          item-value="name"
          variant="outlined"
        />
      </v-col>
    </v-row>

    <v-row v-if="props.form.graph_mode !== 'distribution'">
      <v-col
        v-if="props.form.graph_mode === 'grouped_mean'"
        cols="12"
        md="4"
      >
        <v-select
          v-model="props.form.group_by"
          label="Группировать по"
          :items="groupByOptions"
          item-title="label"
          item-value="name"
          variant="outlined"
        />
      </v-col>

      <v-col
        v-if="props.form.graph_mode === 'entity_timeline'"
        cols="12"
        md="4"
      >
        <v-select
          v-model="props.form.entity_type"
          label="Объект на графике"
          :items="entityTypeOptions"
          item-title="label"
          item-value="name"
          variant="outlined"
        />
      </v-col>

      <v-col
        v-if="props.form.graph_mode === 'entity_timeline'"
        cols="12"
        md="8"
      >
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="3">
        <v-text-field
          v-model.number="props.form.metric_min"
          label="Значение метрики от"
          type="number"
          variant="outlined"
          clearable
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-text-field
          v-model.number="props.form.metric_max"
          label="Значение метрики до"
          type="number"
          variant="outlined"
          clearable
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-text-field
          v-model.number="props.form.year_from"
          label="Год от"
          type="number"
          variant="outlined"
          clearable
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-text-field
          v-model.number="props.form.year_to"
          label="Год до"
          type="number"
          variant="outlined"
          clearable
        />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <h2 class="text-subtitle-1 mb-4">
      Фильтры
    </h2>

    <v-row>
      <v-col cols="12" md="4">
        <v-autocomplete
          v-model="props.form.authors"
          label="Авторы"
          :items="props.options.authors"
          item-title="name"
          item-value="id"
          variant="outlined"
          multiple
          chips
          clearable
        />
      </v-col>

      <v-col cols="12" md="4">
        <v-autocomplete
          v-model="props.form.documents"
          label="Произведения"
          :items="props.options.documents"
          item-title="title"
          item-value="id"
          variant="outlined"
          multiple
          chips
          clearable
        />
      </v-col>

      <v-col cols="12" md="4">
        <v-autocomplete
          v-model="props.form.genres"
          label="Жанры"
          :items="props.options.genres"
          variant="outlined"
          multiple
          chips
          clearable
        />
      </v-col>
    </v-row>

    <div class="d-flex ga-3 mt-4">
      <v-btn
        color="primary"
        size="large"
        :loading="loadingAnalysis"
        @click="emit('analyze')"
      >
        Анализировать
      </v-btn>

      <v-btn
        variant="outlined"
        size="large"
        @click="emit('reset')"
      >
        Сбросить
      </v-btn>
    </div>
  </v-card>
</template>