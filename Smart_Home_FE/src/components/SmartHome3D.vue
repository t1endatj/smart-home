<template>
  <div class="relative w-full h-[600px] bg-[#121214] rounded-2xl overflow-hidden border border-gray-800/20 shadow-xl flex flex-col">
    <!-- View Options Header inside canvas -->
    <div id="controls" class="absolute top-4 left-4 right-4 z-10 flex gap-2 justify-center pointer-events-none">
      <button 
        id="btn-persp" 
        :class="['pointer-events-auto text-xs px-4 py-2 rounded-lg font-semibold border transition-all', viewMode === 'persp' ? 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-900/60 border-gray-700/50 text-gray-300 backdrop-blur-md hover:bg-gray-800/80']" 
        @click="changeView('persp')"
      >
        Góc nhìn 3D
      </button>
      <button 
        id="btn-top" 
        :class="['pointer-events-auto text-xs px-4 py-2 rounded-lg font-semibold border transition-all', viewMode === 'top' ? 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-900/60 border-gray-700/50 text-gray-300 backdrop-blur-md hover:bg-gray-800/80']" 
        @click="changeView('top')"
      >
        Mặt bằng 2D
      </button>
      <button 
        id="btn-front" 
        :class="['pointer-events-auto text-xs px-4 py-2 rounded-lg font-semibold border transition-all', viewMode === 'front' ? 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-900/60 border-gray-700/50 text-gray-300 backdrop-blur-md hover:bg-gray-800/80']" 
        @click="changeView('front')"
      >
        Nhìn từ trước
      </button>
      <button 
        class="pointer-events-auto text-xs px-4 py-2 rounded-lg font-semibold bg-gray-900/60 border border-gray-700/50 text-gray-300 backdrop-blur-md hover:bg-gray-800/80 transition-all" 
        @click="resetCam"
      >
        ↺ Đặt lại
      </button>
    </div>

    <!-- Three.js Canvas -->
    <div ref="container" class="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">
      <canvas ref="canvasEl" class="w-full h-full block"></canvas>
      
      <!-- Interactive Tooltip -->
      <div 
        ref="tooltipEl" 
        class="absolute hidden bg-gray-950/90 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 pointer-events-none z-20 backdrop-blur-md shadow-2xl max-w-[220px] line-height-relaxed"
      >
      </div>
    </div>

    <!-- Color Legend Footer inside canvas -->
    <div id="legend" class="absolute bottom-4 left-4 right-4 z-10 flex gap-4 text-[11px] text-gray-400 justify-center flex-wrap pointer-events-none">
      <div class="flex items-center gap-1.5 backdrop-blur-sm bg-black/20 px-2.5 py-1 rounded-full"><span class="w-3 h-3 rounded-sm bg-[#c0623a]"></span>Cửa</div>
      <div class="flex items-center gap-1.5 backdrop-blur-sm bg-black/20 px-2.5 py-1 rounded-full"><span class="w-3 h-3 rounded-sm bg-[#5bb8d4] opacity-80"></span>Lối thông</div>
      <div class="flex items-center gap-1.5 backdrop-blur-sm bg-black/20 px-2.5 py-1 rounded-full"><span class="w-3 h-3 rounded-sm bg-[#ffe066]"></span>Đèn</div>
      <div class="flex items-center gap-1.5 backdrop-blur-sm bg-black/20 px-2.5 py-1 rounded-full"><span class="w-3 h-3 rounded-sm bg-[#55cc77]"></span>Cảm biến</div>
      <div class="flex items-center gap-1.5 backdrop-blur-sm bg-black/20 px-2.5 py-1 rounded-full"><span class="w-3 h-3 rounded-sm bg-[#4a6fa5]"></span>Điện tử</div>
    </div>
    
    <!-- Error Overlay -->
    <div v-if="errorMsg" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/95 text-red-500 p-6 z-50 font-mono text-xs gap-3">
      <span class="font-bold text-sm">⚠️ LỖI KHỞI TẠO 3D:</span>
      <pre class="bg-black/60 p-4 rounded border border-red-500/20 max-w-full overflow-auto whitespace-pre-wrap">{{ errorMsg }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { WALL_IMAGE_DATA } from '../assets/wall_texture.js'

const props = defineProps({
  deviceStates: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['toggle'])

const container = ref(null)
const canvasEl = ref(null)
const tooltipEl = ref(null)
const viewMode = ref('persp')
const errorMsg = ref(null)

let scene, camera, renderer, animationFrameId
let rotatingFans = []
let doors = []
let lightObjects = {}

const HX = 30, HY = 2, HZ = 20
let view = 'persp'
let cs = { phi: Math.PI / 2.7, theta: -Math.PI * 0.25, r: 80 }
let drag = false
let lx = 0, ly = 0
let lt = null

const ray = new THREE.Raycaster()
const ms = new THREE.Vector2()

function updateCam() {
  if (!camera) return
  camera.up.set(0, 1, 0)
  if (view === 'top') {
    camera.position.set(HX, 115, HZ)
    camera.up.set(0, 0, -1)
    camera.lookAt(HX, 0, HZ)
  } else if (view === 'front') {
    camera.position.set(HX, 18, -68)
    camera.lookAt(HX, 3, HZ)
  } else {
    const { phi, theta, r } = cs
    camera.position.set(
      HX + r * Math.sin(phi) * Math.sin(theta), 
      HY + r * Math.cos(phi), 
      HZ + r * Math.sin(phi) * Math.cos(theta)
    )
    camera.lookAt(HX, HY, HZ)
  }
}

// Geometry Box helper
function B(w, h, d, col, x, y, z, name, info) {
  const mat = col instanceof THREE.Material ? col : new THREE.MeshLambertMaterial({ color: col })
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat)
  m.position.set(x, y, z)
  m.castShadow = true
  m.receiveShadow = true
  if (name) {
    m.userData.name = name
    m.userData.info = info || ''
  }
  scene.add(m)
  return m
}

// Wall Fan Group Creator
function wallFan(x, y, z, side, name, info) {
  const fanM = new THREE.MeshLambertMaterial({ color: 0x8f969a })
  const cageM = new THREE.MeshLambertMaterial({ color: 0xb9c0c3, transparent: true, opacity: .42 })
  const hubM = new THREE.MeshLambertMaterial({ color: 0x4b5560 })
  const rot = side === 'west' ? Math.PI / 2 : -Math.PI / 2
  const base = B(.22, 1.6, 1.6, fanM, x, y, z, name, info)
  
  const cage = new THREE.Mesh(new THREE.CylinderGeometry(.82, .82, .16, 32), cageM)
  cage.position.set(x + (side === 'west' ? .16 : -.16), y, z)
  cage.rotation.z = rot
  cage.castShadow = true
  cage.receiveShadow = true
  cage.userData = base.userData
  scene.add(cage)
  
  const rotorGroup = new THREE.Group()
  const rx = x + (side === 'west' ? .28 : -.28)
  rotorGroup.position.set(rx, y, z)
  
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, .22, 24), hubM)
  hub.rotation.z = rot
  hub.castShadow = true
  hub.receiveShadow = true
  hub.userData = base.userData
  rotorGroup.add(hub)
  
  for (let i = 0; i < 3; i++) {
    const bladeM = new THREE.MeshLambertMaterial({ color: 0xd8dde0 })
    const blade = new THREE.Mesh(new THREE.BoxGeometry(.08, .18, .68), bladeM)
    blade.castShadow = true
    blade.receiveShadow = true
    blade.userData = base.userData
    blade.rotation.x = i * Math.PI * 2 / 3
    blade.position.set(
      side === 'west' ? .04 : -.04, 
      Math.sin(blade.rotation.x) * .25, 
      Math.cos(blade.rotation.x) * .25
    )
    rotorGroup.add(blade)
  }
  scene.add(rotorGroup)
  rotatingFans.push({ name: name, group: rotorGroup, axis: 'x', speed: side === 'west' ? 0.15 : -0.15, state: false })
}

