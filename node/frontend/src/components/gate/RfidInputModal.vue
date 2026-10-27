<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Nfc, Loader2, AlertTriangle, CheckCircle2, ArrowRight, Car, Camera, X } from '@lucide/vue'
import api from '@/services/api'

const props = defineProps({
  detection: { type: Object, default: null }, // Deteksi radar baru (sebelum kamera capture)
  vehicle: { type: Object, default: null },   // Data kendaraan (jika capture manual/fallback)
  direction: { type: String, required: true }, // "masuk" atau "keluar"
})

const emit = defineEmits(['close', 'done'])

const rfidInput = ref('')
const rfidRef = ref(null)
const submitting = ref(false)
const submitError = ref('')
const rfidMatchResult = ref(null) // true, false, null
const submitted = ref(false)
const capturedVehicle = ref(props.vehicle || null)

const isMasuk = computed(() => (props.direction || props.detection?.direction) === 'masuk')
const dirLabel = computed(() => isMasuk.value ? 'Masuk' : 'Keluar')
const title = computed(() => `RFID untuk ${dirLabel.value}`)

const handleSubmit = async () => {
  if (submitting.value) return
  submitting.value = true
  submitError.value = ''

  try {
    const rawRfid = rfidInput.value.trim()
    const rfidUid = rawRfid || null

    if (props.detection) {
      // ── Alur Baru: Radar deteksi objek → input RFID → capture kamera ──
      const result = await api.submitDetectionRfid(props.detection.detection_id, rfidUid)

      if (result.status === 'failed') {
        submitError.value = result.message || 'Gagal memproses deteksi kamera.'
        return
      }

      if (result.vehicle) {
        capturedVehicle.value = result.vehicle
      }

      submitted.value = true

      // Auto-close setelah 2.5 detik
      setTimeout(() => {
        emit('done', { detection: result, vehicle: result.vehicle })
        emit('close')
      }, 2500)

    } else if (props.vehicle) {
      // ── Alur Fallback/Manual: Kamera sudah capture → input RFID ──
      const result = await api.submitRfid(props.vehicle.event_id, rfidUid)

      if (!result.success) {
        submitError.value = result.message || 'Gagal menyimpan RFID'
        return
      }

      rfidMatchResult.value = result.rfid_match
      submitted.value = true

      const delay = result.rfid_match === false ? 4000 : 2000
      setTimeout(() => {
        emit('done', { rfid_match: result.rfid_match, vehicle: props.vehicle })
        emit('close')
      }, delay)
    }
  } catch (err) {
    submitError.value = err.message || 'Gagal mengirim perintah ke server'
  } finally {
    submitting.value = false
  }
}

const handleLanjutkan = () => {
  rfidInput.value = '-'
  handleSubmit()
}

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
  }
}

