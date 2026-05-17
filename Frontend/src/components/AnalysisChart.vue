<script setup>
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement
} from 'chart.js'

import { Bar, Line } from 'vue-chartjs'
import { computed } from 'vue'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement
)

const emit = defineEmits(['select'])

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  metricLabel: {
    type: String,
    default: 'Значение метрики'
  }
})

const chartColor = '#1DB5E8'
const lineColor = '#374B9B'

const labelsCount = computed(() => {
  if (props.result.chart_type === 'entity_timeline') {
    return props.result?.data?.line?.length || 0
  }

  return props.result?.data?.length || 0
})

const chartWidth = computed(() => {
  if (props.result.chart_type === 'histogram') {
    return `${Math.max(900, labelsCount.value * 34)}px`
  }

  if (props.result.chart_type === 'bar') {
    return `${Math.max(900, labelsCount.value * 80)}px`
  }

  if (props.result.chart_type === 'line') {
    return `${Math.max(900, labelsCount.value * 70)}px`
  }

  if (props.result.chart_type === 'entity_timeline') {
    return `${Math.max(900, labelsCount.value * 80)}px`
  }

  return '900px'
})

const chartData = computed(() => {
  const result = props.result

  if (result.chart_type === 'histogram') {
    return {
      labels: result.data.map(item => item.label),
      datasets: [
        {
          label: 'Количество предложений',
          data: result.data.map(item => item.count),
          minBarLength: 3,
          maxBarThickness: 22,
          backgroundColor: chartColor,
          borderColor: chartColor
        }
      ]
    }
  }

  if (result.chart_type === 'bar') {
    return {
      labels: result.data.map(item => item.group || 'Без значения'),
      datasets: [
        {
          label: props.metricLabel,
          data: result.data.map(item => Number(item.mean)),
          minBarLength: 3,
          maxBarThickness: 42,
          backgroundColor: chartColor,
          borderColor: chartColor
        }
      ]
    }
  }

  if (result.chart_type === 'line') {
    return {
      labels: result.data.map(item => item.period),
      datasets: [
        {
          label: props.metricLabel,
          data: result.data.map(item => Number(item.mean)),
          tension: 0.25,
          pointRadius: 4,
          pointHoverRadius: 6,
          backgroundColor: chartColor,
          borderColor: chartColor,
          pointBackgroundColor: chartColor,
          pointBorderColor: chartColor
        }
      ]
    }
  }

  if (result.chart_type === 'entity_timeline') {
    const line = result.data?.line || []
    const points = result.data?.points || []

    return {
      labels: line.map(item => item.period),
      datasets: [
        {
          label: 'Среднее по десятилетиям',
          data: line.map(item => toChartNumber(item.mean)),
          borderColor: lineColor,
          backgroundColor: lineColor,
          pointBackgroundColor: lineColor,
          pointBorderColor: lineColor,
          tension: 0.25,
          pointRadius: 3,
          pointHoverRadius: 5
        },
        {
          label: 'Объекты',
          data: points.map(item => ({
            x: item.period,
            y: Number(item.mean)
          })),
          showLine: false,
          borderColor: chartColor,
          backgroundColor: chartColor,
          pointBackgroundColor: chartColor,
          pointBorderColor: chartColor,
          pointRadius: 6,
          pointHoverRadius: 8
        }
      ]
    }
  }

  return {
    labels: [],
    datasets: []
  }
})

function getPointSelection(chart, event) {
  const isLineLike =
    props.result.chart_type === 'line' ||
    props.result.chart_type === 'entity_timeline'

  return chart.getElementsAtEventForMode(
    event,
    'nearest',
    {
      intersect: !isLineLike
    },
    true
  )
}
function toChartNumber(value) {
  if (value === null || value === undefined) {
    return null
  }

  const number = Number(value)
  return Number.isNaN(number) ? null : number
}

