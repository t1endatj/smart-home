<template>
  <div class="bg-[#18181c] border border-gray-800/40 rounded-2xl p-5 shadow-xl flex flex-col justify-between h-full gap-4 text-gray-200">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-gray-800/50 pb-2">
      <h3 class="text-sm font-bold text-white tracking-wider uppercase flex items-center gap-2">
        ⚙️ PANEL ĐIỀU KHIỂN
      </h3>
    </div>

    <!-- Console Monitor -->
    <div class="flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <div class="text-[10px] font-bold text-gray-500 uppercase tracking-[0.18em]">ESP32 Serial Monitor</div>
        <div class="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[9px] font-bold uppercase tracking-[0.18em] text-emerald-300">
          Live
        </div>
      </div>
      <div
        class="relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.10),transparent_40%),linear-gradient(180deg,#11131a_0%,#0b0d12_100%)] shadow-[0_18px_40px_rgba(0,0,0,0.28)]"
      >
        <div class="flex items-center justify-between border-b border-white/6 px-4 py-3">
          <div class="flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(74,222,128,0.75)]" />
            <span class="font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-100/85">Telemetry Stream</span>
          </div>
          <span class="font-mono text-[10px] text-gray-500">{{ logs.length }} entries</span>
        </div>
        <div class="pointer-events-none absolute inset-x-0 top-0 h-14 bg-gradient-to-b from-cyan-300/5 to-transparent" />
        <div ref="consoleEl" class="max-h-[250px] min-h-[220px] overflow-y-auto px-4 py-3 font-mono text-[12px] leading-5">
          <div v-if="logs.length === 0" class="rounded-xl border border-dashed border-white/8 bg-white/[0.02] px-4 py-8 text-center text-[12px] text-gray-500">
            Waiting for serial events...
          </div>
          <div
            v-for="(log, idx) in logs"
            :key="idx"
            class="mb-2 flex items-start gap-3 rounded-xl border border-white/[0.04] bg-white/[0.02] px-3 py-2.5 transition-colors hover:bg-white/[0.04]"
          >
            <span class="shrink-0 rounded-md bg-black/30 px-2 py-1 text-[11px] text-cyan-200/75">{{ log.time }}</span>
            <span
              :class="[
                'shrink-0 rounded-md px-2 py-1 text-[11px] font-bold uppercase tracking-wide',
                logTagClass(log)
              ]"
            >
              {{ log.tag }}
            </span>
            <span class="min-w-0 flex-1 whitespace-normal break-words text-[12px] font-medium text-gray-100/90">{{ log.msg }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Environment Sensors -->
    <div class="grid grid-cols-2 gap-2 bg-[#0f0f14] border border-gray-800/40 rounded-xl p-2 text-xs">
      <!-- Cột 1: Nhiệt độ -->
      <div class="flex items-center gap-2 w-full truncate">
        <span class="text-base text-orange-400">🌡️</span>
        <div>
          <div class="text-[9px] text-gray-500 font-bold uppercase leading-none">Nhiệt độ</div>
          <div class="text-xs font-bold text-white mt-0.5">{{ sensors.temperature !== null ? sensors.temperature.toFixed(1) + '°C' : '--' }}</div>
        </div>
      </div>
      
      <!-- Cột 2: Độ ẩm -->
      <div class="flex items-center gap-2 border-l border-gray-800/60 pl-2 w-full truncate">
        <span class="text-base text-cyan-400">💧</span>
        <div>
          <div class="text-[9px] text-gray-500 font-bold uppercase leading-none">Độ ẩm</div>
          <div class="text-xs font-bold text-white mt-0.5">{{ sensors.humidity !== null ? sensors.humidity.toFixed(1) + '%' : '--' }}</div>
        </div>
      </div>
      
      <!-- Cột 3: Chuyển động -->
      <div class="flex items-center gap-2 border-t border-gray-800/40 pt-2 w-full truncate">
        <span class="text-base" :class="sensors.motion ? 'text-red-400 animate-pulse' : 'text-gray-400'">
          {{ sensors.motion ? '🚶' : '👤' }}
        </span>
        <div>
          <div class="text-[9px] text-gray-500 font-bold uppercase leading-none">Chuyển động</div>
          <div 
            class="text-[9px] font-bold mt-0.5" 
            :class="sensors.motion ? 'text-red-400' : 'text-gray-400'"
          >
            {{ sensors.motion ? 'CÓ NGƯỜI' : 'TRỐNG' }}
          </div>
        </div>
      </div>
      
      <!-- Cột 4: Cảm biến Gas MQ2 -->
      <div class="flex items-center gap-2 border-l border-gray-800/60 pl-2 border-t border-gray-800/40 pt-2 w-full truncate">
        <span class="text-base" :class="sensors.gasAlarm ? 'text-red-500 animate-bounce' : 'text-gray-400'">
          ⚠️
        </span>
        <div>
          <div class="text-[9px] text-gray-500 font-bold uppercase leading-none">Khí Gas (MQ-2)</div>
          <div class="text-[9px] font-bold mt-0.5 flex gap-1 items-center">
            <span :class="sensors.gasAlarm ? 'text-red-500 font-extrabold' : 'text-green-500'">
              {{ sensors.gasAlarm ? 'CẢNH BÁO!' : 'AN TOÀN' }}
            </span>
            <span class="text-[8px] text-gray-400 font-medium tracking-wide">
              ({{ sensors.gasPpm !== null && sensors.gasPpm !== undefined ? sensors.gasPpm + ' ppm' : '--' }})
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Biểu đồ lịch sử cảm biến -->
    <div class="flex flex-col gap-1.5 border-t border-gray-800/40 pt-2">
      <div class="flex items-center justify-between">
        <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">📊 Biểu Đồ Lịch Sử</span>
        <!-- Hệ thống tab chọn biểu đồ -->
        <div class="flex bg-gray-900 border border-gray-800 rounded-lg p-0.5 gap-0.5">
          <button 
            type="button"
            @click="activeChartTab = 'temp'"
            :class="[
              'px-2 py-0.5 rounded text-[8px] font-bold uppercase transition-all cursor-pointer',
              activeChartTab === 'temp' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 'text-gray-500 hover:text-gray-300 border border-transparent'
            ]"
          >
            Nhiệt độ
          </button>
          <button 
            type="button"
            @click="activeChartTab = 'motion'"
            :class="[
              'px-2 py-0.5 rounded text-[8px] font-bold uppercase transition-all cursor-pointer',
              activeChartTab === 'motion' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-gray-500 hover:text-gray-300 border border-transparent'
            ]"
          >
            Chuyển động
          </button>
        </div>
      </div>

      <div 
        @click="openChartModal" 
        class="bg-[#0f0f14] border border-gray-800/40 rounded-xl p-2 h-[150px] flex items-center justify-center relative overflow-hidden cursor-zoom-in hover:border-orange-500/20 transition-all w-full"
        title="Bấm để xem biểu đồ phóng to"
      >
        <!-- Vùng hiển thị biểu đồ nhiệt độ -->
        <div v-show="activeChartTab === 'temp'" class="w-full h-full">
          <apexchart 
            v-if="sensorHistory.length > 0"
            height="100%"
            width="100%"
            :options="tempChartOptions" 
            :series="tempSeries"
          />
          <div v-else class="text-[10px] text-gray-600 flex items-center justify-center h-full w-full">
            Đang tải dữ liệu nhiệt độ...
          </div>
        </div>

        <!-- Vùng hiển thị biểu đồ chuyển động -->
        <div v-show="activeChartTab === 'motion'" class="w-full h-full">
          <apexchart 
            v-if="sensorHistory.length > 0"
            height="100%"
            width="100%"
            :options="motionChartOptions" 
            :series="motionSeries"
          />
          <div v-else class="text-[10px] text-gray-600 flex items-center justify-center h-full w-full">
            Đang tải dữ liệu chuyển động...
          </div>
        </div>
      </div>
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
      <div class="grid grid-cols-1 gap-2">
        <div
          v-for="fan in fansList"
          :key="fan.name"
          :class="[
            'flex flex-col gap-2 p-3 rounded-lg border transition-all',
            deviceStates[fan.name]
              ? 'bg-cyan-500/10 border-cyan-500/40 shadow-md shadow-cyan-500/5'
              : 'bg-white/[0.02] border-gray-800/60 hover:bg-white/[0.05]'
          ]"
        >
          <button
            class="flex flex-col items-start gap-0.5 active:scale-[0.98] transition-all"
            @click="$emit('toggle', fan.name)"
          >
            <span class="text-[11px] font-semibold truncate w-full text-left">{{ fan.label }}</span>
            <span :class="['text-[9px] font-bold uppercase', deviceStates[fan.name] ? 'text-cyan-400' : 'text-gray-500']">
              {{ deviceStates[fan.name] ? `ON • ${fanSpeedText(fan.name)}` : `OFF • ${fanSpeedText(fan.name)}` }}
            </span>
          </button>
          <div class="flex flex-col gap-1">
            <div class="flex items-center justify-between text-[9px] font-semibold uppercase tracking-[0.18em] text-gray-500">
              <span>10%</span>
              <span>55%</span>
              <span>100%</span>
            </div>
            <input
              :value="fanSpeeds[fan.name] || 35"
              type="range"
              min="10"
              max="100"
              step="1"
              class="h-2 w-full cursor-pointer appearance-none rounded-full border border-cyan-500/10 bg-gray-900/70 accent-cyan-400"
              :style="fanSpeedTrackStyle(fan.name)"
              @input="onFanSpeedDrag(fan.name, Number($event.target.value))"
            />
            <div class="flex items-center justify-between text-[9px] text-gray-500">
              <span>Nhẹ</span>
              <span class="font-bold text-cyan-300">{{ fanSpeedText(fan.name) }}</span>
              <span>Mạnh</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Auto Fan Control Config -->
      <div class="bg-white/[0.01] border border-gray-800/40 rounded-lg p-2 mt-1.5 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wide flex items-center gap-1">
            🌡️ Tự động theo nhiệt độ
          </span>
          <label class="relative inline-flex items-center cursor-pointer scale-90">
            <input 
              type="checkbox" 
              v-model="localAutoFanEnabled"
              class="sr-only peer"
              @change="onAutoFanChange"
            />
            <div class="w-7 h-4 bg-gray-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-gray-400 peer-checked:after:bg-purple-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-purple-600/30 peer-checked:border peer-checked:border-purple-500/40"></div>
          </label>
        </div>
        
        <div v-if="localAutoFanEnabled" class="flex flex-col gap-1 transition-all">
          <div class="flex justify-between text-[9px] text-gray-500 font-medium">
            <span>Ngưỡng kích hoạt:</span>
            <span class="text-purple-400 font-bold">{{ localAutoFanThreshold }}°C</span>
          </div>
          <input 
            type="range" 
            v-model.number="localAutoFanThreshold" 
            min="25" 
            max="40" 
            step="1"
            class="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
            @input="onAutoFanChange"
          />
        </div>
      </div>

      <div class="bg-white/[0.01] border border-gray-800/40 rounded-lg p-2 flex items-center justify-between gap-3">
        <div class="flex flex-col">
          <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wide">⚠️ Tự phản ứng gas</span>
          <span class="text-[9px] text-gray-500">Bật đèn, mở cửa và chạy SOS khi MQ-2 cảnh báo.</span>
        </div>
        <label class="relative inline-flex items-center cursor-pointer scale-90">
          <input
            type="checkbox"
            v-model="localAutoGasEnabled"
            class="sr-only peer"
            @change="onAutoGasChange"
          />
          <div class="w-7 h-4 bg-gray-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-gray-400 peer-checked:after:bg-red-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-red-600/30 peer-checked:border peer-checked:border-red-500/40"></div>
        </label>
      </div>

      <div class="bg-white/[0.01] border border-gray-800/40 rounded-lg p-2 flex items-center justify-between gap-3 mt-1.5">
        <div class="flex flex-col">
          <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wide">🏃 Tự động theo chuyển động</span>
          <span class="text-[9px] text-gray-500">Tự động bật quạt và đèn khi phát hiện có người.</span>
        </div>
        <label class="relative inline-flex items-center cursor-pointer scale-90">
          <input
            type="checkbox"
            v-model="localAutoMotionEnabled"
            class="sr-only peer"
            @change="onAutoMotionChange"
          />
          <div class="w-7 h-4 bg-gray-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-gray-400 peer-checked:after:bg-cyan-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-cyan-600/30 peer-checked:border peer-checked:border-cyan-500/40"></div>
        </label>
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

    <!-- Xác Thực Face ID (Face Recognition) -->
    <div class="flex flex-col gap-1.5 border-t border-gray-800/40 pt-2">
      <div class="flex items-center justify-between">
        <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">📸 Xác Thực Face ID</span>
        <span class="text-[8px] text-gray-500 font-medium">So khớp ảnh mẫu trong BE/faces/</span>
      </div>
      
      <div class="flex flex-col gap-2 bg-white/[0.01] border border-gray-800/40 rounded-lg p-2">
        <!-- Preview camera hoặc placeholder -->
        <div 
          @click="openCameraModal" 
          class="relative overflow-hidden rounded-lg bg-black aspect-video flex items-center justify-center border border-gray-800 cursor-zoom-in hover:border-cyan-500/30 transition-all"
          title="Bấm để phóng to camera"
        >
          <video 
            v-show="cameraActive" 
            ref="videoEl" 
            autoplay 
            playsinline 
            muted
            class="w-full h-full object-cover"
          />
          <div v-show="!cameraActive" class="text-center p-4 text-[10px] text-gray-500 flex flex-col items-center gap-1">
            <span>📷 Camera đang tắt</span>
            <span class="text-[8px] text-gray-600">Bấm "Mở Camera" để bắt đầu quét khuôn mặt</span>
          </div>
          
          <!-- Lớp phủ trạng thái -->
          <div 
            v-if="faceStatus" 
            :class="[
              'absolute inset-0 flex items-center justify-center text-xs font-bold text-center px-4 backdrop-blur-sm transition-all',
              faceStatus === 'processing' ? 'bg-black/60 text-cyan-300' : '',
              faceStatus === 'success' ? 'bg-emerald-950/85 text-emerald-300' : '',
              faceStatus === 'failed' ? 'bg-red-950/85 text-red-300' : ''
            ]"
          >
            <div class="flex flex-col items-center gap-1">
              <span v-if="faceStatus === 'processing'" class="animate-spin text-lg">🔄</span>
              <span v-if="faceStatus === 'success'" class="text-lg">✅</span>
              <span v-if="faceStatus === 'failed'" class="text-lg">❌</span>
              <span>{{ faceStatusText }}</span>
            </div>
          </div>
        </div>

        <!-- Các nút điều khiển camera & Face ID -->
        <div class="flex gap-1.5">
          <button 
            type="button"
            @click="cameraActive ? stopCamera() : startCamera()"
            :class="[
              'flex-1 py-1.5 rounded-lg text-[10px] font-bold transition-all text-center border cursor-pointer',
              cameraActive 
                ? 'bg-gray-800 hover:bg-gray-700 border-gray-700 text-gray-300' 
                : 'bg-cyan-600/10 hover:bg-cyan-600/20 border-cyan-500/30 text-cyan-300'
            ]"
          >
            {{ cameraActive ? 'Tắt Camera' : 'Mở Camera' }}
          </button>
          
          <button 
            v-if="cameraActive"
            type="button"
            @click="verifyFaceCapture"
            class="flex-1 bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 py-1.5 rounded-lg text-[10px] font-bold transition-all text-center cursor-pointer"
          >
            Quét Khuôn Mặt
          </button>
        </div>
      </div>
    </div>



    <!-- AI Command Input -->
    <div class="flex flex-col gap-1 border-t border-gray-800/40 pt-2 mt-0.5">
      <div class="text-[10px] font-bold text-gray-500 uppercase tracking-wide">🤖 Trợ lý AI</div>
      <form @submit.prevent="submitCommand" class="flex gap-2 items-center">
        <!-- Nút Micro giọng nói -->
        <button
          type="button"
          @click="toggleVoiceRecognition"
          :class="[
            'p-2 rounded-lg border text-xs transition-all active:scale-95 shrink-0 flex items-center justify-center h-8 w-8',
            isListening 
              ? 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse shadow-md shadow-red-500/10' 
              : (speechSupported ? 'bg-white/[0.02] border-gray-800/80 hover:bg-white/[0.05] text-gray-400' : 'bg-gray-900/60 border-gray-800/80 text-gray-600 cursor-not-allowed')
          ]"
          :title="!speechSupported ? 'Trình duyệt không hỗ trợ nhận diện giọng nói' : (isListening ? 'Đang lắng nghe... Click để dừng' : 'Ra lệnh bằng giọng nói')"
          :disabled="aiLoading || !speechSupported"
        >
          <span>🎙️</span>
        </button>

        <input 
          v-model="commandText"
          type="text" 
          :placeholder="isListening ? 'Đang nghe giọng nói của bạn...' : 'Nhập lệnh hoặc dùng giọng nói...'" 
          class="flex-1 bg-[#0f0f14] border border-gray-800/80 focus:border-purple-500/50 rounded-lg px-2.5 py-1.5 text-[11px] outline-none transition-all placeholder-gray-600 text-gray-200 h-8"
          :disabled="aiLoading || isListening"
        />
        <button 
          type="submit" 
          class="bg-purple-600/10 hover:bg-purple-600/20 active:scale-95 border border-purple-500/30 text-purple-300 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all flex items-center gap-1 shrink-0 h-8"
          :disabled="aiLoading || isListening || !commandText.trim()"
        >
          <span v-if="aiLoading" class="animate-spin text-[8px]">🔄</span>
          <span>Gửi</span>
        </button>
      </form>
    </div>

    <!-- Camera Modal Overlay -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div 
        v-if="isCameraModalOpen" 
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4"
        @click.self="closeCameraModal"
      >
        <div class="relative w-full max-w-2xl max-h-[90vh] bg-[#18181c] border border-gray-800/80 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
          <!-- Modal Header -->
          <div class="flex items-center justify-between border-b border-gray-800 px-4 py-3 bg-[#131316] shrink-0">
            <h3 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              📷 Camera Face ID (Phóng to)
            </h3>
            <button 
              type="button" 
              @click="closeCameraModal" 
              class="text-gray-400 hover:text-white text-sm font-bold p-1 cursor-pointer"
            >
              ✕
            </button>
          </div>

          <!-- Video content -->
          <div class="relative flex-1 bg-black flex items-center justify-center overflow-hidden min-h-0">
            <video 
              ref="videoElModal" 
              autoplay 
              playsinline 
              muted 
              class="w-full h-full max-h-[55vh] object-contain"
            />
            
            <!-- Lớp phủ trạng thái -->
            <div 
              v-if="faceStatus" 
              :class="[
                'absolute inset-0 flex items-center justify-center text-xs font-bold text-center px-6 backdrop-blur-sm transition-all',
                faceStatus === 'processing' ? 'bg-black/60 text-cyan-300' : '',
                faceStatus === 'success' ? 'bg-emerald-950/85 text-emerald-300' : '',
                faceStatus === 'failed' ? 'bg-red-950/85 text-red-300' : ''
              ]"
            >
              <div class="flex flex-col items-center gap-1.5">
                <span v-if="faceStatus === 'processing'" class="animate-spin text-lg">🔄</span>
                <span v-if="faceStatus === 'success'" class="text-lg">✅</span>
                <span v-if="faceStatus === 'failed'" class="text-lg">❌</span>
                <span class="text-xs">{{ faceStatusText }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="p-3 flex gap-2.5 bg-[#111113] border-t border-gray-800/80 shrink-0">
            <button 
              type="button"
              @click="cameraActive ? stopCameraFromModal() : startCamera()"
              class="flex-1 py-1.5 rounded-lg text-[10px] font-bold bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 cursor-pointer"
            >
              {{ cameraActive ? 'Tắt Camera' : 'Mở Camera' }}
            </button>
            <button 
              v-if="cameraActive"
              type="button"
              @click="verifyFaceCapture"
              class="flex-1 py-1.5 rounded-lg text-[10px] font-bold bg-emerald-600/15 hover:bg-emerald-600/25 text-emerald-300 border border-emerald-500/30 cursor-pointer"
            >
              Quét Khuôn Mặt
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Chart Modal Overlay -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div 
        v-if="isChartModalOpen" 
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4"
        @click.self="closeChartModal"
      >
        <div class="relative w-full max-w-3xl max-h-[90vh] bg-[#18181c] border border-gray-800/80 rounded-2xl p-5 shadow-2xl flex flex-col gap-4 overflow-hidden">
          <!-- Modal Header -->
          <div class="flex items-center justify-between border-b border-gray-800/80 pb-3 shrink-0">
            <h3 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              📊 Biểu đồ lịch sử cảm biến (Phóng to)
            </h3>
            
            <div class="flex items-center gap-4">
              <!-- Tab selection inside modal -->
              <div class="flex bg-gray-900 border border-gray-800 rounded-lg p-0.5 gap-0.5">
                <button 
                  type="button"
                  @click="activeChartTab = 'temp'"
                  :class="[
                    'px-2.5 py-0.5 rounded text-[9px] font-bold uppercase transition-all cursor-pointer',
                    activeChartTab === 'temp' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 'text-gray-500 hover:text-gray-300 border border-transparent'
                  ]"
                >
                  Nhiệt độ
                </button>
                <button 
                  type="button"
                  @click="activeChartTab = 'motion'"
                  :class="[
                    'px-2.5 py-0.5 rounded text-[9px] font-bold uppercase transition-all cursor-pointer',
                    activeChartTab === 'motion' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-gray-500 hover:text-gray-300 border border-transparent'
                  ]"
                >
                  Chuyển động
                </button>
              </div>

              <button 
                type="button" 
                @click="closeChartModal" 
                class="text-gray-400 hover:text-white text-sm font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>

          <!-- Enlarged Chart Content -->
          <div class="bg-[#0f0f14] border border-gray-800/40 rounded-xl p-3 flex-1 h-[300px] max-h-[50vh] flex items-center justify-center relative overflow-hidden min-h-0">
            <div v-show="activeChartTab === 'temp'" class="w-full h-full">
              <apexchart 
                v-if="sensorHistory.length > 0"
                height="100%"
                width="100%"
                :options="tempChartOptionsModal" 
                :series="tempSeries"
              />
              <div v-else class="text-[10px] text-gray-500 flex items-center justify-center h-full w-full">
                Đang tải dữ liệu nhiệt độ...
              </div>
            </div>

            <div v-show="activeChartTab === 'motion'" class="w-full h-full">
              <apexchart 
                v-if="sensorHistory.length > 0"
                height="100%"
                width="100%"
                :options="motionChartOptionsModal" 
                :series="motionSeries"
              />
              <div v-else class="text-[10px] text-gray-500 flex items-center justify-center h-full w-full">
                Đang tải dữ liệu chuyển động...
              </div>
            </div>
          </div>
          
          <!-- Tip -->
          <div class="text-[9px] text-gray-500 text-center uppercase tracking-wide">
            💡 Rê chuột vào các điểm dữ liệu để xem thông số chi tiết
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  deviceStates: {
    type: Object,
    required: true
  },
  fanSpeeds: {
    type: Object,
    default: () => ({})
  },
  logs: {
    type: Array,
    default: () => []
  },
  aiLoading: {
    type: Boolean,
    default: false
  },
  sensors: {
    type: Object,
    default: () => ({ temperature: null, humidity: null, motion: false, gasAlarm: false, gasPpm: null })
  },
  autoFanEnabled: {
    type: Boolean,
    default: false
  },
  autoFanThreshold: {
    type: Number,
    default: 32
  },
  autoGasEnabled: {
    type: Boolean,
    default: true
  },
  autoMotionEnabled: {
    type: Boolean,
    default: false
  },
  voiceStopRequest: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['toggle', 'set-fan-speed', 'scenario', 'ai-command', 'add-log', 'voice-state', 'update-auto-fan', 'update-auto-gas', 'update-auto-motion'])

