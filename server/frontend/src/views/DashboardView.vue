<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { BarChart3, Car, Radio, Wifi, WifiOff, History, ArrowRight } from '@lucide/vue'
import NodeStatusList from '@/components/node/NodeStatusList.vue'
import api from '@/services/api'

const emit = defineEmits(['navigate'])

const summary = ref({
  total_events: 0,
  today_events: 0,
  vehicles_inside: 0,
  total_nodes: 0,
  online_nodes: 0,
  offline_nodes: 0,
})

const recentHistory = ref([])
const loading = ref(false)
let refreshTimer = null

const fetchData = async () => {
  loading.value = true
  try {
    const [summaryData, historyData] = await Promise.all([
      api.getDashboardSummary(),
      api.getHistory({ limit: 10 }),
    ])
    summary.value = summaryData
    recentHistory.value = historyData.items || []
  } catch (err) {
    console.error('Gagal mengambil data:', err)
  } finally {
    loading.value = false
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

// Field response getHistory() sudah dikonfirmasi dari HistoryView.vue
const getEntryTime = (h) => h.entry_at
const getExitTime = (h) => h.exit_at
const getIsInside = (h) => h.is_inside

onMounted(() => {
  fetchData()
  refreshTimer = setInterval(fetchData, 15000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div class="p-4 sm:p-6 space-y-6">
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
            <BarChart3 class="w-5 h-5 text-blue-400" />
          </div>
          <div class="min-w-0">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider truncate">Total Event</p>
            <p class="text-2xl font-bold text-[var(--text-primary)] font-mono">{{ summary.total_events }}</p>
            <p class="text-[10px] text-[var(--text-muted)]">Sepanjang waktu</p>
          </div>
        </div>
      </div>

      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-[var(--accent)]/10 border border-[var(--accent)]/20 flex items-center justify-center shrink-0">
            <Car class="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div class="min-w-0">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider truncate">Hari Ini</p>
            <p class="text-2xl font-bold text-[var(--text-primary)] font-mono">{{ summary.today_events }}</p>
            <p class="text-[10px] text-[var(--text-muted)]">Sejak 00:00</p>
          </div>
        </div>
      </div>

      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-[var(--status-ok)]/10 border border-[var(--status-ok)]/20 flex items-center justify-center shrink-0">
            <Car class="w-5 h-5 text-[var(--status-ok)]" />
          </div>
          <div class="min-w-0">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider truncate">Di Dalam</p>
            <p class="text-2xl font-bold text-[var(--text-primary)] font-mono">{{ summary.vehicles_inside }}</p>
            <p class="text-[10px] text-[var(--text-muted)]">Saat ini</p>
          </div>
        </div>
      </div>

      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-[var(--status-ok)]/10 border border-[var(--status-ok)]/20 flex items-center justify-center shrink-0">
            <Wifi class="w-5 h-5 text-[var(--status-ok)]" />
          </div>
          <div class="min-w-0">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider truncate">Node Online</p>
            <p class="text-2xl font-bold text-[var(--text-primary)] font-mono">{{ summary.online_nodes }}</p>
            <p class="text-[10px] text-[var(--text-muted)]">Semua node aktif</p>
          </div>
        </div>
      </div>

      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-[var(--status-fail)]/10 border border-[var(--status-fail)]/20 flex items-center justify-center shrink-0">
            <WifiOff class="w-5 h-5 text-[var(--status-fail)]" />
          </div>
          <div class="min-w-0">
            <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider truncate">Node Offline</p>
            <p class="text-2xl font-bold text-[var(--text-primary)] font-mono">{{ summary.offline_nodes }}</p>
            <p class="text-[10px] text-[var(--text-muted)]">Tidak ada gangguan</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <!-- History -->
      <div class="xl:col-span-2 space-y-6 min-w-0">
        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
              <History class="w-4 h-4 text-[var(--text-muted)]" />
              Riwayat Terbaru
            </h3>
            <button
              @click="emit('navigate', 'history')"
              class="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 hover:bg-[var(--bg-panel-alt)] px-2.5 py-1 rounded-lg transition border border-transparent hover:border-[var(--border)]"
            >
              <span>Lihat Semua</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-[var(--border)]">
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Plat Nomor</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Waktu Masuk</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Waktu Keluar</th>
                  <th class="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="h in recentHistory"
                  :key="h.id"
                  class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] cursor-pointer"
                >
                  <td class="py-2 px-3 font-mono font-bold text-[var(--text-primary)]">{{ h.plate_number }}</td>
                  <td class="py-2 px-3 text-[var(--text-primary)]">{{ formatTime(getEntryTime(h)) }}</td>
                  <td class="py-2 px-3 text-[var(--text-primary)]">{{ formatTime(getExitTime(h)) }}</td>
                  <td class="py-2 px-3">
                    <span
                      :class="[
                        'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                        getIsInside(h)
                          ? 'bg-[var(--status-info)]/10 text-[var(--status-info)] border border-[var(--status-info)]/20'
                          : 'bg-[var(--status-ok)]/10 text-[var(--status-ok)] border border-[var(--status-ok)]/20',
                      ]"
                    >
                      {{ getIsInside(h) ? 'Di Dalam' : 'Selesai' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="!recentHistory.length">
                  <td colspan="4" class="py-4 text-center text-[var(--text-muted)]">Belum ada data</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Sidebar: Node Status -->
      <div class="space-y-6">
        <NodeStatusList />
      </div>
    </div>
  </div>
</template>