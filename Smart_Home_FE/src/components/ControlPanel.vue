<template>
  <div class="bg-white rounded-2xl p-6 shadow-md">
    <h3 class="text-sm font-medium text-gray-500 mb-4">Điều khiển thiết bị</h3>
    <div class="flex flex-col gap-4">

      <!-- Quạt -->
      <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🌀</span>
          <div>
            <div class="font-medium text-gray-700">Quạt</div>
            <div class="text-xs text-gray-400">{{ fanStatus ? 'Đang bật' : 'Đang tắt' }}</div>
          </div>
        </div>
        <button
          @click="toggleFan"
          :class="fanStatus
            ? 'bg-blue-500 hover:bg-blue-600'
            : 'bg-gray-200 hover:bg-gray-300'"
          class="w-14 h-7 rounded-full transition-all duration-300 relative"
        >
          <span
            :class="fanStatus ? 'translate-x-7' : 'translate-x-1'"
            class="absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-all duration-300"
          />
        </button>
      </div>

      <!-- Khóa cửa -->
      <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🔒</span>
          <div>
            <div class="font-medium text-gray-700">Khóa cửa</div>
            <div class="text-xs text-gray-400">{{ doorStatus ? 'Đang mở' : 'Đang khóa' }}</div>
          </div>
        </div>
        <button
          @click="toggleDoor"
          :class="doorStatus
            ? 'bg-green-500 hover:bg-green-600'
            : 'bg-gray-200 hover:bg-gray-300'"
          class="w-14 h-7 rounded-full transition-all duration-300 relative"
        >
          <span
            :class="doorStatus ? 'translate-x-7' : 'translate-x-1'"
            class="absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-all duration-300"
          />
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const fanStatus = ref(false)
const doorStatus = ref(false)

const API = 'http://localhost:8000'

async function toggleFan() {
  fanStatus.value = !fanStatus.value
  await axios.post(`${API}/api/control`, {
    device: 'fan',
    status: fanStatus.value
  })
}

async function toggleDoor() {
  doorStatus.value = !doorStatus.value
  await axios.post(`${API}/api/control`, {
    device: 'door',
    status: doorStatus.value
  })
}
</script>