const commandText = ref('')
const isListening = ref(false)
const speechSupported = ref(false)
const liveTranscript = ref('')
let recognition = null

const localAutoFanEnabled = ref(props.autoFanEnabled)
const localAutoFanThreshold = ref(props.autoFanThreshold)
const localAutoGasEnabled = ref(props.autoGasEnabled)
const localAutoMotionEnabled = ref(props.autoMotionEnabled)

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const activeChartTab = ref('temp')
const sensorHistory = ref([])

async function fetchSensorHistory() {
  try {
    const res = await axios.get(`${API}/api/sensor?limit=20`)
    if (res.data && Array.isArray(res.data)) {
      sensorHistory.value = res.data.reverse().map(item => ({
        temperature: item.temperature,
        humidity: item.humidity,
        pir: item.pir !== undefined ? Boolean(item.pir) : false,
        gas_ppm: item.gas_ppm,
        gas_alarm: item.gas_alarm,
        timestamp: item.timestamp
      }))
    }
  } catch (err) {
    console.error('Lỗi khi tải lịch sử cảm biến:', err)
  }
}

const cameraActive = ref(false)
const videoEl = ref(null)
const faceStatus = ref(null)
const faceStatusText = ref('')
let stream = null

const isChartModalOpen = ref(false)
const isCameraModalOpen = ref(false)
const videoElModal = ref(null)

