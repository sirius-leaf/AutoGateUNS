<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import GateCard from '@/components/gate/GateCard.vue'
import PlateDetailModal from '@/components/gate/PlateDetailModal.vue'
import RfidInputModal from '@/components/gate/RfidInputModal.vue'
import SyncStatus from '@/components/sync/SyncStatus.vue'
import { Nfc, Loader2, Eye } from '@lucide/vue'
import api from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'

const gates = ref([
  {
    id: 1,
    title: 'Gate Masuk',
    lane: 'Lane 1',
    direction: 'masuk',
    timestamp: '',
    image: '',
    plate: '',
    confidence: null,
    barrierStatus: 'TERTUTUP',
  },
  {
    id: 2,
    title: 'Gate Keluar',
    lane: 'Lane 2',
    direction: 'keluar',
    timestamp: '',
    image: '',
    confidence: null,
    barrierStatus: 'TERTUTUP',
  },
])

const recentPlates = ref([])
const loading = ref(false)
const selectedPlate = ref(null)
let refreshTimer = null
let fastPollTimer = null
const emit = defineEmits(['navigate'])

// ── RFID Modal State ──
const pendingRfid = ref(null) // { vehicle, direction }
const lastSeenIds = ref(new Set()) // id kendaraan yang sudah diketahui
const firstLoad = ref(true) // skip deteksi pada load pertama

// ── Vehicle menunggu RFID (untuk banner) ──
const waitingRfidPlates = computed(() => {
  return recentPlates.value.filter(v => v.rfid_uid === null)
})

const fetchRecentPlates = async () => {
  try {
    const data = await api.getPlates({ limit: 10 })
    recentPlates.value = data.items || []

    // Update gate cards dengan data terbaru
    for (const dir of ['masuk', 'keluar']) {
      const latest = data.items?.find(v => v.direction === dir)
      if (latest) {
        const gate = gates.value.find(g => g.direction === dir)
        if (gate) {
          gate.plate = latest.plate_number
          gate.confidence = latest.confidence
          gate.timestamp = latest.captured_at
            ? new Date(latest.captured_at).toLocaleString('id-ID')
            : ''
        }
      }
    }

    // Deteksi vehicle baru tanpa RFID (dari Hikvision push otomatis)
    const currentIds = new Set((data.items || []).map(v => v.id))

    if (!firstLoad.value && !pendingRfid.value) {
      for (const item of (data.items || [])) {
        if (item.rfid_uid === null && !lastSeenIds.value.has(item.id)) {
          // Vehicle baru tanpa RFID — tampilkan modal
          pendingRfid.value = {
            vehicle: item,
            direction: item.direction,
          }
          break
        }
      }
    }

    // Update lastSeenIds setelah deteksi
    lastSeenIds.value = currentIds
    firstLoad.value = false
  } catch (err) {
    console.error('Gagal mengambil data:', err)
  }
}

const handleCapture = (direction) => {
  fetchRecentPlates()
}

const handleRefresh = () => {
  fetchRecentPlates()
}

// Handle capture response dari GateCard (manual capture)
const handleCaptureResponse = (response) => {
  if (response.rfid_pending && response.vehicle) {
    lastSeenIds.value.add(response.vehicle.id)
    pendingRfid.value = {
      vehicle: response.vehicle,
      direction: response.vehicle.direction,
    }
  }
}

// Klik banner "menunggu RFID" → buka modal lagi
const reopenRfidModal = (item) => {
  if (!pendingRfid.value) {
    pendingRfid.value = {
      vehicle: item,
      direction: item.direction,
    }
  }
}

const handleRfidDone = ({ rfid_match }) => {
  // Bisa tambahkan notifikasi jika rfid_match === false
}

const nodeStatus = ref(null)

const fetchStatus = async () => {
  try {
    nodeStatus.value = await api.getStatus()
  } catch (err) {
    nodeStatus.value = null
  }
}

