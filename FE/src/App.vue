<template>
  <div class="min-h-screen bg-[#111113] text-gray-200">
    <!-- Navbar -->
    <nav class="bg-[#18181c] border-b border-gray-800/40 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-2xl">🏠</span>
        <span class="text-lg font-semibold text-white">Smart Home Dashboard</span>
      </div>
      <div class="flex items-center gap-2">
        <span
          :class="connected ? 'bg-green-400' : 'bg-red-400'"
          class="w-2.5 h-2.5 rounded-full animate-pulse"
        />
        <span class="text-xs text-gray-400 font-medium">
          {{ connected ? 'Đang kết nối API' : 'Mất kết nối API' }}
        </span>
      </div>
    </nav>

    <!-- Grid Content Layout -->
    <div class="max-w-7xl mx-auto px-4 py-4 grid grid-cols-1 lg:grid-cols-3 gap-6 lg:h-[calc(100vh-100px)] lg:min-h-[500px]">
      
      <!-- Left Column: 3D Model -->
      <div class="lg:col-span-2 h-full flex flex-col">
        <!-- 3D Digital Twin Viewer -->
        <SmartHome3D 
          :deviceStates="deviceStates"
          @toggle="toggleDevice($event, '3D Click')"
          class="h-full"
        />
      </div>

      <!-- Right Column: Control Panel and Monitor Logs -->
      <div class="h-full flex flex-col">
        <ControlPanel 
          :deviceStates="deviceStates"
          :logs="logs"
          :aiLoading="aiLoading"
          @toggle="toggleDevice($event, 'UI Switch')"
          @scenario="runScenario"
          @ai-command="handleAICommand"
          @add-log="addLog($event.tag, $event.msg, $event.type)"
          class="h-full"
        />
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import ControlPanel from './components/ControlPanel.vue'
import SmartHome3D from './components/SmartHome3D.vue'

const API = 'http://localhost:8000'

const connected = ref(false)
const aiLoading = ref(false)

// Shared states for all lights, fans and doors
const deviceStates = ref({
  'Đèn Hành Lang': false,
  'Đèn Phòng Ngủ': false,
  'Đèn Nhà Vệ Sinh': false,
  'Đèn Chùm Trung Tâm': false,
  'Đèn Nhà Bếp': false,
  'Đèn Khu KT': false,
  'Quạt Phòng Ngủ': false,
  'Quạt Nhà Bếp': false,
  'Quạt Trần Phòng Khách': false,
  'Cửa Chính': false,
  'Cửa Nhà Vệ Sinh': false,
  'Cửa Phòng Ngủ': false,
  'Cửa Nhà Bếp': false,
  'Cửa Khu KT': false
})

const logs = ref([])