function openChartModal() {
  isChartModalOpen.value = true
}

function closeChartModal() {
  isChartModalOpen.value = false
}

function openCameraModal() {
  if (!cameraActive.value) return
  isCameraModalOpen.value = true
  nextTick(() => {
    if (videoElModal.value && stream) {
      videoElModal.value.srcObject = stream
      videoElModal.value.play().catch(e => console.error("Error playing modal video:", e))
    }
  })
}

function closeCameraModal() {
  isCameraModalOpen.value = false
  nextTick(() => {
    if (videoEl.value && stream) {
      videoEl.value.srcObject = stream
      videoEl.value.play().catch(e => console.error("Error playing small video:", e))
    }
  })
}

function stopCameraFromModal() {
  stopCamera()
  closeCameraModal()
}


async function startCamera() {
  faceStatus.value = null
  faceStatusText.value = ''
  try {
    cameraActive.value = true
    const mediaStream = await navigator.mediaDevices.getUserMedia({ 
      video: { width: 640, height: 480 } 
    })
    stream = mediaStream
    if (videoEl.value) {
      videoEl.value.srcObject = mediaStream
      videoEl.value.play().catch(err => console.error('Error playing video:', err))
    }
    emit('add-log', { tag: 'SYSTEM', msg: 'Đã mở camera thành công.', type: 'info' })
  } catch (err) {
    cameraActive.value = false
    console.error('Lỗi mở camera:', err)
    emit('add-log', { tag: 'SYSTEM', msg: 'Lỗi: Không truy cập được Camera.', type: 'danger' })
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  cameraActive.value = false
  if (videoEl.value) {
    videoEl.value.srcObject = null
  }
}

async function verifyFaceCapture() {
  const activeVideo = isCameraModalOpen.value ? videoElModal.value : videoEl.value
  if (!activeVideo) return

  faceStatus.value = 'processing'
  faceStatusText.value = 'Đang quét khuôn mặt...'
  emit('add-log', { tag: 'SYSTEM', msg: 'Đang chụp ảnh so khớp khuôn mặt...', type: 'info' })

  try {
    const canvas = document.createElement('canvas')
    canvas.width = activeVideo.videoWidth || 640
    canvas.height = activeVideo.videoHeight || 480
    const ctx = canvas.getContext('2d')
    ctx.drawImage(activeVideo, 0, 0, canvas.width, canvas.height)
    
    const base64Image = canvas.toDataURL('image/jpeg', 0.8)
    
    const res = await axios.post(`${API}/api/face/verify`, {
      image: base64Image
    })

    if (res.data && res.data.result === true) {
      const matchedName = res.data.name || 'Thành viên'
      faceStatus.value = 'success'
      faceStatusText.value = `Xác thực thành công! Xin chào ${matchedName}.`
      emit('add-log', { tag: 'SYSTEM', msg: `Face ID: Khớp thành công: "${matchedName}". Đang mở cửa chính.`, type: 'success' })
      
      // Mở cửa chính nếu đang khóa
      if (props.deviceStates['Cửa Chính'] === false) {
        emit('toggle', 'Cửa Chính')
      }
      
      setTimeout(() => {
        stopCamera()
        closeCameraModal()
        faceStatus.value = null
      }, 2500)
    } else {
      const errMsg = res.data.message || res.data.error || 'Khuôn mặt không trùng khớp.'
      faceStatus.value = 'failed'
      faceStatusText.value = 'Xác thực thất bại! Không tìm thấy mẫu khớp.'
      emit('add-log', { tag: 'SYSTEM', msg: `Face ID: Xác thực thất bại - ${errMsg}`, type: 'danger' })
      
      setTimeout(() => {
        if (cameraActive.value) faceStatus.value = null
      }, 3000)
    }
  } catch (err) {
    console.error('Lỗi xác thực khuôn mặt:', err)
    faceStatus.value = 'failed'
    faceStatusText.value = 'Lỗi hệ thống khi so khớp.'
    emit('add-log', { tag: 'SYSTEM', msg: 'Face ID: Lỗi kết nối máy chủ.', type: 'danger' })
    
    setTimeout(() => {
      if (cameraActive.value) faceStatus.value = null
    }, 3000)
  }
}


onUnmounted(() => {
  stopCamera()
})

onMounted(() => {
  fetchSensorHistory()
})

watch(() => props.sensors, (newVal) => {
  if (newVal && newVal.timestamp) {
    const exists = sensorHistory.value.some(item => item.timestamp === newVal.timestamp)
    if (!exists) {
      sensorHistory.value.push({
        temperature: newVal.temperature,
        humidity: newVal.humidity,
        pir: newVal.motion,
        gas_ppm: newVal.gasPpm,
        gas_alarm: newVal.gasAlarm,
        timestamp: newVal.timestamp
      })
      if (sensorHistory.value.length > 30) {
        sensorHistory.value.shift()
      }
    }
  }
}, { deep: true })

const tempChartOptions = computed(() => ({
  chart: {
    id: 'temp-chart',
    type: 'area',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, easing: 'linear', dynamicAnimation: { speed: 800 } }
  },
  colors: ['#f97316'],
  dataLabels: {
    enabled: false
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.35,
      opacityTo: 0.02,
      stops: [20, 100]
    }
  },
  stroke: { curve: 'smooth', width: 2 },
  grid: {
    borderColor: '#1f2937',
    strokeDashArray: 3,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } }
  },
  xaxis: {
    categories: sensorHistory.value.map(item => {
      if (!item.timestamp) return ''
      const parts = String(item.timestamp).split(' ')
      return parts.length > 1 ? parts[1] : String(item.timestamp)
    }),
    labels: {
      show: true,
      style: { colors: '#6b7280', fontSize: '8px' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: {
      style: { colors: '#6b7280', fontSize: '8px' },
      formatter: (val) => `${val.toFixed(1)}°C`
    }
  },
  tooltip: {
    theme: 'dark',
    x: { show: true }
  }
}))