// Ceiling Fan Group Creator
function ceilingFan(x, y, z, name, info) {
  const base = B(.18, .65, .18, 0x777777, x, y + .34, z, name, info)
  const rotorGroup = new THREE.Group()
  rotorGroup.position.set(x, y, z)
  
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(.34, .34, .18, 28), new THREE.MeshLambertMaterial({ color: 0x555b60 }))
  hub.castShadow = true
  hub.receiveShadow = true
  hub.userData = base.userData
  rotorGroup.add(hub)
  
  for (let i = 0; i < 4; i++) {
    const bladeM = new THREE.MeshLambertMaterial({ color: 0xbfc5c8 })
    const blade = new THREE.Mesh(new THREE.BoxGeometry(3.4, .08, .42), bladeM)
    blade.castShadow = true
    blade.receiveShadow = true
    blade.userData = base.userData
    blade.rotation.y = i * Math.PI / 2
    rotorGroup.add(blade)
  }
  scene.add(rotorGroup)
  rotatingFans.push({ name: name, group: rotorGroup, axis: 'y', speed: 0.12, state: false })
}

// Wall Picture North
function wallPictureNorth(x, y, z, w, name, info) {
  const tex = new THREE.TextureLoader().load(WALL_IMAGE_DATA)
  tex.encoding = THREE.sRGBEncoding
  const h = w * (168 / 180)
  const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide })
  const pic = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat)
  pic.position.set(x, y, z)
  pic.rotation.y = Math.PI
  pic.userData.name = name
  pic.userData.info = info
  scene.add(pic)
  
  B(w + .22, .08, .08, 0x5b4635, x, y + h / 2 + .06, z - .02)
  B(w + .22, .08, .08, 0x5b4635, x, y - h / 2 - .06, z - .02)
  B(.08, h + .22, .08, 0x5b4635, x - w / 2 - .06, y, z - .02)
  B(.08, h + .22, .08, 0x5b4635, x + w / 2 + .06, y, z - .02)
}