function addLog(tag, msg, type = 'info') {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  logs.value.push({ time, tag, msg, type })
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

function logToConsole(device, state, source) {
  let tag = 'LIGHT'
  let msg = ''
  
  if (device.startsWith('Đèn')) {
    tag = 'LIGHT'
    msg = `${state ? 'BẬT' : 'TẮT'} ${device.toLowerCase()}`
    addLog(tag, msg, state ? 'success' : 'info')
    addLog('RELAY', `Kích hoạt Rơ-le Kênh ${getRelayChannel(device)} (${state ? 'BẬT' : 'TẮT'})`, 'warning')
  } else if (device.startsWith('Quạt')) {
    tag = 'FAN'
    msg = `${state ? 'BẬT' : 'TẮT'} ${device.toLowerCase()}`
    addLog(tag, msg, state ? 'success' : 'info')
    addLog('RELAY', `Kích hoạt Rơ-le Kênh ${getRelayChannel(device)} (${state ? 'BẬT' : 'TẮT'})`, 'warning')
  } else if (device.startsWith('Cửa')) {
    tag = 'DOOR'
    msg = `${state ? 'MỞ KHÓA' : 'ĐÓNG KHÓA'} ${device.toLowerCase()}`
    addLog(tag, msg, state ? 'success' : 'info')
    addLog('RELAY', `${state ? 'Mở khóa' : 'Khóa'} chốt điện từ`, 'warning')
  }
}

function getRelayChannel(device) {
  const mapping = {
    'Đèn Hành Lang': 1, 'Đèn Phòng Ngủ': 2, 'Đèn Nhà Vệ Sinh': 3,
    'Đèn Chùm Trung Tâm': 4, 'Đèn Nhà Bếp': 5, 'Đèn Khu KT': 6,
    'Quạt Phòng Ngủ': 7, 'Quạt Nhà Bếp': 8, 'Quạt Trần Phòng Khách': 'PWM'
  }
  return mapping[device] || 1
}

function mapDeviceToApiKey(name) {
  const mapping = {
    'Đèn Hành Lang': 'light_hallway',
    'Đèn Phòng Ngủ': 'light_bedroom',
    'Đèn Nhà Vệ Sinh': 'light_toilet',
    'Đèn Chùm Trung Tâm': 'light_livingroom',
    'Đèn Nhà Bếp': 'light_kitchen',
    'Đèn Khu KT': 'light_tech',
    'Quạt Phòng Ngủ': 'fan_bedroom',
    'Quạt Nhà Bếp': 'fan_kitchen',
    'Quạt Trần Phòng Khách': 'fan', // Map to general 'fan' as in original
    'Cửa Chính': 'door',            // Map to general 'door' as in original
    'Cửa Nhà Vệ Sinh': 'door_toilet',
    'Cửa Phòng Ngủ': 'door_bedroom',
    'Cửa Nhà Bếp': 'door_kitchen',
    'Cửa Khu KT': 'door_tech'
  }
  return mapping[name] || 'unknown'
}

async function toggleDevice(name, source = 'UI Panel') {
  if (deviceStates.value[name] === undefined) return
  
  deviceStates.value[name] = !deviceStates.value[name]
  const isON = deviceStates.value[name]

  // Add locally to the Console log monitor
  logToConsole(name, isON, source)

  // Send request to API backend
  try {
    const apiDeviceKey = mapDeviceToApiKey(name)
    await axios.post(`${API}/api/control`, {
      device: apiDeviceKey,
      status: isON
    })
  } catch (err) {
    console.error('Lỗi khi điều khiển thiết bị thông qua API:', err)
  }
}

function runScenario(type) {
  if (type === 'welcome') {
    addLog('SYSTEM', 'Kịch bản: VỀ NHÀ', 'info')
    addLog('ALERT', 'Gửi thông báo: Bot Telegram', 'info')
    if (!deviceStates.value['Cửa Chính']) toggleDevice('Cửa Chính', 'Scenario Auto')
    if (!deviceStates.value['Đèn Hành Lang']) toggleDevice('Đèn Hành Lang', 'Scenario Auto')
    if (!deviceStates.value['Đèn Chùm Trung Tâm']) toggleDevice('Đèn Chùm Trung Tâm', 'Scenario Auto')
    if (!deviceStates.value['Quạt Trần Phòng Khách']) toggleDevice('Quạt Trần Phòng Khách', 'Scenario Auto')
  } 
  else if (type === 'sleep') {
    addLog('SYSTEM', 'Kịch bản: ĐI NGỦ', 'info')
    addLog('ALERT', 'Kích hoạt an ninh đêm', 'success')
    ['Cửa Chính', 'Cửa Nhà Vệ Sinh', 'Cửa Phòng Ngủ', 'Cửa Nhà Bếp', 'Cửa Khu KT'].forEach(door => {
      if (deviceStates.value[door]) toggleDevice(door, 'Scenario Auto')
    })
    ['Đèn Hành Lang', 'Đèn Nhà Vệ Sinh', 'Đèn Chùm Trung Tâm', 'Đèn Nhà Bếp', 'Đèn Khu KT'].forEach(light => {
      if (deviceStates.value[light]) toggleDevice(light, 'Scenario Auto')
    })
    if (!deviceStates.value['Đèn Phòng Ngủ']) toggleDevice('Đèn Phòng Ngủ', 'Scenario Auto')
    ['Quạt Nhà Bếp', 'Quạt Trần Phòng Khách'].forEach(fan => {
      if (deviceStates.value[fan]) toggleDevice(fan, 'Scenario Auto')
    })
    if (!deviceStates.value['Quạt Phòng Ngủ']) toggleDevice('Quạt Phòng Ngủ', 'Scenario Auto')
  } 
  else if (type === 'sos') {
    addLog('MQ2', 'Khói vượt ngưỡng: 380 ppm', 'danger')
    addLog('ALERT', 'Gửi báo động: Telegram + Còi', 'danger')
    addLog('RELAY', 'Bật quạt hút bếp tự động', 'warning')
    ['Cửa Chính', 'Cửa Nhà Vệ Sinh', 'Cửa Phòng Ngủ', 'Cửa Nhà Bếp', 'Cửa Khu KT'].forEach(door => {
      if (!deviceStates.value[door]) toggleDevice(door, 'Scenario Auto')
    })
    ['Đèn Hành Lang', 'Đèn Phòng Ngủ', 'Đèn Nhà Vệ Sinh', 'Đèn Chùm Trung Tâm', 'Đèn Nhà Bếp', 'Đèn Khu KT'].forEach(light => {
      if (!deviceStates.value[light]) toggleDevice(light, 'Scenario Auto')
    })
    ['Quạt Phòng Ngủ', 'Quạt Trần Phòng Khách', 'Quạt Nhà Bếp'].forEach(fan => {
      if (!deviceStates.value[fan]) toggleDevice(fan, 'Scenario Auto')
    })
  } 
  else if (type === 'alloff') {
    addLog('SYSTEM', 'Kịch bản: TẮT HẾT', 'info')
    addLog('MQ2', 'Khói giảm - Bình thường', 'success')
    addLog('ALERT', 'Tắt còi báo động - An toàn', 'success')
    Object.keys(deviceStates.value).forEach(device => {
      if (deviceStates.value[device]) toggleDevice(device, 'Scenario Auto')
    })
  }
}

async function handleAICommand(command) {
  if (aiLoading.value) return
  
  aiLoading.value = true
  addLog('SYSTEM', `Đang gửi lệnh AI: "${command}"...`, 'info')
  
  try {
    const res = await axios.post(`${API}/api/ai/command`, { command })
    const data = res.data
    
    // In phản hồi của AI vào Console Log
    if (data.response) {
      addLog('SYSTEM', `Trợ lý AI: ${data.response}`, 'success')
    }
    
    // Kích hoạt kịch bản nếu có
    if (data.scenario) {
      runScenario(data.scenario)
    }
    
    // Thực thi các hành động trên thiết bị
    if (data.actions && Array.isArray(data.actions)) {
      for (const action of data.actions) {
        const { device, status } = action
        if (deviceStates.value[device] !== undefined) {
          // Chỉ thay đổi trạng thái nếu trạng thái hiện tại khác trạng thái mong muốn
          if (deviceStates.value[device] !== status) {
            await toggleDevice(device, 'AI Assistant')
          }
        }
      }
    }
  } catch (err) {
    console.error('Lỗi khi gọi API AI:', err)
    let errorMsg = 'Không thể kết nối đến máy chủ AI.'
    if (err.response && err.response.data && err.response.data.response) {
      errorMsg = err.response.data.response
    }
    addLog('SYSTEM', `Trợ lý AI: Lỗi - ${errorMsg}`, 'danger')
  } finally {
    aiLoading.value = false
  }
}

async function pingAPI() {
  try {
    await axios.get(`${API}/api/sensor?limit=1`)
    connected.value = true
  } catch {
    connected.value = false
  }
}

let interval
onMounted(() => {
  pingAPI()
  interval = setInterval(pingAPI, 5000)
  
  // Set initial boot log
  setTimeout(() => {
    addLog('SYSTEM', 'ESP32 khởi động thành công.', 'success')
    addLog('RELAY', 'Khởi tạo kênh Rơ-le thành công.', 'warning')
    addLog('SYSTEM', 'Serial 115200 sẵn sàng.', 'info')
  }, 100)
})

onUnmounted(() => clearInterval(interval))
</script>