const tempSeries = computed(() => [{
  name: 'Nhiệt độ',
  data: sensorHistory.value.map(item => item.temperature)
}])

const motionChartOptions = computed(() => ({
  chart: {
    id: 'motion-chart',
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true }
  },
  colors: ['#10b981'],
  dataLabels: {
    enabled: false
  },
  plotOptions: {
    bar: {
      columnWidth: '50%',
      borderRadius: 1
    }
  },
  grid: {
    borderColor: '#1f2937',
    strokeDashArray: 3,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } }
  },
  xaxis: {
    categories: sensorHistory.value.map(item => {
      if (!item.timestamp) return ''
      const parts = String(item.timestamp).split(' ')
      return parts.length > 1 ? parts[1] : String(item.timestamp)
    }),
    labels: {
      show: true,
      style: { colors: '#6b7280', fontSize: '8px' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    tickAmount: 1,
    min: 0,
    max: 1,
    labels: {
      style: { colors: '#6b7280', fontSize: '8px' },
      formatter: (val) => val === 1 ? 'CÓ NGƯỜI' : 'TRỐNG'
    }
  },
  tooltip: {
    theme: 'dark',
    x: { show: true },
    y: {
      formatter: (val) => val === 1 ? 'Phát hiện chuyển động' : 'Không có chuyển động'
    }
  }
}))

