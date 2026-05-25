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
    <div class="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Left Column: 3D Model -->
      <div class="lg:col-span-2 flex flex-col gap-6">
        <!-- 3D Digital Twin Viewer -->
        <SmartHome3D 
          :deviceStates="deviceStates"
          @toggle="toggleDevice($event, '3D Click')"
        />
      </div>

      <!-- Right Column: Control Panel and Monitor Logs -->
      <div class="flex flex-col gap-6">
        <ControlPanel 
          :deviceStates="deviceStates"
          :logs="logs"
          @toggle="toggleDevice($event, 'UI Switch')"
          @scenario="runScenario"
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

const logs = ref('')

function logToConsole(device, state, source) {
  const time = new Date().toLocaleTimeString()
  let espCmd = ''
  let relayMsg = ''
  
  if (device.startsWith('Đèn')) {
    espCmd = state ? `ESP32_CMD_LIGHT_ON` : `ESP32_CMD_LIGHT_OFF`
    relayMsg = `Relay Channel ${getRelayChannel(device)} -> ${state ? 'CLOSED (ON)' : 'OPEN (OFF)'}`
  } else if (device.startsWith('Quạt')) {
    espCmd = state ? `ESP32_CMD_FAN_ON` : `ESP32_CMD_FAN_OFF`
    relayMsg = `Relay Channel ${getRelayChannel(device)} -> ${state ? 'CLOSED (ON)' : 'OPEN (OFF)'}`
  } else if (device.startsWith('Cửa')) {
    espCmd = state ? `ESP32_CMD_SOLENOID_UNLOCK` : `ESP32_CMD_SOLENOID_LOCK`
    relayMsg = `Solenoid lock -> ${state ? 'UNLOCKED (Open)' : 'LOCKED (Closed)'}`
  }

  logs.value += `[${time}] [Source: ${source}]
>> ESP32: Broadcast command [${espCmd}] for "${device}"
>> Status: ${relayMsg}
----------------------------------------\n`
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
  logs.value += `\n[${new Date().toLocaleTimeString()}] *** KÍCH HOẠT KỊCH BẢN: ${type.toUpperCase()} ***\n`
  
  if (type === 'welcome') {
    if (!deviceStates.value['Cửa Chính']) toggleDevice('Cửa Chính', 'Scenario Auto')
    if (!deviceStates.value['Đèn Hành Lang']) toggleDevice('Đèn Hành Lang', 'Scenario Auto')
    if (!deviceStates.value['Đèn Chùm Trung Tâm']) toggleDevice('Đèn Chùm Trung Tâm', 'Scenario Auto')
    if (!deviceStates.value['Quạt Trần Phòng Khách']) toggleDevice('Quạt Trần Phòng Khách', 'Scenario Auto')
  } 
  else if (type === 'sleep') {
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
    Object.keys(deviceStates.value).forEach(device => {
      if (deviceStates.value[device]) toggleDevice(device, 'Scenario Auto')
    })
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
    logs.value = `[${new Date().toLocaleTimeString()}] ESP32-WROOM-3D Booted.\n[RELAY] Relay board channels initialised.\n[SERIAL] Baudrate 115200 active.\nReady for hardware demo commands.\n----------------------------------------\n`
  }, 100)
})

onUnmounted(() => clearInterval(interval))
</script>