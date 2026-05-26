<template>
  <div class="bg-[#18181c] border border-gray-800/40 rounded-2xl p-5 shadow-xl flex flex-col justify-between h-full gap-4 text-gray-200">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-gray-800/50 pb-2">
      <h3 class="text-sm font-bold text-white tracking-wider uppercase flex items-center gap-2">
        ⚙️ PANEL ĐIỀU KHIỂN
      </h3>
    </div>

    <!-- Scenarios -->
    <div class="flex flex-col gap-1.5">
      <div class="grid grid-cols-4 gap-1.5">
        <button 
          class="text-[10px] font-bold py-2 px-1 rounded-lg border border-purple-500/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 active:scale-95 transition-all uppercase text-center truncate"
          @click="$emit('scenario', 'welcome')"
        >
          🏠 Về Nhà
        </button>
        <button 
          class="text-[10px] font-bold py-2 px-1 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 active:scale-95 transition-all uppercase text-center truncate"
          @click="$emit('scenario', 'sleep')"
        >
          🌙 Đi Ngủ
        </button>
        <button 
          class="text-[10px] font-bold py-2 px-1 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 active:scale-95 transition-all uppercase text-center truncate"
          @click="$emit('scenario', 'sos')"
        >
          🚨 SOS
        </button>
        <button 
          class="text-[10px] font-bold py-2 px-1 rounded-lg border border-gray-700 bg-gray-800/40 text-gray-300 hover:bg-gray-800/60 active:scale-95 transition-all uppercase text-center truncate"
          @click="$emit('scenario', 'alloff')"
        >
          🔌 Tắt Hết
        </button>
      </div>
    </div>

    <!-- Lights -->
    <div class="flex flex-col gap-1.5">
      <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">💡 Hệ thống Đèn</div>
      <div class="grid grid-cols-3 gap-1.5">
        <button 
          v-for="light in lightsList" 
          :key="light.name"
          @click="$emit('toggle', light.name)"
          :class="[
            'flex flex-col items-start gap-0.5 p-2 rounded-lg border transition-all active:scale-[0.98]',
            deviceStates[light.name] 
              ? 'bg-yellow-500/10 border-yellow-500/40 shadow-md shadow-yellow-500/5' 
              : 'bg-white/[0.02] border-gray-800/60 hover:bg-white/[0.05]'
          ]"
        >
          <span class="text-[11px] font-semibold truncate w-full text-left">{{ light.label }}</span>
          <span :class="['text-[9px] font-bold uppercase', deviceStates[light.name] ? 'text-yellow-400' : 'text-gray-500']">
            {{ deviceStates[light.name] ? 'ON' : 'OFF' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Fans -->
    <div class="flex flex-col gap-1.5">
      <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">🌀 Hệ thống Quạt</div>
      <div class="grid grid-cols-3 gap-1.5">
        <button 
          v-for="fan in fansList" 
          :key="fan.name"
          @click="$emit('toggle', fan.name)"
          :class="[
            'flex flex-col items-start gap-0.5 p-2 rounded-lg border transition-all active:scale-[0.98]',
            deviceStates[fan.name] 
              ? 'bg-cyan-500/10 border-cyan-500/40 shadow-md shadow-cyan-500/5' 
              : 'bg-white/[0.02] border-gray-800/60 hover:bg-white/[0.05]'
          ]"
        >
          <span class="text-[11px] font-semibold truncate w-full text-left">{{ fan.label }}</span>
          <span :class="['text-[9px] font-bold uppercase', deviceStates[fan.name] ? 'text-cyan-400' : 'text-gray-500']">
            {{ deviceStates[fan.name] ? 'ON' : 'OFF' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Doors -->
    <div class="flex flex-col gap-1.5">
      <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">🚪 Khóa & Cửa</div>
      <div class="grid grid-cols-3 gap-1.5">
        <button 
          v-for="door in doorsList" 
          :key="door.name"
          @click="$emit('toggle', door.name)"
          :class="[
            'flex flex-col items-start gap-0.5 p-2 rounded-lg border transition-all active:scale-[0.98]',
            deviceStates[door.name] 
              ? 'bg-green-500/10 border-green-500/40 shadow-md shadow-green-500/5' 
              : 'bg-white/[0.02] border-gray-800/60 hover:bg-white/[0.05]'
          ]"
        >
          <span class="text-[11px] font-semibold truncate w-full text-left">{{ door.label }}</span>
          <span :class="['text-[9px] font-bold uppercase', deviceStates[door.name] ? 'text-green-400' : 'text-gray-500']">
            {{ deviceStates[door.name] ? 'OPEN' : 'CLOSED' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Console Monitor -->
    <div class="flex flex-col gap-1.5 mt-0.5">
      <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">📟 ESP32 Serial Monitor</div>
      <div 
        ref="consoleEl" 
        class="bg-[#0f0f14] border border-gray-800/80 rounded-lg h-[90px] overflow-y-auto font-mono text-[10px] p-2.5 shadow-inner flex flex-col gap-1.5"
      >
        <div v-if="logs.length === 0" class="text-gray-500">[System initialization...]</div>
        <div 
          v-for="(log, idx) in logs" 
          :key="idx" 
          class="flex items-start gap-2.5 leading-none"
        >
          <span class="text-gray-600 select-none shrink-0">{{ log.time }}</span>
          <span 
            :class="[
              'font-bold shrink-0 min-w-[55px] text-left',
              log.tag === 'ALERT' ? 'text-red-500' : '',
              log.tag === 'MQ2' ? (log.type === 'danger' ? 'text-red-500' : 'text-green-500') : '',
              log.tag === 'RELAY' ? 'text-amber-500' : '',
              log.tag === 'FAN' ? 'text-green-500' : '',
              log.tag === 'LIGHT' ? 'text-yellow-500' : '',
              log.tag === 'DOOR' ? 'text-emerald-500' : '',
              log.tag === 'SYSTEM' ? 'text-purple-400' : ''
            ]"
          >
            [{{ log.tag }}]
          </span>
          <span class="text-gray-300 font-medium truncate flex-1 text-left">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  deviceStates: {
    type: Object,
    required: true
  },
  logs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['toggle', 'scenario'])

const consoleEl = ref(null)

const lightsList = [
  { name: 'Đèn Hành Lang', label: 'Hành Lang' },
  { name: 'Đèn Phòng Ngủ', label: 'Phòng Ngủ' },
  { name: 'Đèn Nhà Vệ Sinh', label: 'Vệ Sinh' },
  { name: 'Đèn Chùm Trung Tâm', label: 'Phòng Khách' },
  { name: 'Đèn Nhà Bếp', label: 'Nhà Bếp' },
  { name: 'Đèn Khu KT', label: 'Khu Kỹ Thuật' }
]

const fansList = [
  { name: 'Quạt Phòng Ngủ', label: 'Phòng Ngủ' },
  { name: 'Quạt Trần Phòng Khách', label: 'P. Khách' },
  { name: 'Quạt Nhà Bếp', label: 'Nhà Bếp' }
]

const doorsList = [
  { name: 'Cửa Chính', label: 'Cửa Chính' },
  { name: 'Cửa Nhà Vệ Sinh', label: 'Cửa Vệ Sinh' },
  { name: 'Cửa Phòng Ngủ', label: 'Cửa Phòng Ngủ' },
  { name: 'Cửa Nhà Bếp', label: 'Cửa Nhà Bếp' },
  { name: 'Cửa Khu KT', label: 'Cửa Khu KT' }
]


// Auto scroll console log to bottom
watch(() => props.logs, () => {
  nextTick(() => {
    if (consoleEl.value) {
      consoleEl.value.scrollTop = consoleEl.value.scrollHeight
    }
  })
}, { deep: true })
</script>