const motionSeries = computed(() => [{
  name: 'Chuyển động',
  data: sensorHistory.value.map(item => item.pir ? 1 : 0)
}])

const tempChartOptionsModal = computed(() => {
  const base = tempChartOptions.value
  return {
    ...base,
    chart: {
      ...base.chart,
      id: 'temp-chart-modal'
    },
    xaxis: {
      ...base.xaxis,
      labels: {
        ...base.xaxis.labels,
        style: { ...base.xaxis.labels.style, fontSize: '10px' }
      }
    },
    yaxis: {
      ...base.yaxis,
      labels: {
        ...base.yaxis.labels,
        style: { ...base.yaxis.labels.style, fontSize: '10px' }
      }
    }
  }
})

const motionChartOptionsModal = computed(() => {
  const base = motionChartOptions.value
  return {
    ...base,
    chart: {
      ...base.chart,
      id: 'motion-chart-modal'
    },
    xaxis: {
      ...base.xaxis,
      labels: {
        ...base.xaxis.labels,
        style: { ...base.xaxis.labels.style, fontSize: '10px' }
      }
    },
    yaxis: {
      ...base.yaxis,
      labels: {
        ...base.yaxis.labels,
        style: { ...base.yaxis.labels.style, fontSize: '10px' }
      }
    }
  }
})