// Hinge swinging door creator
const dM = new THREE.MeshLambertMaterial({ color: 0xc0623a })
function createDoor(w, h, d, x, y, z, hingeX, hingeZ, name, info, openSwingAngle) {
  const pivot = new THREE.Group()
  pivot.position.set(hingeX, y, hingeZ)
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), dM)
  mesh.position.set(x - hingeX, 0, z - hingeZ)
  mesh.castShadow = true
  mesh.receiveShadow = true
  mesh.userData.name = name
  mesh.userData.info = info || ''
  pivot.add(mesh)
  pivot.userData.name = name
  scene.add(pivot)
  doors.push({ name: name, group: pivot, closedAngle: 0, openAngle: openSwingAngle || Math.PI / 2, state: false })
  return pivot;
}

// PointLight helper
function createPointLight(x, y, z, name) {
  const light = new THREE.PointLight(0xffe066, 0, 18, 1.2)
  light.position.set(x, y - 0.4, z)
  light.castShadow = true
  light.shadow.bias = -0.002
  light.shadow.mapSize.set(512, 512)
  scene.add(light)
  lightObjects[name] = light
}

function getDeviceByName(name) {
  let target = null;
  scene.traverse(obj => {
    if (obj.userData && obj.userData.name === name && obj instanceof THREE.Mesh && !obj.parent.userData.name) {
      target = obj;
    }
  });
  return target;
}

const WH = 6;
const WT = 0.4;
const FH = WH / 2 + 0.15;
const WC = 0xf0ebe0;

function lbl(text, x, y, z, sc) {
  const cv = document.createElement('canvas'); cv.width = 340; cv.height = 64;
  const c2 = cv.getContext('2d');
  c2.font = 'bold 22px sans-serif'; c2.fillStyle = '#a0aec0'; c2.textAlign = 'center';
  c2.fillText(text, 170, 42);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), transparent: true }));
  sp.position.set(x, y, z); sp.scale.set(sc || 10, 2, 1); scene.add(sp);
}

