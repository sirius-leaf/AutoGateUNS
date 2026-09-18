<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Copy, Check, ChevronsLeft, Square, Camera, Loader2, AlertTriangle,
  X, ShieldCheck, ShieldX, Settings, Save, Eye, EyeOff, RefreshCw, ToggleRight,
  DoorOpen, ScanLine, Nfc, Car
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
  nodeStatus: {
    type: Object,
    default: null,
  },
  // OPSIONAL: jumlah kendaraan hari ini untuk gate ini.
  // Kalau belum ada API-nya, biarkan tidak diisi -> tampil "--"
  dailyCount: {
    type: [Number, String],
    default: null,
  }
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

// --- BARU: mode validasi (dibaca dari settings node) ---
const validationMode = ref('')

const validationLabel = computed(() => {
  const map = {
    plate_only: 'Plat',
    rfid_only: 'Kartu',
    both: 'Plat + Kartu',
  }
  return map[validationMode.value] || '--'
})

// --- BARU: hasil deteksi terakhir (plat & kartu) ---
const lastPlate = ref('')
const lastCard = ref('')

// --- BARU: hitung lama offline kamera ---
const offlineSince = ref(null)
const nowTick = ref(Date.now())
let clockTimer = null

const offlineMinutes = computed(() => {
  if (!offlineSince.value) return 0
  return Math.max(0, Math.floor((nowTick.value - offlineSince.value) / 60000))
})

const streamUrl = computed(() => {
  return `${api.baseUrl}/api/stream/${props.direction}?t=${cacheBuster.value}`
})

const cameraActive = computed(() => {
  if (streamError.value) return false;
  if (props.nodeStatus) {
    const activeInDb = props.direction === 'masuk' ? props.nodeStatus.camera_in_active : props.nodeStatus.camera_out_active;
    if (activeInDb) return true;
  }
  return !streamError.value;
})

// --- BARU: status gerbang (relay), terpisah dari status kamera ---
const gateOnline = computed(() => {
  if (relayError.value) return false
  if (props.nodeStatus && typeof props.nodeStatus.relay_connected === 'boolean') {
    return props.nodeStatus.relay_connected
  }
  return true
})