watch(() => props.autoFanEnabled, (val) => { localAutoFanEnabled.value = val })
watch(() => props.autoFanThreshold, (val) => { localAutoFanThreshold.value = val })
watch(() => props.autoGasEnabled, (val) => { localAutoGasEnabled.value = val })
watch(() => props.autoMotionEnabled, (val) => { localAutoMotionEnabled.value = val })

function onAutoFanChange() {
  emit('update-auto-fan', {
    enabled: localAutoFanEnabled.value,
    threshold: localAutoFanThreshold.value
  })
}

function onAutoGasChange() {
  emit('update-auto-gas', localAutoGasEnabled.value)
}

function onAutoMotionChange() {
  emit('update-auto-motion', localAutoMotionEnabled.value)
}

// Initialize SpeechRecognition if browser supported
if (typeof window !== 'undefined') {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SpeechRecognition) {
    speechSupported.value = true
    recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.lang = 'vi-VN'
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      isListening.value = true
      liveTranscript.value = ''
      emit('voice-state', { isListening: true, transcript: '', supported: true })
      emit('add-log', { tag: 'SYSTEM', msg: 'Đang lắng nghe giọng nói...', type: 'info' })
    }

    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const phrase = event.results[index][0].transcript.trim()
        if (event.results[index].isFinal) {
          finalTranscript = `${finalTranscript} ${phrase}`.trim()
        } else {
          interimTranscript = `${interimTranscript} ${phrase}`.trim()
        }
      }

      liveTranscript.value = finalTranscript || interimTranscript
      emit('voice-state', {
        isListening: true,
        transcript: liveTranscript.value,
        supported: true
      })

      if (finalTranscript) {
        commandText.value = finalTranscript
        emit('add-log', { tag: 'SYSTEM', msg: `Nhận diện: "${commandText.value}"`, type: 'success' })
        submitCommand()
      }
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      isListening.value = false
      let msg = 'Lỗi nhận diện giọng nói.'
      if (event.error === 'not-allowed') {
        msg = 'Lỗi: Trình duyệt bị từ chối quyền truy cập Micro.'
      } else if (event.error === 'no-speech') {
        msg = 'Lỗi: Không nghe thấy giọng nói.'
      }
      emit('voice-state', { isListening: false, transcript: '', supported: true })
      emit('add-log', { tag: 'SYSTEM', msg, type: 'danger' })
    }

    recognition.onend = () => {
      isListening.value = false
      liveTranscript.value = ''
      emit('voice-state', { isListening: false, transcript: '', supported: true })
    }
  }
}

