<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { X, Car, ExternalLink, Nfc } from '@lucide/vue'

const props = defineProps({
  plate: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close'])

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

// BARU: badge status sinkronisasi
const syncBadge = computed(() => {
  const raw = (props.plate.sync_status || props.plate.synced_status || '').toString().toLowerCase()
  if (raw === 'sent' || raw === 'synced' || props.plate.synced === true) {
    return { label: 'Terkirim', tone: 'var(--status-ok)' }
  }
  if (raw === 'failed' || raw === 'error') {
    return { label: 'Gagal', tone: 'var(--status-fail)' }
  }
  if (raw === 'pending' || props.plate.synced === false) {
    return { label: 'Pending', tone: 'var(--status-pending)' }
  }
  return { label: '---', tone: 'var(--text-muted)' }
})

const handleClose = () => {
  emit('close')
}

const previewImage = ref(null)

const handlePreview = (url) => {
  if (url) previewImage.value = url
}

const closePreview = () => {
  previewImage.value = null
}

const onKeydown = (e) => {
  if (e.key === 'Escape') {
    if (previewImage.value) {
      closePreview()
    } else {
      handleClose()
    }
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
    @click.self="handleClose"
  >
    <div
      class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-2xl shadow-2xl shadow-black/40 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
        <div class="flex items-center gap-3">
          <Car class="w-5 h-5 text-[var(--accent)]" />
          <h3 class="text-lg font-bold text-[var(--text-primary)] tracking-tight">Detail Kendaraan</h3>
        </div>
        <button
          @click="handleClose"
          class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition"
          title="Tutup"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-6">
        <!-- Info Ringkas -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Plat</p>
            <p class="text-sm font-bold text-[var(--text-primary)] font-mono mt-0.5">{{ plate.plate_number }}</p>
          </div>
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Arah</p>
            <span
              class="inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
              :style="plate.direction === 'masuk'
                ? { color: 'var(--status-ok)', borderColor: 'var(--status-ok)' }
                : { color: 'var(--accent)', borderColor: 'var(--accent)' }"
            >
              {{ plate.direction }}
            </span>
          </div>
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Confidence</p>
            <p class="text-sm font-bold text-[var(--text-primary)] font-mono mt-0.5">
              {{ plate.confidence ? `${plate.confidence.toFixed(1)}%` : '---' }}
            </p>
          </div>
          <!-- BARU: badge Sinkronisasi -->
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Sinkronisasi</p>
            <span
              class="inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
              :style="{ color: syncBadge.tone, borderColor: syncBadge.tone }"
            >
              {{ syncBadge.label }}
            </span>
          </div>
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Waktu</p>
            <p class="text-xs font-mono text-[var(--text-primary)] mt-0.5">{{ formatTime(plate.captured_at || plate.created_at) }}</p>
          </div>
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Event ID</p>
            <p class="text-[10px] font-mono text-[var(--text-muted)] mt-0.5 break-all">{{ plate.event_id || '---' }}</p>
          </div>
          <div class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">RFID</p>
            <div class="flex items-center gap-1 mt-0.5">
              <span v-if="plate.rfid_uid === '-'" class="text-sm font-bold font-mono text-[var(--text-muted)]">
                Tanpa RFID
              </span>
              <template v-else-if="plate.rfid_uid">
                <Nfc class="w-3 h-3 text-[var(--accent)]" />
                <p class="text-sm font-bold font-mono text-[var(--text-primary)]">{{ plate.rfid_uid }}</p>
              </template>
              <p v-else class="text-sm font-bold font-mono text-[var(--text-muted)] opacity-60">---</p>
            </div>
          </div>
        </div>

        <!-- Gambar Plat -->
        <div v-if="plate.plate_image_url">
          <p class="text-xs font-medium text-[var(--text-muted)] mb-2">Gambar Plat</p>
          <div class="rounded-lg overflow-hidden border border-[var(--border)] bg-[var(--bg-panel-alt)]">
            <img
              :src="plate.plate_image_url"
              alt="Plat Nomor"
              class="w-full h-auto object-contain max-h-48 cursor-zoom-in hover:opacity-90 transition"
              @click="handlePreview(plate.plate_image_url)"
            />
          </div>
        </div>

        <!-- Gambar Full Scene -->
        <div v-if="plate.scene_image_url">
          <p class="text-xs font-medium text-[var(--text-muted)] mb-2">Gambar Kendaraan</p>
          <div class="rounded-lg overflow-hidden border border-[var(--border)] bg-[var(--bg-panel-alt)]">
            <img
              :src="plate.scene_image_url"
              alt="Kendaraan"
              class="w-full h-auto object-contain max-h-80 cursor-zoom-in hover:opacity-90 transition"
              @click="handlePreview(plate.scene_image_url)"
            />
          </div>
        </div>

        <div v-if="!plate.plate_image_url && !plate.scene_image_url" class="text-center py-8 text-[var(--text-muted)]">
          <ExternalLink class="w-10 h-10 mx-auto mb-2 opacity-50" />
          <p class="text-sm">Tidak ada gambar tersedia</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-3 border-t border-[var(--border)] flex justify-end">
        <button
          @click="handleClose"
          class="px-4 py-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-sm font-medium rounded-lg border border-[var(--border)] transition"
        >
          Tutup
        </button>
      </div>
    </div>

    <!-- Image Preview Modal Overlay -->
    <div
      v-if="previewImage"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-md p-4 cursor-zoom-out"
      @click="closePreview"
    >
      <img
        :src="previewImage"
        alt="Preview"
        class="max-w-full max-h-full object-contain"
      />
      <button
        @click.stop="closePreview"
        class="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/80 rounded-full text-white transition"
        title="Tutup Preview"
      >
        <X class="w-6 h-6" />
      </button>
    </div>
  </div>
</template>