<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Copy, Check, ChevronsLeft, Square, Camera, Loader2, AlertTriangle,
  X, ShieldCheck, ShieldX, Settings, Save, Eye, EyeOff,
} from '@lucide/vue'
import api from '@/services/api'

const props = defineProps({
  gate: {
    type: Object,
    required: true,
  },
  direction: {
    type: String,
    required: true, // "masuk" atau "keluar"
  },
})

const emit = defineEmits(['capture', 'refresh', 'capture-response'])

const copied = ref(false)
const capturing = ref(false)
const relayLoading = ref(false)
const streamError = ref(false)
const streamSlowMode = ref(false)
const captureError = ref('')
const captureSuccess = ref('')
const relayError = ref('')
const cacheBuster = ref(0)
let streamTimer = null

// Settings modal removed - logic moved to SettingsView.vue

const currentInterval = ref(1000)
const currentOpenChannel = ref(1)
const currentCloseChannel = ref(2)

const streamUrl = computed(() => {
  return `${api.baseUrl}/api/stream/${props.direction}?t=${cacheBuster.value}`
})

const startStreamTimer = (interval) => {
  if (streamTimer) clearInterval(streamTimer)
  streamTimer = setInterval(() => {
    cacheBuster.value = Date.now()
  }, interval)
}

const loadCameraInterval = async () => {
  try {
    const data = await api.getSettings()
    const prefix = props.direction === 'masuk' ? 'CAMERA_IN' : 'CAMERA_OUT'
    const block = props.direction === 'masuk' ? data.camera_in : data.camera_out
    if (block) {
      currentInterval.value = parseFloat(block[`${prefix}_INTERVAL`] || 1000)
      currentOpenChannel.value = parseInt(block[`${prefix}_RELAY_OPEN`] || (props.direction === 'masuk' ? 1 : 4))
      currentCloseChannel.value = parseInt(block[`${prefix}_RELAY_CLOSE`] || (props.direction === 'masuk' ? 2 : 5))
    }
  } catch (err) {
    console.error('Failed to load camera settings', err)
  }
}

const handleOpenGate = async () => {
  relayLoading.value = true
  relayError.value = ''
  try {
    await api.controlRelay(currentOpenChannel.value, true)
    setTimeout(() => api.controlRelay(currentOpenChannel.value, false), 1000)
  } catch (err) {
    relayError.value = 'Gagal buka gate: ' + err.message
  } finally {
    relayLoading.value = false
  }
}

const handleCloseGate = async () => {
  relayLoading.value = true
  relayError.value = ''
  try {
    await api.controlRelay(currentCloseChannel.value, true)
    setTimeout(() => api.controlRelay(currentCloseChannel.value, false), 1000)
  } catch (err) {
    relayError.value = 'Gagal tutup gate: ' + err.message
  } finally {
    relayLoading.value = false
  }
}

const handleCapture = async () => {
  capturing.value = true
  captureError.value = ''
  captureSuccess.value = ''
  try {
    const res = await api.capturePlate(props.direction)
    emit('capture', res)
    if (res.ignored) {
       captureError.value = res.reason
    } else {
       captureSuccess.value = 'Capture sukses'
       emit('capture-response', res)
    }
  } catch (err) {
    captureError.value = err.message || 'Capture gagal'
  } finally {
    capturing.value = false
  }
}
const onStreamError = () => {
  streamError.value = true
  if (!streamSlowMode.value) {
    streamSlowMode.value = true
    startStreamTimer(5000)
  }
}

const onStreamLoad = () => {
  streamError.value = false
  if (streamSlowMode.value) {
    streamSlowMode.value = false
    startStreamTimer(currentInterval.value)
  }
}

onMounted(async () => {
  startStreamTimer(currentInterval.value)
  await loadCameraInterval()
})
onUnmounted(() => { if (streamTimer) clearInterval(streamTimer) })
</script>

<template>
  <div class="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-xl shadow-black/40 hover:border-zinc-700/80 transition-all">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xl font-bold text-white tracking-tight">{{ gate.title }}</h3>
    </div>

    <!-- Camera Preview (Full Width) -->
    <div class="mb-5">
      <div class="w-full relative rounded-lg overflow-hidden bg-zinc-950 border border-zinc-800 shadow-inner group aspect-video sm:aspect-[16/9] flex items-center justify-center">
        <img
          v-if="!streamError"
          :src="streamUrl"
          alt="CCTV Feed"
          class="w-full h-full object-cover"
          @error="onStreamError"
          @load="onStreamLoad"
        />
        <div v-else class="w-full h-full bg-gradient-to-br from-zinc-900 via-zinc-950 to-black flex flex-col items-center justify-center p-6 text-center">
          <Camera class="w-12 h-12 text-zinc-700 mb-2" />
          <p class="text-xs font-medium text-zinc-500">Kamera Tidak Terhubung</p>
          <p class="text-[10px] text-zinc-600 mt-2">Mencoba lagi otomatis...</p>
        </div>

        <div class="absolute top-3 left-3 bg-black/85 backdrop-blur-md px-2.5 py-1 rounded text-[11px] font-mono text-zinc-200 border border-white/10 z-10">
          {{ gate.timestamp || '--' }}
        </div>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="captureError || captureSuccess || relayError" class="mb-3 space-y-2">
      <div v-if="captureSuccess" class="flex items-start gap-2 bg-emerald-950/80 border border-emerald-800/60 rounded-lg px-3 py-2">
        <ShieldCheck class="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
        <p class="text-xs text-emerald-300 flex-1">{{ captureSuccess }}</p>
        <button @click="captureSuccess = ''" class="p-0.5 text-emerald-400 hover:text-emerald-300"><X class="w-3.5 h-3.5" /></button>
      </div>
      <div v-if="captureError" class="flex items-start gap-2 bg-red-950/80 border border-red-800/60 rounded-lg px-3 py-2">
        <ShieldX v-if="direction === 'keluar'" class="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
        <AlertTriangle v-else class="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
        <p class="text-xs text-red-300 flex-1">{{ captureError }}</p>
        <button @click="captureError = ''" class="p-0.5 text-red-400 hover:text-red-300"><X class="w-3.5 h-3.5" /></button>
      </div>
      <div v-if="relayError" class="flex items-start gap-2 bg-amber-950/80 border border-amber-800/60 rounded-lg px-3 py-2">
        <AlertTriangle class="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p class="text-xs text-amber-300 flex-1">{{ relayError }}</p>
        <button @click="relayError = ''" class="p-0.5 text-amber-400 hover:text-amber-300"><X class="w-3.5 h-3.5" /></button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-3 border-t border-zinc-800">
      <button @click="handleOpenGate" :disabled="relayLoading"
        class="flex items-center justify-center gap-2 bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/70 font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50">
        <Loader2 v-if="relayLoading" class="w-4 h-4 animate-spin" />
        <ChevronsLeft v-else class="w-4 h-4 text-emerald-400" />
        <span>Buka Manual</span>
      </button>
      <button @click="handleCloseGate" :disabled="relayLoading"
        class="flex items-center justify-center gap-2 bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800/70 font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50">
        <Square class="w-4 h-4 text-rose-400" />
        <span>Tutup Manual</span>
      </button>
      <button @click="handleCapture" :disabled="capturing"
        class="flex items-center justify-center gap-2 bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-800/70 font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50">
        <Loader2 v-if="capturing" class="w-4 h-4 animate-spin" />
        <Camera v-else class="w-4 h-4 text-blue-400" />
        <span>Capture</span>
      </button>
    </div>

  </div>
</template>