const chartOptions = computed(() => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'nearest',
      intersect: false
    },

    onClick(event, elements, chart) {
      const points = getPointSelection(chart, event)

      if (!points.length) {
        return
      }

      const point = points[0]

      if (props.result.chart_type === 'entity_timeline') {
        // datasetIndex 0 — линия по десятилетиям,
        // datasetIndex 1 — точки объектов.
        if (point.datasetIndex !== 1) {
          return
        }

        const item = props.result.data.points[point.index]

        if (!item) {
          return
        }

        emit('select', {
          chart_type: props.result.chart_type,
          graph_mode: props.result.graph_mode,
          entity_type: props.result.entity_type,
          index: point.index,
          item
        })

        return
      }

      const item = props.result.data[point.index]

      if (!item) {
        return
      }

      emit('select', {
        chart_type: props.result.chart_type,
        group_by: props.result.group_by,
        index: point.index,
        item
      })
    },

    onHover(event, elements, chart) {
      const points = getPointSelection(chart, event)

      if (event.native?.target) {
        event.native.target.style.cursor = points.length ? 'pointer' : 'default'
      }
    },

    plugins: {
      legend: {
        display: true
      },
      tooltip: {
        enabled: true,
        callbacks: {
          title(context) {
            const point = context[0]

            if (!point) {
              return ''
            }

            if (props.result.chart_type === 'entity_timeline') {
              if (point.datasetIndex === 1) {
                const item = props.result.data.points[point.dataIndex]
                return item?.entity_name || 'Объект'
              }

              const item = props.result.data.line[point.dataIndex]
              return item?.period || ''
            }

            const item = props.result.data[point.dataIndex]

            if (!item) {
              return ''
            }

            if (props.result.chart_type === 'histogram') {
              return `Значение: ${item.label}`
            }

            if (props.result.chart_type === 'bar') {
              return item.group || 'Без значения'
            }

            if (props.result.chart_type === 'line') {
              return item.period
            }

            return ''
          },

          label(context) {
            if (props.result.chart_type === 'entity_timeline') {
              if (context.datasetIndex === 1) {
                const item = props.result.data.points[context.dataIndex]

                if (!item) {
                  return ''
                }

                return [
                  `Период: ${item.period}`,
                  `Среднее значение: ${Number(item.mean).toFixed(3)}`,
                  `Произведений: ${item.documents_count || 0}`,
                  item.year_min && item.year_max
                    ? `Годы: ${item.year_min}–${item.year_max}`
                    : ''
                ].filter(Boolean)
              }

              const item = props.result.data.line[context.dataIndex]

              if (!item) {
                return ''
              }

              return [
                `Среднее значение: ${Number(item.mean).toFixed(3)}`,
                `Объектов/единиц: ${Number(item.count || 0).toLocaleString('ru-RU')}`
              ]
            }

            const item = props.result.data[context.dataIndex]

            if (!item) {
              return ''
            }

            if (props.result.chart_type === 'histogram') {
              return `Предложений: ${Number(item.count).toLocaleString('ru-RU')}`
            }

            if (props.result.chart_type === 'bar') {
              return `Среднее значение: ${Number(item.mean).toFixed(3)}`
            }

            if (props.result.chart_type === 'line') {
              return `Среднее значение: ${Number(item.mean).toFixed(3)}`
            }

            return ''
          },

          afterLabel(context) {
            if (props.result.chart_type === 'entity_timeline') {
              return ''
            }

            const item = props.result.data[context.dataIndex]

            if (!item || item.count === undefined) {
              return ''
            }

            return `Количество: ${Number(item.count).toLocaleString('ru-RU')}`
          }
        }
      }
    },

    scales: {
      x: {
        ticks: {
          autoSkip: false,
          maxRotation: 55,
          minRotation: 55
        },
        grid: {
          display: true
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          callback(value) {
            return Number(value).toLocaleString('ru-RU')
          }
        }
      }
    }
  }
})
</script>

<template>
  <div class="chart-scroll-wrapper">
    <div
      class="chart-inner"
      :style="{ width: chartWidth }"
    >
      <Line
        v-if="result.chart_type === 'line' || result.chart_type === 'entity_timeline'"
        :data="chartData"
        :options="chartOptions"
      />

      <Bar
        v-else
        :data="chartData"
        :options="chartOptions"
      />
    </div>
  </div>
</template>

<style scoped>
.chart-scroll-wrapper {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 12px;
}

.chart-inner {
  height: 420px;
  min-width: 900px;
}
</style>