function toggleVoiceRecognition() {
  if (!recognition) {
    emit('voice-state', { isListening: false, transcript: '', supported: false })
    emit('add-log', {
      tag: 'SYSTEM',
      msg: 'Trình duyệt không hỗ trợ nhận diện giọng nói. Hãy thử Chrome hoặc Edge.',
      type: 'danger'
    })
    return
  }

  if (isListening.value) {
    recognition.stop()
  } else {
    commandText.value = ''
    liveTranscript.value = ''
    try {
      recognition.start()
    } catch (e) {
      console.error(e)
    }
  }
}

function submitCommand() {
  if (!commandText.value.trim() || props.aiLoading) return
  emit('ai-command', commandText.value.trim())
  commandText.value = ''
}

function logTagClass(log) {
  if (log.tag === 'ALERT') return 'bg-red-500/15 text-red-300'
  if (log.tag === 'MQ2') return log.type === 'danger' ? 'bg-red-500/15 text-red-300' : 'bg-emerald-500/15 text-emerald-300'
  if (log.tag === 'RELAY') return 'bg-amber-500/15 text-amber-300'
  if (log.tag === 'FAN') return 'bg-cyan-500/15 text-cyan-300'
  if (log.tag === 'LIGHT') return 'bg-yellow-500/15 text-yellow-300'
  if (log.tag === 'DOOR') return 'bg-green-500/15 text-green-300'
  if (log.tag === 'SYSTEM') return 'bg-violet-500/15 text-violet-300'
  return 'bg-white/10 text-gray-300'
}

