<script setup>
defineProps({
  summary: {
    type: Object,
    required: true
  }
})

function formatNumber(value, digits = 3) {
  if (value === null || value === undefined) {
    return '—'
  }

  const number = Number(value)

  if (Number.isNaN(number)) {
    return '—'
  }

  return number.toFixed(digits)
}

function formatInteger(value) {
  if (value === null || value === undefined) {
    return '—'
  }

  return Number(value).toLocaleString('ru-RU')
}
</script>

<template>
  <v-row class="mb-4">
    <v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Предложений</div>
        <div class="text-h5">
          {{ formatInteger(summary.sentences_count) }}
        </div>
      </v-card>
    </v-col>

    <v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Авторов</div>
        <div class="text-h5">
          {{ formatInteger(summary.authors_count) }}
        </div>
      </v-card>
    </v-col>

    <v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Произведений</div>
        <div class="text-h5">
          {{ formatInteger(summary.documents_count) }}
        </div>
      </v-card>
    </v-col>

    <v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Среднее значение</div>
        <div class="text-h5">
          {{ formatNumber(summary.mean) }}
        </div>
      </v-card>
    </v-col>


    <v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Минимум</div>
        <div class="text-h5">
          {{ formatNumber(summary.min) }}
        </div>
      </v-card>
    </v-col>

	<v-col cols="12" sm="6" md="4">
      <v-card class="pa-4 h-100" variant="tonal">
        <div class="text-caption">Максимум</div>
        <div class="text-h5">
          {{ formatNumber(summary.max) }}
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>