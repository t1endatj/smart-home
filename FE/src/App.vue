<template>
  <div class="min-h-screen bg-[#111113] text-gray-200">
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="voiceOverlayVisible"
        class="fixed inset-0 z-40 flex items-center justify-center bg-[#06070b]/42 backdrop-blur-md"
      >
        <div class="mx-6 w-full max-w-3xl rounded-[28px] border border-cyan-300/18 bg-[linear-gradient(180deg,rgba(13,18,27,0.94)_0%,rgba(8,12,18,0.96)_100%)] px-8 py-10 shadow-[0_30px_80px_rgba(0,0,0,0.42)]">
          <div class="mb-4 flex items-center justify-center gap-3">
            <span class="h-3 w-3 rounded-full bg-red-400 shadow-[0_0_18px_rgba(248,113,113,0.95)] animate-pulse" />
            <span class="text-[11px] font-semibold uppercase tracking-[0.28em] text-cyan-100/75">Voice Capture Active</span>
          </div>
          <p class="mb-4 text-center text-sm text-gray-400">Transcript đang được ghi nhận trực tiếp từ microphone</p>
          <div class="min-h-[140px] rounded-[24px] border border-white/8 bg-white/[0.03] px-6 py-8">
            <p class="text-center text-3xl font-medium leading-relaxed text-white md:text-4xl">
              {{ voiceTranscript || 'Hãy nói lệnh của bạn...' }}
            </p>
          </div>
          <div class="mt-6 flex justify-center">
            <button
              type="button"
              @click="requestVoiceStop"
              class="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-6 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/18"
            >
              Xong
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Navbar -->
    <nav :class="[voiceListening ? 'blur-sm scale-[0.995]' : '', !systemUnlocked ? 'blur-md pointer-events-none' : '']" class="bg-[#18181c] border-b border-gray-800/40 px-6 py-4 flex items-center justify-between transition duration-300">
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
    <div :class="[voiceListening ? 'blur-md scale-[0.985]' : '', !systemUnlocked ? 'blur-md pointer-events-none' : '']" class="max-w-7xl mx-auto px-4 py-4 grid grid-cols-1 lg:grid-cols-3 gap-6 lg:h-[calc(100vh-100px)] lg:min-h-[500px] transition duration-300">
      
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
          :fanSpeeds="fanSpeeds"
          :logs="logs"
          :aiLoading="aiLoading"
          :sensors="sensors"
          :autoFanEnabled="autoFanEnabled"
          :autoFanThreshold="autoFanThreshold"
          :autoGasEnabled="autoGasEnabled"
          :autoMotionEnabled="autoMotionEnabled"
          :voice-stop-request="voiceStopRequest"
          @toggle="toggleDevice($event, 'UI Switch')"
          @set-fan-speed="handleSetFanSpeed"
          @scenario="runScenario"
          @ai-command="handleAICommand"
          @add-log="addLog($event.tag, $event.msg, $event.type)"
          @voice-state="updateVoiceState"
          @update-auto-fan="handleUpdateAutoFan"
          @update-auto-gas="handleUpdateAutoGas"
          @update-auto-motion="handleUpdateAutoMotion"
          class="h-full"
        />
      </div>

    </div>

    <!-- Face ID System Lock Overlay -->
    <transition
      enter-active-class="transition duration-500 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-300 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="!systemUnlocked"
        class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#0d0e12]/95 backdrop-blur-lg p-6 select-none"
      >
        <div class="w-full max-w-md bg-[#18181c] border border-gray-800 rounded-3xl p-6 shadow-2xl flex flex-col items-center gap-6 relative overflow-hidden">
          
          <!-- Background Glow decoration -->
          <div class="absolute -top-24 -left-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
          <div class="absolute -bottom-24 -right-24 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <!-- Header -->
          <div class="text-center">
            <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-[10px] font-bold uppercase tracking-wider mb-2">
              🔒 BẢO MẬT HỆ THỐNG
            </div>
            <h2 class="text-lg font-bold text-white uppercase tracking-wide">Xác thực khuôn mặt</h2>
            <p class="text-[10px] text-gray-500 mt-1 max-w-[280px] mx-auto leading-relaxed">
              Vui lòng hướng khuôn mặt vào camera để mở khóa bảng điều khiển Smart Home
            </p>
          </div>

          <!-- Video container with scanner animation -->
          <div class="relative w-full aspect-video rounded-2xl bg-black border border-gray-800 overflow-hidden flex items-center justify-center shadow-inner">
            <video 
              v-show="lockCameraActive"
              ref="lockVideoEl" 
              autoplay 
              playsinline 
              muted 
              class="w-full h-full object-cover"
            />
            
            <!-- Camera placeholder when off -->
            <div v-show="!lockCameraActive" class="text-center p-4 text-[10px] text-gray-500 flex flex-col items-center gap-1.5">
              <span class="text-2xl animate-pulse">📷</span>
              <span class="font-semibold uppercase tracking-wider text-gray-400">Camera chưa sẵn sàng</span>
              <span class="text-[8px] text-gray-600">Đang khởi tạo camera hoặc bấm nút bên dưới</span>
            </div>

            <!-- Laser Scanning line effect -->
            <div 
              v-if="lockCameraActive && lockFaceStatus === 'processing'" 
              class="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_8px_#22d3ee] animate-scan"
            />
            
            <!-- Scan Status overlay -->
            <div 
              v-if="lockFaceStatus" 
              :class="[
                'absolute inset-0 flex items-center justify-center text-xs font-bold text-center px-4 backdrop-blur-sm transition-all',
                lockFaceStatus === 'processing' ? 'bg-black/40 text-cyan-300' : '',
                lockFaceStatus === 'success' ? 'bg-emerald-950/85 text-emerald-300' : '',
                lockFaceStatus === 'failed' ? 'bg-red-950/85 text-red-300' : ''
              ]"
            >
              <div class="flex flex-col items-center gap-1">
                <span v-if="lockFaceStatus === 'processing'" class="animate-spin text-lg">🔄</span>
                <span v-if="lockFaceStatus === 'success'" class="text-lg">✅</span>
                <span v-if="lockFaceStatus === 'failed'" class="text-lg">❌</span>
                <span>{{ lockFaceStatusText }}</span>
              </div>
            </div>
          </div>

          <!-- Controls -->
          <div class="w-full flex flex-col gap-2">
            <button 
              v-if="lockCameraActive"
              type="button" 
              @click="verifyLockFace"
              :disabled="lockFaceStatus === 'processing'"
              class="w-full bg-cyan-600/10 hover:bg-cyan-600/20 active:scale-[0.98] border border-cyan-500/30 text-cyan-300 py-2 rounded-xl text-xs font-bold transition-all text-center cursor-pointer"
            >
              Quét Khuôn Mặt
            </button>
            <button 
              type="button" 
              @click="lockCameraActive ? stopLockCamera() : startLockCamera()"
              class="w-full bg-gray-800/40 hover:bg-gray-800/60 active:scale-[0.98] border border-gray-700 text-gray-300 py-2 rounded-xl text-xs font-bold transition-all text-center cursor-pointer"
            >
              {{ lockCameraActive ? 'Tắt Camera' : 'Bật Camera' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>


<script setup>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import ControlPanel from './components/ControlPanel.vue'
import SmartHome3D from './components/SmartHome3D.vue'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const systemUnlocked = ref(false)
const lockCameraActive = ref(false)
const lockVideoEl = ref(null)
const lockFaceStatus = ref(null)
const lockFaceStatusText = ref('')
let lockStream = null

async function startLockCamera() {
  lockFaceStatus.value = null
  lockFaceStatusText.value = ''
  try {
    lockCameraActive.value = true
    await nextTick()
    const mediaStream = await navigator.mediaDevices.getUserMedia({ 
      video: { width: 640, height: 480 } 
    })
    lockStream = mediaStream
    if (lockVideoEl.value) {
      lockVideoEl.value.srcObject = mediaStream
      lockVideoEl.value.play().catch(e => console.error("Error playing lock camera:", e))
    }
  } catch (err) {
    lockCameraActive.value = false
    console.error('Lỗi mở camera lock:', err)
    lockFaceStatus.value = 'failed'
    lockFaceStatusText.value = 'Không thể truy cập camera. Vui lòng cấp quyền.'
  }
}

function stopLockCamera() {
  if (lockStream) {
    lockStream.getTracks().forEach(track => track.stop())
    lockStream = null
  }
  lockCameraActive.value = false
  if (lockVideoEl.value) {
    lockVideoEl.value.srcObject = null
  }
}

async function verifyLockFace() {
  if (!lockVideoEl.value) return

  lockFaceStatus.value = 'processing'
  lockFaceStatusText.value = 'Đang quét khuôn mặt...'

  try {
    const canvas = document.createElement('canvas')
    canvas.width = lockVideoEl.value.videoWidth || 640
    canvas.height = lockVideoEl.value.videoHeight || 480
    const ctx = canvas.getContext('2d')
    ctx.drawImage(lockVideoEl.value, 0, 0, canvas.width, canvas.height)
    
    const base64Image = canvas.toDataURL('image/jpeg', 0.8)
    
    const res = await axios.post(`${API}/api/face/verify`, {
      image: base64Image
    })

    if (res.data && res.data.result === true) {
      const matchedName = res.data.name || 'Thành viên'
      lockFaceStatus.value = 'success'
      lockFaceStatusText.value = `Xác thực thành công! Xin chào ${matchedName}.`
      
      setTimeout(() => {
        stopLockCamera()
        systemUnlocked.value = true
      }, 1500)
    } else {
      const errMsg = res.data.message || res.data.error || 'Khuôn mặt không trùng khớp.'
      lockFaceStatus.value = 'failed'
      lockFaceStatusText.value = 'Xác thực thất bại! Không tìm thấy mẫu khớp.'
    }
  } catch (err) {
    console.error('Lỗi xác thực khóa:', err)
    lockFaceStatus.value = 'failed'
    lockFaceStatusText.value = 'Lỗi kết nối máy chủ.'
  }
}


const connected = ref(false)
const aiLoading = ref(false)
const sensors = ref({ temperature: null, humidity: null, motion: false, gasAlarm: false, gasPpm: null, timestamp: null })
const autoFanEnabled = ref(false)
const autoFanThreshold = ref(32)
const autoGasEnabled = ref(true)
const autoMotionEnabled = ref(false)
const voiceListening = ref(false)
const voiceTranscript = ref('')
const voiceStopRequest = ref(0)

const voiceOverlayVisible = computed(() => voiceListening.value)

// Shared states for all lights, fans and doors
const DEFAULT_DEVICE_STATES = {
  'Đèn Hành Lang': false,
  'Đèn Phòng Ngủ': false,
  'Đèn Nhà Vệ Sinh': false,
  'Đèn Chùm Trung Tâm': false,
  'Đèn Nhà Bếp': false,
  'Quạt Phòng Ngủ': false,
  'Quạt Trần Phòng Khách': false,
  'Cửa Chính': false,
  'Cửa Nhà Vệ Sinh': false,
  'Cửa Phòng Ngủ': false,
  'Cửa Nhà Bếp': false,
  'Cửa Khu KT': false
}
const deviceStates = ref({ ...DEFAULT_DEVICE_STATES })
const DEFAULT_FAN_SPEEDS = {
  'Quạt Phòng Ngủ': 35,
  'Quạt Trần Phòng Khách': 35
}
const fanSpeeds = ref({ ...DEFAULT_FAN_SPEEDS })

const logs = ref([])
let nextSyncAllowedAt = 0
let persistInFlight = false
let latestAppliedRevision = 0
let pendingLocalRevision = 0

function lockStateSync(durationMs = 1800) {
  nextSyncAllowedAt = Math.max(nextSyncAllowedAt, Date.now() + durationMs)
}

let isApplyingState = false

function applyHomeState(payload) {
  if (!payload || typeof payload !== 'object') return
  isApplyingState = true
  if (payload.deviceStates && typeof payload.deviceStates === 'object') {
    deviceStates.value = { ...DEFAULT_DEVICE_STATES, ...payload.deviceStates }
  }
  if (payload.fanSpeeds && typeof payload.fanSpeeds === 'object') {
    fanSpeeds.value = { ...DEFAULT_FAN_SPEEDS, ...payload.fanSpeeds }
  }
  if (Array.isArray(payload.logs)) {
    logs.value = payload.logs
  }
  if (typeof payload.automation?.autoGasEnabled === 'boolean') {
    autoGasEnabled.value = payload.automation.autoGasEnabled
  }
  if (typeof payload.automation?.autoMotionEnabled === 'boolean') {
    autoMotionEnabled.value = payload.automation.autoMotionEnabled
  }
  if (typeof payload.automation?.autoTemperatureEnabled === 'boolean') {
    autoFanEnabled.value = payload.automation.autoTemperatureEnabled
  }
  if (typeof payload.automation?.autoTemperatureThreshold === 'number') {
    autoFanThreshold.value = payload.automation.autoTemperatureThreshold
  }
  setTimeout(() => {
    isApplyingState = false
  }, 50)
}

async function syncHomeState() {
  if (aiLoading.value || persistInFlight || Date.now() < nextSyncAllowedAt) {
    return
  }

  try {
    const res = await axios.get(`${API}/api/state`)
    const payload = res?.data?.payload
    const remoteRevision = Number(res?.data?.revision || 0)
    if (!payload) {
      return
    }
    if (remoteRevision <= latestAppliedRevision || remoteRevision < pendingLocalRevision) {
      return
    }
    applyHomeState(payload)
    latestAppliedRevision = remoteRevision
  } catch {
    // Ignore transient sync failures; connectivity is handled by pingAPI.
  }
}

let persistTimer
async function persistHomeState() {
  const payload = {
    deviceStates: deviceStates.value,
    fanSpeeds: fanSpeeds.value,
    logs: logs.value,
    automation: {
      autoTemperatureEnabled: autoFanEnabled.value,
      autoTemperatureThreshold: autoFanThreshold.value,
      autoGasEnabled: autoGasEnabled.value,
      autoMotionEnabled: autoMotionEnabled.value
    }
  }

  persistInFlight = true
  try {
    const res = await axios.post(`${API}/api/state`, payload)
    const committedRevision = Number(res?.data?.revision || 0)
    latestAppliedRevision = committedRevision
    pendingLocalRevision = committedRevision
    // Giảm thời gian lock khi persist thành công để nhận update nhanh hơn
    lockStateSync(500)
  } catch (error) {
    pendingLocalRevision = latestAppliedRevision
    throw error
  } finally {
    persistInFlight = false
  }
}

function schedulePersistHomeState() {
  if (isApplyingState) return
  lockStateSync(1000)
  pendingLocalRevision = latestAppliedRevision + 1
  clearTimeout(persistTimer)
  persistTimer = setTimeout(() => {
    persistHomeState().catch(() => {})
  }, 250)
}

function addLog(tag, msg, type = 'info') {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  logs.value.push({ time, tag, msg, type })
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

function updateVoiceState(payload) {
  voiceListening.value = Boolean(payload?.isListening)
  voiceTranscript.value = typeof payload?.transcript === 'string' ? payload.transcript : ''
}

function requestVoiceStop() {
  voiceStopRequest.value += 1
}

function logToConsole(device, state, source, speed = null) {
  let tag = 'LIGHT'
  let msg = ''
  
  if (device.startsWith('Đèn')) {
    tag = 'LIGHT'
    msg = `${state ? 'BẬT' : 'TẮT'} ${device.toLowerCase()}`
    if (!isApplyingState) addLog(tag, msg, state ? 'success' : 'info')
  } else if (device.startsWith('Quạt')) {
    tag = 'FAN'
    msg = `${state ? 'BẬT' : 'TẮT'} ${device.toLowerCase()}${state && speed ? ` ${speed}%` : ''}`
    if (!isApplyingState) addLog(tag, msg, state ? 'success' : 'info')
  } else if (device.startsWith('Cửa')) {
    tag = 'DOOR'
    msg = `${state ? 'MỞ KHÓA' : 'ĐÓNG KHÓA'} ${device.toLowerCase()}`
    if (!isApplyingState) addLog(tag, msg, state ? 'success' : 'info')
  }
}

function getRelayChannel(device) {
  const mapping = {
    'Đèn Hành Lang': 1, 'Đèn Phòng Ngủ': 2, 'Đèn Nhà Vệ Sinh': 3,
    'Đèn Chùm Trung Tâm': 4, 'Đèn Nhà Bếp': 5,
    'Quạt Phòng Ngủ': 7, 'Quạt Trần Phòng Khách': 'PWM'
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
    'Quạt Phòng Ngủ': 'fan_bedroom',
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

  lockStateSync(1000)
  deviceStates.value[name] = !deviceStates.value[name]
  const isON = deviceStates.value[name]
  const speed = name.startsWith('Quạt') ? fanSpeeds.value[name] : null

  // Add locally to the Console log monitor
  logToConsole(name, isON, source, speed)

  // Lights are FE-only (no BE call)
  if (name.startsWith('Đèn')) {
    schedulePersistHomeState()
    return
  }

  // Send request to API backend (fans/doors)
  try {
    const apiDeviceKey = mapDeviceToApiKey(name)
    await axios.post(`${API}/api/control`, {
      device: apiDeviceKey,
      status: isON,
      speed
    })
  } catch (err) {
    console.error('Lỗi khi điều khiển thiết bị thông qua API:', err)
  } finally {
    schedulePersistHomeState()
  }
}

async function handleSetFanSpeed({ name, speed, shouldTurnOn = true, source = 'UI Panel' }) {
  if (fanSpeeds.value[name] === undefined) return
  if (speed < 10 || speed > 100) return

  lockStateSync(1000)
  fanSpeeds.value[name] = speed
  const isOn = shouldTurnOn ? true : Boolean(deviceStates.value[name])
  if (shouldTurnOn) {
    deviceStates.value[name] = true
  }

  if (!isApplyingState) addLog('FAN', `${name} chuyển sang ${speed}%${isOn ? '' : ' (ghi nhớ)'}`, 'info')

  try {
    await axios.post(`${API}/api/control`, {
      device: mapDeviceToApiKey(name),
      status: isOn,
      speed
    })
  } catch (err) {
    console.error('Lỗi khi cập nhật tốc độ quạt:', err)
  } finally {
    schedulePersistHomeState()
  }
}

function runScenario(type) {
  lockStateSync(2000)
  if (type === 'welcome') {
    if (!isApplyingState) addLog('SYSTEM', 'Kịch bản: VỀ NHÀ', 'info')
    if (!deviceStates.value['Cửa Chính']) toggleDevice('Cửa Chính', 'Scenario Auto')
    if (!deviceStates.value['Đèn Hành Lang']) toggleDevice('Đèn Hành Lang', 'Scenario Auto')
    if (!deviceStates.value['Đèn Chùm Trung Tâm']) toggleDevice('Đèn Chùm Trung Tâm', 'Scenario Auto')
    if (!deviceStates.value['Quạt Trần Phòng Khách']) toggleDevice('Quạt Trần Phòng Khách', 'Scenario Auto')
  } 
  else if (type === 'sleep') {
    if (!isApplyingState) addLog('SYSTEM', 'Kịch bản: ĐI NGỦ', 'info')
    ['Cửa Chính', 'Cửa Nhà Vệ Sinh', 'Cửa Phòng Ngủ', 'Cửa Nhà Bếp', 'Cửa Khu KT'].forEach(door => {
      if (deviceStates.value[door]) toggleDevice(door, 'Scenario Auto')
    })
    ['Đèn Hành Lang', 'Đèn Nhà Vệ Sinh', 'Đèn Chùm Trung Tâm', 'Đèn Nhà Bếp'].forEach(light => {
      if (deviceStates.value[light]) toggleDevice(light, 'Scenario Auto')
    })
    if (!deviceStates.value['Đèn Phòng Ngủ']) toggleDevice('Đèn Phòng Ngủ', 'Scenario Auto')
    ['Quạt Trần Phòng Khách'].forEach(fan => {
      if (deviceStates.value[fan]) toggleDevice(fan, 'Scenario Auto')
    })
    if (!deviceStates.value['Quạt Phòng Ngủ']) toggleDevice('Quạt Phòng Ngủ', 'Scenario Auto')
  } 
  else if (type === 'sos') {
    if (!isApplyingState) addLog('MQ2', 'Khói vượt ngưỡng / Cảnh báo Gas', 'danger')
    ['Cửa Chính', 'Cửa Nhà Vệ Sinh', 'Cửa Phòng Ngủ', 'Cửa Nhà Bếp', 'Cửa Khu KT'].forEach(door => {
      if (!deviceStates.value[door]) toggleDevice(door, 'Scenario Auto')
    })
    ['Đèn Hành Lang', 'Đèn Phòng Ngủ', 'Đèn Nhà Vệ Sinh', 'Đèn Chùm Trung Tâm', 'Đèn Nhà Bếp'].forEach(light => {
      if (!deviceStates.value[light]) toggleDevice(light, 'Scenario Auto')
    })
    ['Quạt Phòng Ngủ', 'Quạt Trần Phòng Khách'].forEach(fan => {
      if (!deviceStates.value[fan]) toggleDevice(fan, 'Scenario Auto')
    })
  } 
  else if (type === 'alloff') {
    if (!isApplyingState) addLog('SYSTEM', 'Kịch bản: TẮT HẾT', 'info')
    Object.keys(deviceStates.value).forEach(device => {
      if (deviceStates.value[device]) toggleDevice(device, 'Scenario Auto')
    })
  }
}

async function handleAICommand(command) {
  if (aiLoading.value) return

  lockStateSync(3000)
  aiLoading.value = true
  if (!isApplyingState) addLog('SYSTEM', `Đang gửi lệnh AI: "${command}"...`, 'info')
  
  try {
    const res = await axios.post(`${API}/api/ai/command`, { command })
    const data = res.data
    
    // In phản hồi của AI vào Console Log
    if (data.response) {
      if (!isApplyingState) addLog('SYSTEM', `Trợ lý AI: ${data.response}`, 'success')
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
    if (!isApplyingState) addLog('SYSTEM', `Trợ lý AI: Lỗi - ${errorMsg}`, 'danger')
  } finally {
    aiLoading.value = false
  }
}

function handleUpdateAutoFan({ enabled, threshold }) {
  autoFanEnabled.value = enabled
  autoFanThreshold.value = threshold
  if (!isApplyingState) addLog('SYSTEM', `Tự động quạt: ${enabled ? 'BẬT' : 'TẮT'} (Ngưỡng: ${threshold}°C)`, 'info')
  schedulePersistHomeState()
}

function handleUpdateAutoGas(enabled) {
  autoGasEnabled.value = enabled
  if (!isApplyingState) addLog('SYSTEM', `Tự phản ứng khi có gas: ${enabled ? 'BẬT' : 'TẮT'}`, 'info')
  schedulePersistHomeState()
}

function handleUpdateAutoMotion(enabled) {
  autoMotionEnabled.value = enabled
  if (!isApplyingState) addLog('SYSTEM', `Tự động bật thiết bị khi có người: ${enabled ? 'BẬT' : 'TẮT'}`, 'info')
  schedulePersistHomeState()
}

// Watcher tự động bật/tắt quạt theo nhiệt độ khi chế độ Auto bật
watch([() => sensors.value.temperature, autoFanEnabled, autoFanThreshold], () => {
  if (!autoFanEnabled.value || sensors.value.temperature === null || isApplyingState) return
  
  const temp = sensors.value.temperature
  const thresh = autoFanThreshold.value
  const targetFan = 'Quạt Trần Phòng Khách' // Quạt đại diện điều khiển
  
  if (temp >= thresh) {
    if (!deviceStates.value[targetFan]) {
      addLog('SYSTEM', `Nhiệt độ ${temp.toFixed(1)}°C >= ${thresh}°C. Tự động bật quạt phòng khách.`, 'warning')
      toggleDevice(targetFan, 'Climate Auto')
    }
  } else if (temp <= thresh - 2.0) {
    if (deviceStates.value[targetFan]) {
      addLog('SYSTEM', `Nhiệt độ ${temp.toFixed(1)}°C <= ${thresh - 2}°C. Tự động tắt quạt phòng khách.`, 'info')
      toggleDevice(targetFan, 'Climate Auto')
    }
  }
})

// Watcher tự động kích hoạt kịch bản SOS khi có cảnh báo Gas, và tự động tắt khi an toàn trở lại
watch(() => sensors.value.gasAlarm, (newAlarm, oldAlarm) => {
  if (!autoGasEnabled.value || isApplyingState) return
  if (newAlarm === oldAlarm) return
  if (newAlarm === true) {
    runScenario('sos')
  } else if (newAlarm === false && oldAlarm === true) {
    runScenario('alloff')
  }
})

// Watcher tự động bật đèn/quạt khi có người
watch(() => sensors.value.motion, (hasMotion) => {
  if (!autoMotionEnabled.value || isApplyingState) return
  if (hasMotion) {
    addLog('SYSTEM', 'Phát hiện chuyển động: Tự động bật quạt & đèn', 'info')
    if (!deviceStates.value['Đèn Hành Lang']) toggleDevice('Đèn Hành Lang', 'Motion Auto')
    if (!deviceStates.value['Quạt Trần Phòng Khách']) toggleDevice('Quạt Trần Phòng Khách', 'Motion Auto')
  }
})

async function pingAPI() {
  try {
    const res = await axios.get(`${API}/api/sensor/latest`)
    if (res.data && res.data.temperature !== undefined) {
      sensors.value.temperature = res.data.temperature
      sensors.value.humidity = res.data.humidity
      sensors.value.motion = res.data.pir !== undefined ? Boolean(res.data.pir) : false
      sensors.value.gasAlarm = res.data.gas_alarm !== undefined 
        ? Boolean(res.data.gas_alarm) 
        : (res.data.gas_ppm !== undefined ? (Number(res.data.gas_ppm) >= 2000) : false)
      sensors.value.gasPpm = res.data.gas_ppm !== undefined ? Number(res.data.gas_ppm) : null
      sensors.value.timestamp = res.data.timestamp || new Date().toISOString()
    }
    connected.value = true
  } catch (err) {
    connected.value = false
  }
}

let interval
let syncInterval
onMounted(() => {
  // Bootstrap FE state from BE snapshot (if any)
  syncHomeState()

  pingAPI()
  interval = setInterval(pingAPI, 5000)
  syncInterval = setInterval(syncHomeState, 1000)
  
  // Set initial boot log
  setTimeout(() => {
    addLog('SYSTEM', 'ESP32 khởi động thành công.', 'success')
    addLog('RELAY', 'Khởi tạo kênh Rơ-le thành công.', 'warning')
    addLog('SYSTEM', 'Serial 115200 sẵn sàng.', 'info')
  }, 100)

  // Auto start camera for Face ID lock screen
  startLockCamera()
})

watch(deviceStates, () => {
  if (!isApplyingState) schedulePersistHomeState()
}, { deep: true })
watch(fanSpeeds, () => {
  if (!isApplyingState) schedulePersistHomeState()
}, { deep: true })
watch(logs, () => {
  if (!isApplyingState) schedulePersistHomeState()
}, { deep: true })

onUnmounted(() => {
  clearInterval(interval)
  clearInterval(syncInterval)
  clearTimeout(persistTimer)
  stopLockCamera()
})

</script>

<style scoped>
@keyframes scan {
  0% { top: 0%; }
  50% { top: 100%; }
  100% { top: 0%; }
}
.animate-scan {
  animation: scan 2.5s ease-in-out infinite;
}
</style>