const validationMode = ref('both')

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown, true)

  try {
    const data = await api.getSettings()
    if (data && data.node && data.node.VALIDATION_MODE) {
      validationMode.value = data.node.VALIDATION_MODE
    }
  } catch (err) {
    console.error('Failed to get validation mode', err)
  }

  await nextTick()
  rfidRef.value?.focus()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown, true)
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
    <div class="bg-zinc-900 border border-zinc-700 rounded-2xl shadow-2xl shadow-black/80 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div class="flex items-center gap-3">
          <div
            :class="[
              'p-2.5 rounded-xl',
              isMasuk ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
            ]"
          >
            <Nfc class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-bold text-white tracking-tight">{{ title }}</h3>
            <p class="text-xs text-zinc-400">
              <span v-if="props.detection">Radar mendeteksi objek — silakan tap kartu RFID</span>
              <span v-else>Tap kartu RFID untuk membuka gerbang</span>
            </p>
          </div>
        </div>

        <button
          v-if="!submitting && !submitted"
          @click="emit('close')"
          class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
          title="Tutup Modal"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <!-- Display Info Kendaraan jika sudah ada / sudah dicapture -->
        <div
          v-if="capturedVehicle"
          class="flex items-center gap-3 bg-zinc-950 rounded-xl p-3 border border-zinc-800"
        >
          <img
            v-if="capturedVehicle.plate_image_url"
            :src="capturedVehicle.plate_image_url"
            alt="Plat"
            class="w-20 h-12 object-contain rounded-lg border border-zinc-700 bg-zinc-900"
          />
          <div class="flex-1 min-w-0">
            <p class="font-mono font-bold text-white text-lg tracking-wide">{{ capturedVehicle.plate_number }}</p>
            <p class="text-xs text-zinc-400">
              Confidence: {{ capturedVehicle.confidence ? `${capturedVehicle.confidence.toFixed(1)}%` : '---' }}
            </p>
          </div>
          <span
            :class="[
              'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
              isMasuk
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
            ]"
          >
            {{ dirLabel }}
          </span>
        </div>

        <!-- Display Info Deteksi Radar (Sebelum kamera capture) -->
        <div
          v-else
          class="flex items-center gap-3.5 bg-zinc-950/80 rounded-xl p-3.5 border border-zinc-800"
        >
          <div
            :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border relative',
              isMasuk ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
            ]"
          >
            <Car class="w-6 h-6" />
            <span
              :class="[
                'absolute -top-1 -right-1 w-3 h-3 rounded-full animate-ping',
                isMasuk ? 'bg-emerald-400' : 'bg-blue-400'
              ]"
            />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-white">Kendaraan Terdeteksi</p>
            <p class="text-xs text-zinc-400 mt-0.5">
              Kamera akan mengambil foto saat kartu RFID discan
            </p>
          </div>
          <span
            :class="[
              'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
              isMasuk
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
            ]"
          >
            {{ dirLabel }}
          </span>
        </div>

        <!-- State Berhasil -->
        <div v-if="submitted" class="space-y-3">
          <div class="flex items-center gap-2.5 bg-emerald-950/80 border border-emerald-800/60 rounded-xl px-4 py-3">
            <CheckCircle2 class="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <p class="text-sm font-semibold text-emerald-300">
                {{ capturedVehicle ? `Plat ${capturedVehicle.plate_number} Terbaca` : 'Deteksi Berhasil Diproses' }}
              </p>
              <p class="text-xs text-emerald-400/80">Perintah buka gate telah dikirimkan...</p>
            </div>
          </div>

          <!-- Warning RFID mismatch (keluar) -->
          <div v-if="rfidMatchResult === false" class="flex items-start gap-2 bg-amber-950/80 border border-amber-800/60 rounded-xl px-4 py-3">
            <AlertTriangle class="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p class="text-sm font-semibold text-amber-300">RFID Berbeda</p>
              <p class="text-xs text-amber-400/80">RFID tidak cocok dengan data entry masuk. Gate tetap dibuka.</p>
            </div>
          </div>
        </div>

        <!-- Form input RFID -->
        <div v-else class="space-y-4">
          <div>
            <label class="block text-xs text-zinc-400 font-medium mb-1.5">UID Kartu RFID</label>
            <div class="relative">
              <input
                ref="rfidRef"
                v-model="rfidInput"
                @keydown.enter.prevent="handleSubmit"
                type="text"
                placeholder="Scan kartu RFID..."
                autocomplete="off"
                :disabled="submitting"
                :class="[
                  'w-full bg-zinc-950 border rounded-xl px-4 py-3 text-lg font-mono text-white focus:outline-none transition disabled:opacity-50',
                  isMasuk ? 'border-zinc-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50' : 'border-zinc-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50',
                ]"
              />
              <Nfc class="absolute right-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500 pointer-events-none" />
            </div>
            <p class="text-[11px] text-zinc-500 mt-1.5">Scanner RFID otomatis mengetik UID dan menekan Enter.</p>
          </div>

          <!-- Error message -->
          <div v-if="submitError" class="flex items-start gap-2.5 bg-red-950/80 border border-red-800/60 rounded-xl px-3.5 py-2.5">
            <AlertTriangle class="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p class="text-xs text-red-300">{{ submitError }}</p>
          </div>

          <!-- Buttons -->
          <div class="flex gap-2.5 pt-1">
            <button
              @click="handleLanjutkan"
              :disabled="submitting"
              class="flex-1 flex items-center justify-center gap-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 font-medium py-2.5 px-3.5 rounded-xl text-xs sm:text-sm transition active:scale-[0.98] disabled:opacity-50"
            >
              <ArrowRight class="w-4 h-4" />
              Lanjutkan Tanpa RFID
            </button>
            <button
              @click="handleSubmit"
              :disabled="submitting || !rfidInput.trim()"
              :class="[
                'flex-1 flex items-center justify-center gap-2 border font-semibold py-2.5 px-4 rounded-xl text-xs sm:text-sm transition active:scale-[0.98] disabled:opacity-50',
                isMasuk
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500'
                  : 'bg-blue-600 hover:bg-blue-500 text-white border-blue-500',
              ]"
            >
              <Loader2 v-if="submitting" class="w-4 h-4 animate-spin" />
              <Camera v-else-if="props.detection" class="w-4 h-4" />
              <Nfc v-else class="w-4 h-4" />
              <span>{{ submitting ? 'Memotret & Proses...' : (props.detection ? 'Scan & Foto' : 'Submit RFID') }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