// Main initialisation
function initThree() {
  rotatingFans.length = 0
  doors.length = 0
  for (let key in lightObjects) delete lightObjects[key]

  const rect = container.value.getBoundingClientRect()
  let width = rect.width
  let height = rect.height

  if (!width || !height || isNaN(width) || isNaN(height) || width === 0 || height === 0) {
    width = container.value.clientWidth || 800
    height = container.value.clientHeight || 550
  }

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xe2e8f0)
  scene.fog = new THREE.Fog(0xe2e8f0, 120, 220)

  camera = new THREE.PerspectiveCamera(44, width / height, 0.1, 300)
  updateCam()

  renderer = new THREE.WebGLRenderer({ canvas: canvasEl.value, antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio || 1)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap

  // Ambient & directional lights adjusted for bright day settings
  scene.add(new THREE.AmbientLight(0xfff8f0, 0.7))
  const sun = new THREE.DirectionalLight(0xfff4e0, 0.95)
  sun.position.set(60, 90, 40)
  sun.castShadow = true
  sun.shadow.mapSize.set(1024, 1024)
  sun.shadow.camera.left = sun.shadow.camera.bottom = -100
  sun.shadow.camera.right = sun.shadow.camera.top = 100
  sun.shadow.bias = -0.001
  scene.add(sun)
  
  const fill = new THREE.DirectionalLight(0xc8e0ff, 0.35)
  fill.position.set(-50, 30, -30)
  scene.add(fill)

  // ── BUILD ENVIRONMENT ──
  // Floor
  B(60, 0.28, 40, 0xd5ccb0, 30, -0.14, 20)
  B(19.6, .1, 9.6, 0xd5d0bc, 10, .06, 35)   // Hành Lang
  B(19.6, .1, 17.6, 0xcfc8a8, 10, .06, 21)   // Phòng Ngủ
  B(19.6, .1, 11.6, 0xbecec6, 10, .06, 6)    // Nhà VS
  B(24.6, .1, 39.6, 0xc8c2a0, 32.5, .06, 20)  // Phòng Khách
  B(14.6, .1, 11.6, 0xb2c0aa, 52.5, .06, 34)  // Khu KT
  B(14.6, .1, 27.6, 0xbcaa8c, 52.5, .06, 14)  // Nhà Bếp

  // Outer Walls
  B(60, WH, WT, WC, 30, FH, -0.2)
  B(60, WH, WT, WC, 30, FH, 40.2)
  B(WT, WH, 40, WC, -0.2, FH, 20)
  B(WT, WH, 40, WC, 60.2, FH, 20)

  // Inner Walls
  B(WT, WH, 3, WC, 20, FH, 1.5)
  B(WT, WH, 5, WC, 20, FH, 9.5)
  B(WT, WH, 6, WC, 20, FH, 15)
  B(WT, WH, 8, WC, 20, FH, 26)
  B(WT, WH, 3, WC, 20, FH, 31.5)
  B(WT, WH, 1, WC, 20, FH, 39.5)
  B(20, WH, WT, WC, 10, FH, 30)
  B(20, WH, WT, WC, 10, FH, 12)
  B(WT, WH, 9, WC, 45, FH, 4.5)
  B(WT, WH, 14, WC, 45, FH, 21)
  B(WT, WH, 5, WC, 45, FH, 30.5)
  B(WT, WH, 1, WC, 45, FH, 39.5)
  B(15, WH, WT, WC, 52.5, FH, 28)

  // Doors swing arcs
  const swM = new THREE.MeshLambertMaterial({ color: 0xd08050, transparent: true, opacity: .15 })
  B(4, .06, 4, swM, 22, .06, 5)
  B(4, .06, 4, swM, 22, .06, 20)
  B(5, .06, 5, swM, 43, .06, 11.5)
  B(6, .06, 6, swM, 43, .06, 36)

  // Openings
  const oM = new THREE.MeshLambertMaterial({ color: 0x5bb8d4, transparent: true, opacity: .52 })
  B(WT * 1.5, WH * .85, 6, oM, 20, WH * .425, 36, 'Lối Thông: Hành Lang ↔ Khách', 'Lối đi thông không cửa')

  // Doors
  createDoor(7, WH * .85, WT * 2, 8.5, WH * .425, 40.1, 5, 40.1, 'Cửa Chính', 'Cửa ra vào từ ngoài → Hành Lang', -Math.PI / 1.8)
  createDoor(WT * 2, WH * .85, 4, 20.3, WH * .425, 5, 20.3, 3, 'Cửa Nhà Vệ Sinh', 'Cửa phòng vệ sinh', Math.PI / 2)
  createDoor(WT * 2, WH * .85, 4, 20.3, WH * .425, 20, 20.3, 18, 'Cửa Phòng Ngủ', 'Cửa phòng ngủ → Phòng Khách', Math.PI / 2)
  createDoor(WT * 2, WH * .85, 5, 45.3, WH * .425, 11.5, 45.3, 9, 'Cửa Nhà Bếp', 'Cửa nhà bếp → Phòng Khách', -Math.PI / 2)
  createDoor(WT * 2, WH * .85, 6, 45.3, WH * .425, 36, 45.3, 33, 'Cửa Khu KT', 'Cửa đi vào khu kỹ thuật', -Math.PI / 2)

  // Devices & Ceiling PointLights
  // Hành Lang
  B(1.2, .16, 1.2, 0xffe066, 10, WH + .1, 35, 'Đèn Hành Lang', 'LED trần · Hành Lang')
  createPointLight(10, WH + .1, 35, 'Đèn Hành Lang')
  B(.5, .9, .22, 0xddaa33, 1, 1.8, 39, 'Servo Khóa Cửa', 'Servo motor khóa cửa')
  B(.55, .45, .45, new THREE.MeshLambertMaterial({ color: 0x1a1a33, emissive: 0x0a0a99, emissiveIntensity: .6 }), 8.5, 4.8, 40.65, 'Camera AI', 'Camera ngoài cửa chính · Nhận diện')

  // Phòng Ngủ
  B(1.2, .16, 1.2, 0xffe066, 10, WH + .1, 21, 'Đèn Phòng Ngủ', 'LED trần · Phòng Ngủ')
  createPointLight(10, WH + .1, 21, 'Đèn Phòng Ngủ')
  wallFan(19.7, 3.6, 25, 'east', 'Quạt Phòng Ngủ', 'Quạt treo tường · Phòng Ngủ')
  B(7, .65, 9, 0x8899bb, 5, .48, 20)
  B(7, 1, .9, 0xaabbdd, 5, .85, 25.5)

  // Nhà VS
  B(1.2, .16, 1.2, 0xffe066, 10, WH + .1, 6, 'Đèn Nhà Vệ Sinh', 'LED trần · Vệ Sinh')
  createPointLight(10, WH + .1, 6, 'Đèn Nhà Vệ Sinh')

  // Phòng Khách
  B(4, .2, 4, 0xffe066, 32.5, WH + .1, 20, 'Đèn Chùm Trung Tâm', 'Đèn chùm LED · Phòng Khách')
  createPointLight(32.5, WH + .1, 20, 'Đèn Chùm Trung Tâm')
  ceilingFan(32.5, WH - .2, 12, 'Quạt Trần Phòng Khách', 'Quạt trần DC · Phòng Khách')
  B(5, 3, .2, new THREE.MeshLambertMaterial({ color: 0x1a2d5a, emissive: 0x0f2299, emissiveIntensity: .5 }), 32.5, 2.5, .4, 'Màn Hình OLED', 'Dashboard thông minh')
  B(.55, .55, .55, 0x55cc77, 32, WH - .3, 18, 'Cảm Biến PIR', 'Phát hiện chuyển động')
  B(.55, .55, .3, 0x55cc77, 30, 2, 13, 'DHT11 Phòng Khách', 'Nhiệt độ · Phòng Khách')
  B(1.1, 1.6, .5, new THREE.MeshLambertMaterial({ color: 0x334455, emissive: 0x112244, emissiveIntensity: .4 }), 21.5, 1.3, 26, 'Loa + Mic', 'Kết nối Laptop · Phòng Khách')
  B(14, .65, 4, 0x7a6655, 32.5, .5, 37)
  B(14, 1.2, .4, 0x7a6655, 32.5, .9, 39.4)
  wallPictureNorth(32.5, 3.5, 39.92, 4.3, 'Ảnh Treo Tường', 'Ảnh PNG nhúng base64 · Phòng Khách')

  // Nhà Bếp
  B(1.2, .16, 1.2, 0xffe066, 52.5, WH + .1, 14, 'Đèn Nhà Bếp', 'LED trần · Bếp')
  createPointLight(52.5, WH + .1, 14, 'Đèn Nhà Bếp')
  B(.65, .65, .42, 0x55cc77, 59.3, 1.8, 26, 'Cảm Biến MQ2 Gas', 'Phát hiện khí gas · Bếp')
  wallFan(45.3, 3.6, 22, 'west', 'Quạt Nhà Bếp', 'Quạt treo tường · Nhà Bếp')
  B(12, 1, 2.5, 0x9a8870, 52.5, .65, 27)

  // Khu KT
  B(1.2, .16, 1.2, 0xffe066, 52.5, WH + .1, 34, 'Đèn Khu KT', 'LED trần · Khu Kỹ Thuật')
  createPointLight(52.5, WH + .1, 34, 'Đèn Khu KT')
  B(1.4, .32, .85, 0x4a6fa5, 47.5, .45, 30, 'ESP32 DevKit V1', 'Vi điều khiển chính')
  B(2.8, .85, 1, new THREE.MeshLambertMaterial({ color: 0xdd4444, emissive: 0xcc1111, emissiveIntensity: .35 }), 52.5, .68, 30, 'Module Relay 8 Kênh', 'Điều khiển 8 thiết bị')

  // Labels
  lbl('Hành Lang', 10, WH + 1.6, 35)
  lbl('Phòng Ngủ', 10, WH + 1.6, 21)
  lbl('Nhà Vệ Sinh', 10, WH + 1.6, 6, 11)
  lbl('Phòng Khách', 32.5, WH + 1.6, 20)
  lbl('Nhà Bếp', 52.5, WH + 1.6, 14)
  lbl('Khu KT', 52.5, WH + 1.6, 34)

  // EVENT LISTENERS
  canvasEl.value.addEventListener('mousedown', onMouseDown)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('mousemove', onMouseMove)
  canvasEl.value.addEventListener('wheel', onWheel, { passive: false })
  canvasEl.value.addEventListener('touchstart', onTouchStart)
  canvasEl.value.addEventListener('touchmove', onTouchMove, { passive: false })
  canvasEl.value.addEventListener('click', onCanvasClick)

  window.addEventListener('resize', onWindowResize)
}

