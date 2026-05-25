<template>
  <div class="bg-white rounded-2xl p-6 shadow-md">
    <h3 class="text-sm font-medium text-gray-500 mb-4">{{ title }}</h3>
    <apexchart
      type="area"
      height="200"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  data: Array,
  labels: Array,
  color: { type: String, default: '#f97316' }
})

const series = computed(() => [{
  name: props.title,
  data: props.data || []
}])

const chartOptions = computed(() => ({
  chart: {
    toolbar: { show: false },
    animations: { enabled: true },
    background: 'transparent'
  },
  stroke: { curve: 'smooth', width: 2 },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.0
    }
  },
  colors: [props.color],
  xaxis: {
    categories: props.labels || [],
    labels: {
      style: { fontSize: '10px', colors: '#9ca3af' },
      rotate: -45,
      maxHeight: 60
    },
    tickAmount: 6
  },
  yaxis: {
    labels: { style: { colors: '#9ca3af' } }
  },
  grid: { borderColor: '#f3f4f6' },
  tooltip: { theme: 'light' },
  dataLabels: { enabled: false }
}))
</script>