const handleRfidClose = () => {
  pendingRfid.value = null
  fetchRecentPlates()
}

onMounted(() => {
  fetchRecentPlates()
  fetchStatus()
  // Polling utama: 15 detik
  refreshTimer = setInterval(() => {
    fetchRecentPlates()
    fetchStatus()
  }, 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="p-4 sm:p-6 space-y-6">
    <PageHeader
      title="Dashboard Operasional"
      subtitle="Monitoring gerbang masuk keluar museum secara real-time."
      @navigate="emit('navigate', $event)"
    />

    <!-- Banner: Menunggu RFID -->
    <div
      v-if="waitingRfidPlates.length > 0 && !pendingRfid"
      class="rounded-xl p-4 shadow-lg shadow-black/20 border animate-pulse"
      :style="{ borderColor: 'var(--status-pending)', backgroundColor: 'color-mix(in srgb, var(--status-pending) 12%, transparent)' }"
    >
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-lg" :style="{ backgroundColor: 'color-mix(in srgb, var(--status-pending) 20%, transparent)' }">
          <Nfc class="w-5 h-5 animate-bounce" :style="{ color: 'var(--status-pending)' }" />
        </div>
        <div class="flex-1">
          <p class="text-sm font-bold" :style="{ color: 'var(--status-pending)' }">Menunggu Input RFID</p>
          <p class="text-xs" :style="{ color: 'var(--status-pending)' }">
            {{ waitingRfidPlates.length }} kendaraan menunggu RFID:
            <span v-for="(p, i) in waitingRfidPlates" :key="p.id">
              <button
                @click="reopenRfidModal(p)"
                class="font-mono font-bold underline cursor-pointer hover:opacity-80"
                :style="{ color: 'var(--text-primary)' }"
              >{{ p.plate_number }}</button>{{ i < waitingRfidPlates.length - 1 ? ', ' : '' }}
            </span>
          </p>
        </div>
        <button
          v-if="waitingRfidPlates.length === 1"
          @click="reopenRfidModal(waitingRfidPlates[0])"
          class="px-4 py-2 text-white text-xs font-bold rounded-lg transition hover:opacity-90"
          :style="{ backgroundColor: 'var(--status-pending)' }"
        >
          Input RFID
        </button>
      </div>
    </div>

    <!-- Grid: Gate Cards + Sync Status -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <!-- Gate Cards (2 kolom) -->
      <div class="xl:col-span-2 space-y-6 min-w-0">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GateCard
            v-for="gate in gates"
            :key="gate.id"
            :gate="gate"
            :direction="gate.direction"
            :node-status="nodeStatus"
            @capture="handleCapture"
            @refresh="handleRefresh"
            @capture-response="handleCaptureResponse"
          />
        </div>

        <!-- Riwayat Terbaru -->
        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/20">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-[var(--text-primary)] tracking-tight">Riwayat Terbaru (10 Terakhir)</h3>
            <button
              @click="$emit('navigate', 'history')"
              class="text-xs font-semibold text-[var(--accent)] hover:underline transition"
            >
              Lihat Selengkapnya →
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-[var(--border)]">
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Event ID</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Waktu</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Arah</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Gambar</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Plat</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">RFID</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Confidence</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Sync</th>
                  <!-- BARU: kolom Detail -->
                  <th class="text-right py-2 px-3 text-[var(--text-muted)] font-medium">Detail</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="plate in recentPlates"
                  :key="plate.id"
                  class="border-b border-[var(--border)] hover:bg-[var(--bg-panel-alt)] cursor-pointer transition"
                  :style="plate.rfid_uid === null ? { backgroundColor: 'color-mix(in srgb, var(--status-pending) 8%, transparent)' } : null"
                  @click="selectedPlate = plate"
                >
                  <td class="py-2 px-3 font-mono text-[10px] text-[var(--text-muted)]">
                    {{ plate.event_id ? plate.event_id.substring(0, 8) + '...' : '---' }}
                  </td>
                  <td class="py-2 px-3 font-mono text-[var(--text-primary)]">
                    {{ plate.created_at ? new Date(plate.created_at).toLocaleString('id-ID') : '---' }}
                  </td>
                  <td class="py-2 px-3">
                    <span
                      class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold capitalize border"
                      :style="plate.direction === 'masuk'
                        ? { color: 'var(--status-ok)', borderColor: 'var(--status-ok)' }
                        : { color: 'var(--accent)', borderColor: 'var(--accent)' }"
                    >
                      <span
                        class="w-1.5 h-1.5 rounded-full"
                        :style="{ backgroundColor: plate.direction === 'masuk' ? 'var(--status-ok)' : 'var(--accent)' }"
                      ></span>
                      {{ plate.direction }}
                    </span>
                  </td>
                  <td class="py-2 px-3">
                    <img
                      v-if="plate.scene_image_url"
                      :src="plate.scene_image_url"
                      alt="Plat"
                      class="w-16 h-10 object-contain rounded border border-[var(--border)] bg-[var(--bg-panel-alt)]"
                    />
                    <span v-else class="text-[var(--text-muted)] opacity-60">---</span>
                  </td>
                  <td class="py-2 px-3 font-mono font-bold text-[var(--text-primary)]">{{ plate.plate_number }}</td>
                  <td class="py-2 px-3">
                    <span
                      v-if="plate.rfid_uid === '-'"
                      class="inline-flex items-center gap-1 font-mono text-[10px] text-[var(--text-muted)] border border-[var(--border)] bg-[var(--bg-panel-alt)] px-1.5 py-0.5 rounded"
                    >
                      Tanpa RFID
                    </span>
                    <span
                      v-else-if="plate.rfid_uid"
                      class="inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 rounded border"
                      :style="{ color: 'var(--accent)', borderColor: 'var(--accent)' }"
                    >
                      <Nfc class="w-3 h-3" />
                      {{ plate.rfid_uid }}
                    </span>
                    <span v-else class="inline-flex items-center gap-1 text-[10px] font-semibold" :style="{ color: 'var(--status-pending)' }">
                      <Loader2 class="w-3 h-3 animate-spin" />
                      Menunggu
                    </span>
                  </td>
                  <td class="py-2 px-3 text-[var(--text-primary)]">
                    {{ plate.confidence ? `${plate.confidence.toFixed(1)}%` : '---' }}
                  </td>
                  <td class="py-2 px-3">
                    <span
                      class="w-2 h-2 inline-block rounded-full"
                      :style="{ backgroundColor: plate.synced ? 'var(--status-ok)' : 'var(--status-pending)' }"
                      :title="plate.synced ? 'Terkirim' : 'Menunggu sync'"
                    ></span>
                  </td>
                  <!-- BARU: tombol Detail (klik baris tetap berfungsi) -->
                  <td class="py-2 px-3 text-right">
                    <button
                      @click.stop="selectedPlate = plate"
                      class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-semibold border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--accent)] transition"
                      title="Lihat detail kejadian"
                    >
                      <Eye class="w-3 h-3" />
                      Detail
                    </button>
                  </td>
                </tr>
                <tr v-if="!recentPlates.length">
                  <td colspan="9" class="py-4 text-center text-[var(--text-muted)]">Belum ada data</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Sidebar: Sync Status -->
      <div class="space-y-6">
        <SyncStatus />
      </div>
    </div>

    <!-- Modal Detail -->
    <PlateDetailModal
      v-if="selectedPlate"
      :plate="selectedPlate"
      @close="selectedPlate = null"
    />

    <!-- Modal RFID Input -->
    <RfidInputModal
      v-if="pendingRfid"
      :vehicle="pendingRfid.vehicle"
      :direction="pendingRfid.direction"
      @done="handleRfidDone"
      @close="handleRfidClose"
    />
  </div>
</template>