function syncDeviceStates(states) {
  if (!states) return
  Object.keys(states).forEach(name => {
    const isON = states[name]
    
    // Lights
    if (name.startsWith('Đèn')) {
      const pointLight = lightObjects[name]
      const lampMesh = getDeviceByName(name)
      if (lampMesh) {
        if (isON) {
          lampMesh.material.color.setHex(0xffffff)
          if (lampMesh.material.emissive) {
            lampMesh.material.emissive.setHex(0xffe066)
            lampMesh.material.emissiveIntensity = 1.0
          }
        } else {
          lampMesh.material.color.setHex(0x555555)
          if (lampMesh.material.emissive) {
            lampMesh.material.emissive.setHex(0x000000)
            lampMesh.material.emissiveIntensity = 0
          }
        }
      }
      if (pointLight) {
        pointLight.intensity = isON ? 1.6 : 0
      }
    }
    // Fans
    else if (name.startsWith('Quạt')) {
      const fan = rotatingFans.find(f => f.name === name)
      if (fan) fan.state = isON
    }
    // Doors
    else if (name.startsWith('Cửa')) {
      const door = doors.find(d => d.name === name)
      if (door) door.state = isON
    }
  })
}

// CAMERA / MOUSE HANDLERS
function onMouseDown(e) {
  drag = true
  lx = e.clientX
  ly = e.clientY
  tooltipEl.value.style.display = 'none'
}
function onMouseUp() {
  drag = false
}
function onMouseMove(e) {
  if (drag) {
    cs.theta -= (e.clientX - lx) * 0.007
    cs.phi = Math.max(0.08, Math.min(Math.PI / 2 - 0.05, cs.phi + (e.clientY - ly) * 0.006))
    lx = e.clientX
    ly = e.clientY
    updateCam()
  } else {
    // Show tooltips
    const r = canvasEl.value.getBoundingClientRect()
    ms.x = ((e.clientX - r.left) / r.width) * 2 - 1
    ms.y = -((e.clientY - r.top) / r.height) * 2 + 1
    ray.setFromCamera(ms, camera)
    const hit = ray.intersectObjects(scene.children, true).find(h => h.object.userData.name)
    if (hit) {
      tooltipEl.value.style.display = 'block'
      tooltipEl.value.style.left = (e.clientX - r.left + 12) + 'px'
      tooltipEl.value.style.top = (e.clientY - r.top - 8) + 'px'
      tooltipEl.value.style.innerHTML = `<strong>${hit.object.userData.name}</strong><br>${hit.object.userData.info}`
      tooltipEl.value.innerHTML = `<strong>${hit.object.userData.name}</strong><br>${hit.object.userData.info}`
    } else {
      tooltipEl.value.style.display = 'none'
    }
  }
}
function onWheel(e) {
  e.preventDefault()
  cs.r = Math.max(18, Math.min(160, cs.r + e.deltaY * 0.06))
  updateCam()
}
function onTouchStart(e) {
  lt = e.touches[0]
}
function onTouchMove(e) {
  e.preventDefault()
  if (!lt) return
  cs.theta -= (e.touches[0].clientX - lt.clientX) * 0.007
  cs.phi = Math.max(0.08, Math.min(Math.PI / 2 - 0.05, cs.phi + (e.touches[0].clientY - lt.clientY) * 0.006))
  lt = e.touches[0]
  updateCam()
}
function onCanvasClick(e) {
  if (drag) return
  const r = canvasEl.value.getBoundingClientRect()
  ms.x = ((e.clientX - r.left) / r.width) * 2 - 1
  ms.y = -((e.clientY - r.top) / r.height) * 2 + 1
  ray.setFromCamera(ms, camera)
  const hit = ray.intersectObjects(scene.children, true).find(h => h.object.userData.name)
  if (hit) {
    const name = hit.object.userData.name
    if (props.deviceStates[name] !== undefined) {
      emit('toggle', name)
    }
  }
}
function onWindowResize() {
  if (!container.value || !renderer || !camera) return
  const rect = container.value.getBoundingClientRect()
  camera.aspect = rect.width / rect.height
  camera.updateProjectionMatrix()
  renderer.setSize(rect.width, rect.height)
  updateCam()
}