function fanSpeedText(fanName) {
  const speed = Number(props.fanSpeeds?.[fanName] || 35)
  if (speed <= 35) return `${speed}% • NHẸ`
  if (speed <= 70) return `${speed}% • VỪA`
  return `${speed}% • MẠNH`
}

function fanSpeedTrackStyle(fanName) {
  const speed = Number(props.fanSpeeds?.[fanName] || 35)
  const percent = ((speed - 10) / 90) * 100
  return {
    background: `linear-gradient(90deg, rgba(34,211,238,0.45) 0%, rgba(34,211,238,0.9) ${percent}%, rgba(17,24,39,0.9) ${percent}%, rgba(17,24,39,0.9) 100%)`
  }
}

function onFanSpeedDrag(fanName, speed) {
  emit('set-fan-speed', { name: fanName, speed, shouldTurnOn: true })
}



const consoleEl = ref(null)

const lightsList = [
  { name: 'Đèn Hành Lang', label: 'Hành Lang' },
  { name: 'Đèn Phòng Ngủ', label: 'Phòng Ngủ' },
  { name: 'Đèn Nhà Vệ Sinh', label: 'Vệ Sinh' },
  { name: 'Đèn Chùm Trung Tâm', label: 'Phòng Khách' },
  { name: 'Đèn Nhà Bếp', label: 'Nhà Bếp' }
]

const fansList = [
  { name: 'Quạt Phòng Ngủ', label: 'Phòng Ngủ' },
  { name: 'Quạt Trần Phòng Khách', label: 'P. Khách' }
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

watch(() => props.voiceStopRequest, () => {
  if (recognition && isListening.value) {
    recognition.stop()
  }
})
</script>