// --- BARU: status aktivitas (badge kedua di header) ---
const activityStatus = computed(() => {
  if (capturing.value) return { label: 'Memproses', tone: 'var(--status-pending)' }
  if (lastPlate.value || lastCard.value) return { label: 'Terdeteksi', tone: 'var(--status-ok)' }
  return { label: 'Menunggu', tone: 'var(--status-pending)' }
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
    // BARU: ambil mode validasi dari blok node (tanpa request tambahan)
    if (data.node) {
      validationMode.value = data.node.VALIDATION_MODE || ''
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

const handleToggleRelay = async () => {
  relayLoading.value = true
  relayError.value = ''
  try {
    await api.toggleRelay(props.direction)
  } catch (err) {
    relayError.value = 'Gagal toggle relay: ' + err.message
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
       // BARU: isi field Plat Nomor & Kartu dari hasil capture
       lastPlate.value = res.plate_number || ''
       lastCard.value = res.rfid_uid && res.rfid_uid !== '-' ? res.rfid_uid : ''
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
  if (!offlineSince.value) offlineSince.value = Date.now()
  if (!streamSlowMode.value) {
    streamSlowMode.value = true
    startStreamTimer(5000)
  }
}

const onStreamLoad = () => {
  streamError.value = false
  offlineSince.value = null
  if (streamSlowMode.value) {
    streamSlowMode.value = false
    startStreamTimer(currentInterval.value)
  }
}

const refreshingStream = ref(false)

const handleRefreshStream = () => {
  refreshingStream.value = true
  streamError.value = false
  cacheBuster.value = Date.now()
  setTimeout(() => {
    refreshingStream.value = false
  }, 600)
}

onMounted(async () => {
  startStreamTimer(currentInterval.value)
  clockTimer = setInterval(() => { nowTick.value = Date.now() }, 30000)
  await loadCameraInterval()
})
onUnmounted(() => {
  if (streamTimer) clearInterval(streamTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<template>
  <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-5 shadow-xl shadow-black/20 hover:border-[var(--accent)]/40 transition-all">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-3 flex-wrap">
        <!-- BARU: ikon gerbang sebelum judul -->
        <div class="w-8 h-8 shrink-0 rounded-lg bg-[var(--bg-panel-alt)] border border-[var(--border)] flex items-center justify-center">
          <DoorOpen class="w-4 h-4 text-[var(--accent)]" />
        </div>

        <h3 class="text-xl font-bold text-[var(--text-primary)] tracking-tight">{{ gate.title }}</h3>

        <!-- Camera Status Indicator -->
        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--bg-panel-alt)] border border-[var(--border)]"
             :title="cameraActive ? 'Kamera Terhubung' : 'Kamera Terputus'">
          <span class="w-2 h-2 rounded-full shrink-0"
                :style="{ backgroundColor: cameraActive ? 'var(--status-ok)' : 'var(--status-fail)' }"></span>
          <span class="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider">
            {{ cameraActive ? 'Online' : 'Offline' }}
          </span>
        </div>

        <!-- BARU: badge status aktivitas (Menunggu / Memproses / Terdeteksi) -->
        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--bg-panel-alt)] border border-[var(--border)]">
          <span class="w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: activityStatus.tone }"></span>
          <span class="text-[10px] font-bold uppercase tracking-wider" :style="{ color: activityStatus.tone }">
            {{ activityStatus.label }}
          </span>
        </div>
      </div>

      <!-- Quick Refresh Button -->
      <button
        @click="handleRefreshStream"
        class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition active:scale-95 shadow-sm"
        title="Refresh Kamera">
        <RefreshCw :class="['w-3.5 h-3.5', refreshingStream ? 'animate-spin' : '']" />
        <span class="hidden sm:inline">Refresh Kamera</span>
      </button>
    </div>

    <!-- BARU: baris sub-status gerbang + lama offline -->
    <div class="flex items-center gap-2 mb-3 text-[11px]">
      <span class="w-2 h-2 rounded-full shrink-0"
            :style="{ backgroundColor: gateOnline ? 'var(--status-ok)' : 'var(--status-fail)' }"></span>
      <span class="font-semibold" :style="{ color: gateOnline ? 'var(--status-ok)' : 'var(--status-fail)' }">
        {{ gateOnline ? 'Gerbang Beroperasi' : 'Tidak Terhubung' }}
      </span>
      <span v-if="!cameraActive && offlineSince" class="text-[var(--text-muted)]">
        · Offline selama {{ offlineMinutes }} menit
      </span>
    </div>

    <!-- BARU: baris Mode Validasi + counter kendaraan harian -->
    <div class="flex items-center justify-between gap-3 mb-4 px-3 py-2 rounded-lg bg-[var(--bg-panel-alt)] border border-[var(--border)]">
      <div class="flex items-center gap-1.5 min-w-0">
        <ScanLine class="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0" />
        <span class="text-[11px] text-[var(--text-muted)]">Mode Validasi:</span>
        <span class="text-[11px] font-semibold text-[var(--text-primary)] truncate">{{ validationLabel }}</span>
      </div>
      <div class="flex items-center gap-1.5 shrink-0">
        <Car class="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span class="text-[11px] font-mono font-semibold text-[var(--text-primary)]">
          {{ dailyCount ?? '--' }}
        </span>
        <span class="text-[11px] text-[var(--text-muted)]">kendaraan hari ini</span>
      </div>
    </div>

    <!-- Camera Preview (Full Width) -->
    <div class="mb-4">
      <div class="w-full relative rounded-lg overflow-hidden bg-[var(--bg-panel-alt)] border border-[var(--border)] shadow-inner group aspect-video sm:aspect-[16/9] flex items-center justify-center">
        <img
          v-if="!streamError"
          :src="streamUrl"
          alt="CCTV Feed"
          class="w-full h-full object-cover"
          @error="onStreamError"
          @load="onStreamLoad"
        />
        <div v-else class="w-full h-full bg-[var(--bg-panel-alt)] flex flex-col items-center justify-center p-6 text-center">
          <Camera class="w-12 h-12 text-[var(--text-muted)] opacity-50 mb-2" />
          <p class="text-xs font-medium text-[var(--text-muted)]">Kamera Tidak Terhubung</p>
          <p class="text-[10px] text-[var(--text-muted)] opacity-70 mt-1 mb-3">Mencoba lagi otomatis...</p>
          <button
            @click="handleRefreshStream"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-panel)] hover:bg-[var(--border)] text-[var(--text-primary)] text-xs font-medium border border-[var(--border)] shadow-md transition active:scale-95">
            <RefreshCw :class="['w-3.5 h-3.5', refreshingStream ? 'animate-spin' : '']" />
            <span>Coba Lagi / Refresh</span>
          </button>
        </div>

        <!-- BARU: label kecil "Tidak Terhubung" di pojok kiri atas kotak kamera -->
        <div v-if="!cameraActive"
             class="absolute top-3 left-3 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border z-20"
             :style="{ color: 'var(--status-fail)', borderColor: 'var(--status-fail)', backgroundColor: 'rgba(0,0,0,0.6)' }">
          Tidak Terhubung
        </div>

        <div :class="['absolute left-3 bg-black/85 backdrop-blur-md px-2.5 py-1 rounded text-[11px] font-mono text-zinc-200 border border-white/10 z-10', !cameraActive ? 'top-10' : 'top-3']">
          {{ gate.timestamp || '--' }}
        </div>

        <div v-if="!streamError" class="absolute top-3 right-3 z-10">
          <button
            @click="handleRefreshStream"
            class="bg-black/75 hover:bg-black/90 backdrop-blur-md p-1.5 rounded text-zinc-300 hover:text-white border border-white/10 shadow transition active:scale-95"
            title="Muat ulang stream kamera">
            <RefreshCw :class="['w-3.5 h-3.5', refreshingStream ? 'animate-spin' : '']" />
          </button>
        </div>
      </div>
    </div>

    <!-- BARU: field Plat Nomor & Kartu (read-only) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
      <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
        <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider mb-1">Plat Nomor</p>
        <div class="flex items-center gap-2">
          <ScanLine class="w-4 h-4 text-[var(--text-muted)] shrink-0" />
          <p class="text-sm font-bold font-mono text-[var(--text-primary)] truncate">
            {{ lastPlate || '--' }}
          </p>
        </div>
      </div>
      <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
        <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider mb-1">Kartu</p>
        <div class="flex items-center gap-2">
          <Nfc class="w-4 h-4 text-[var(--text-muted)] shrink-0" />
          <p class="text-sm font-bold font-mono text-[var(--text-primary)] truncate">
            {{ lastCard || '--' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="captureError || captureSuccess || relayError" class="mb-3 space-y-2">
      <div v-if="captureSuccess" class="flex items-start gap-2 rounded-lg px-3 py-2 border"
           :style="{ borderColor: 'var(--status-ok)', backgroundColor: 'color-mix(in srgb, var(--status-ok) 12%, transparent)' }">
        <ShieldCheck class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: 'var(--status-ok)' }" />
        <p class="text-xs flex-1" :style="{ color: 'var(--status-ok)' }">{{ captureSuccess }}</p>
        <button @click="captureSuccess = ''" class="p-0.5" :style="{ color: 'var(--status-ok)' }"><X class="w-3.5 h-3.5" /></button>
      </div>
      <div v-if="captureError" class="flex items-start gap-2 rounded-lg px-3 py-2 border"
           :style="{ borderColor: 'var(--status-fail)', backgroundColor: 'color-mix(in srgb, var(--status-fail) 12%, transparent)' }">
        <ShieldX v-if="direction === 'keluar'" class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: 'var(--status-fail)' }" />
        <AlertTriangle v-else class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: 'var(--status-fail)' }" />
        <p class="text-xs flex-1" :style="{ color: 'var(--status-fail)' }">{{ captureError }}</p>
        <button @click="captureError = ''" class="p-0.5" :style="{ color: 'var(--status-fail)' }"><X class="w-3.5 h-3.5" /></button>
      </div>
      <div v-if="relayError" class="flex items-start gap-2 rounded-lg px-3 py-2 border"
           :style="{ borderColor: 'var(--status-pending)', backgroundColor: 'color-mix(in srgb, var(--status-pending) 12%, transparent)' }">
        <AlertTriangle class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: 'var(--status-pending)' }" />
        <p class="text-xs flex-1" :style="{ color: 'var(--status-pending)' }">{{ relayError }}</p>
        <button @click="relayError = ''" class="p-0.5" :style="{ color: 'var(--status-pending)' }"><X class="w-3.5 h-3.5" /></button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-3 border-t border-[var(--border)]">
      <button @click="handleOpenGate" :disabled="relayLoading"
        class="flex items-center justify-center gap-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] border border-[var(--border)] font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50"
        :style="{ color: 'var(--status-ok)' }">
        <Loader2 v-if="relayLoading" class="w-4 h-4 animate-spin" />
        <ChevronsLeft v-else class="w-4 h-4" />
        <span>Buka Manual</span>
      </button>
      <button @click="handleToggleRelay" :disabled="relayLoading"
        class="flex items-center justify-center gap-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] border border-[var(--border)] font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50"
        :style="{ color: 'var(--status-ok)' }"
        :title="direction === 'masuk' ? 'Toggle Relay Ch 3' : 'Toggle Relay Ch 6'">
        <Loader2 v-if="relayLoading" class="w-4 h-4 animate-spin" />
        <ToggleRight v-else class="w-4 h-4" />
        <span>Selalu Buka</span>
      </button>
      <button @click="handleCloseGate" :disabled="relayLoading"
        class="flex items-center justify-center gap-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] border border-[var(--border)] font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50"
        :style="{ color: 'var(--status-fail)' }">
        <Square class="w-4 h-4" />
        <span>Tutup Manual</span>
      </button>
      <button @click="handleCapture" :disabled="capturing"
        class="flex items-center justify-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white border border-[var(--accent)] font-semibold py-2 px-3 rounded-md text-xs transition active:scale-[0.98] disabled:opacity-50">
        <Loader2 v-if="capturing" class="w-4 h-4 animate-spin" />
        <Camera v-else class="w-4 h-4" />
        <span>Capture</span>
      </button>
    </div>


  </div>
</template>