// Watch deviceStates to trigger light changes / animations
watch(() => props.deviceStates, (newStates) => {
  if (scene) {
    syncDeviceStates(newStates)
  }
}, { deep: true })

function changeView(v) {
  viewMode.value = v
  view = v
  camera.fov = v === 'top' ? 52 : 44
  camera.updateProjectionMatrix()
  updateCam()
}
function resetCam() {
  cs = { phi: Math.PI / 2.7, theta: -Math.PI * 0.25, r: 80 }
  changeView('persp')
}

// Animation loop
function animate() {
  animationFrameId = requestAnimationFrame(animate)

  // Rotate fans
  rotatingFans.forEach(fan => {
    if (fan.state) {
      fan.group.rotation[fan.axis] += fan.speed
    }
  })

  // Swing doors
  doors.forEach(door => {
    const targetAngle = door.state ? door.openAngle : door.closedAngle
    door.group.rotation.y += (targetAngle - door.group.rotation.y) * 0.08
  })

  renderer.render(scene, camera)
}

onMounted(() => {
  try {
    initThree()
    syncDeviceStates(props.deviceStates)
    animate()
  } catch (err) {
    console.error("Three.js Init Error:", err)
    errorMsg.value = err.stack || err.message || err.toString()
  }
})

onUnmounted(() => {
  cancelAnimationFrame(animationFrameId)
  
  // Remove event listeners
  if (canvasEl.value) {
    canvasEl.value.removeEventListener('mousedown', onMouseDown)
    canvasEl.value.removeEventListener('wheel', onWheel)
    canvasEl.value.removeEventListener('touchstart', onTouchStart)
    canvasEl.value.removeEventListener('touchmove', onTouchMove)
    canvasEl.value.removeEventListener('click', onCanvasClick)
  }
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('resize', onWindowResize)

  // Resource cleanup
  scene.traverse(object => {
    if (object.geometry) object.geometry.dispose()
    if (object.material) {
      if (Array.isArray(object.material)) {
        object.material.forEach(material => material.dispose())
      } else {
        object.material.dispose()
      }
    }
  })
  renderer.dispose()
})
</script>
