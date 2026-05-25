<template>
  <div class="min-h-screen bg-gray-100">

    <!-- Navbar -->
    <nav class="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-2xl">🏠</span>
        <span class="text-lg font-semibold text-gray-700">Smart Home</span>
      </div>
      <div class="flex items-center gap-2">
        <span
          :class="connected ? 'bg-green-400' : 'bg-red-400'"
          class="w-2 h-2 rounded-full"
        />
        <span class="text-xs text-gray-400">{{ connected ? 'Đang kết nối' : 'Mất kết nối' }}</span>
      </div>
    </nav>

    <!-- Content -->
    <div class="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-6">

      <!-- Cards -->
      <div class="grid grid-cols-2 gap-4">
        <SensorCard
          label="Nhiệt độ"
          :value="latestTemp"
          unit=" °C"
          icon="🌡️"
          :timestamp="latestTime"
          bgColor="bg-orange-50"
          textColor="text-orange-500"
        />
        <SensorCard
          label="Độ ẩm"
          :value="latestHumi"
          unit=" %"
          icon="💧"
          :timestamp="latestTime"
          bgColor="bg-blue-50"
          textColor="text-blue-500"
        />
      </div>

      <!-- Charts -->
      <SensorChart
        title="Nhiệt độ (°C)"
        :data="tempData"
        :labels="timeLabels"
        color="#f97316"
      />
      <SensorChart
        title="Độ ẩm (%)"
        :data="humiData"
        :labels="timeLabels"
        color="#3b82f6"
      />

      <!-- Control -->
      <ControlPanel />

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import SensorCard from './components/SensorCard.vue'
import SensorChart from './components/SensorChart.vue'
import ControlPanel from './components/ControlPanel.vue'

const API = 'http://localhost:8000'

const connected = ref(false)
const latestTemp = ref(null)
const latestHumi = ref(null)
const latestTime = ref('')
const tempData = ref([])
const humiData = ref([])
const timeLabels = ref([])

async function fetchData() {
  try {
    const res = await axios.get(`${API}/api/sensor?limit=20`)
    const data = res.data
    connected.value = true

    tempData.value = data.map(d => d.temperature)
    humiData.value = data.map(d => d.humidity)
    timeLabels.value = data.map(d => d.timestamp.slice(11, 16))

    if (data.length > 0) {
      const latest = data[data.length - 1]
      latestTemp.value = latest.temperature
      latestHumi.value = latest.humidity
      latestTime.value = latest.timestamp
    }
  } catch {
    connected.value = false
  }
}

let interval
onMounted(() => {
  fetchData()
  interval = setInterval(fetchData, 5000)
})
onUnmounted(() => clearInterval(interval))
</script>