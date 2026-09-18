<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { History, Search, Filter, ChevronLeft, ChevronRight, Eye, Nfc, CheckCircle2, AlertTriangle, XCircle } from '@lucide/vue'
import VehicleHistoryDetailModal from '@/components/gate/VehicleHistoryDetailModal.vue'
import api from '@/services/api'

const history = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(0)
const limit = 20

const selectedHistory = ref(null)

const filterPlate = ref('')
const filterStatus = ref('')
let refreshTimer = null

const fetchHistory = async () => {
  loading.value = true
  try {
    const params = {
      skip: page.value * limit,
      limit,
    }
    if (filterPlate.value) params.plate_number = filterPlate.value
    if (filterStatus.value === 'inside') params.is_inside = true
    if (filterStatus.value === 'outside') params.is_inside = false

    const data = await api.getHistory(params)
    history.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Gagal mengambil history:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 0
  fetchHistory()
}

const nextPage = () => {
  if ((page.value + 1) * limit < total.value) {
    page.value++
    fetchHistory()
  }
}

const prevPage = () => {
  if (page.value > 0) {
    page.value--
    fetchHistory()
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

const rfidMatchStatus = (h) => {
  if (!h.exit_at) return null
  if (!h.entry_rfid && !h.exit_rfid) return 'none'
  if (!h.entry_rfid || !h.exit_rfid) return 'incomplete'
  return h.entry_rfid === h.exit_rfid ? 'match' : 'mismatch'
}

onMounted(() => {
  fetchHistory()
  refreshTimer = setInterval(fetchHistory, 30000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div class="p-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
          <History class="w-5 h-5 text-[var(--text-muted)]" />
          Riwayat Kendaraan
        </h2>
        <p class="text-xs text-[var(--text-muted)] mt-1">Data gabungan masuk + keluar kendaraan</p>
      </div>
      <span class="text-xs text-[var(--text-muted)] bg-[var(--bg-panel-alt)] border border-[var(--border)] px-2.5 py-1 rounded-full">{{ total }} data</span>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <div class="relative flex-1 max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
        <input
          v-model="filterPlate"
          type="text"
          placeholder="Cari plat nomor..."
          @keyup.enter="handleSearch"
          class="w-full bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
        />
      </div>
      <select
        v-model="filterStatus"
        @change="handleSearch"
        class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
      >
        <option value="">Semua Status</option>
        <option value="inside">Di Dalam</option>
        <option value="outside">Sudah Keluar</option>
      </select>
      <button @click="handleSearch" class="px-4 py-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-sm rounded-lg transition border border-[var(--border)]">
        Cari
      </button>
    </div>

    <!-- Table -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-xl shadow-black/40 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Plat</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Pemilik</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Masuk</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Keluar</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Node Masuk</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Node Keluar</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">RFID Masuk</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">RFID Keluar</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Cocok?</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Status</th>
              <th class="text-center py-3 px-4 text-[var(--text-muted)] font-medium">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="h in history"
              :key="h.id"
              class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] transition-colors"
            >
              <td class="py-3 px-4 font-mono font-bold text-[var(--text-primary)]">{{ h.plate_number }}</td>
              <td class="py-3 px-4 text-[var(--text-primary)]">{{ h.owner_name || '---' }}</td>
              <td class="py-3 px-4">
                <div class="text-[var(--text-primary)] font-mono">{{ formatTime(h.entry_at) }}</div>
                <div class="text-[10px] text-[var(--text-muted)]">{{ h.entry_node_name || '---' }}</div>
              </td>
              <td class="py-3 px-4">
                <div class="text-[var(--text-primary)] font-mono">{{ formatTime(h.exit_at) }}</div>
                <div class="text-[10px] text-[var(--text-muted)]">{{ h.exit_node_name || '---' }}</div>
              </td>
              <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--bg-panel-alt)] text-[var(--text-primary)] font-mono border border-[var(--border)]">
                  {{ h.entry_node_name || '---' }}
                </span>
              </td>
              <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--bg-panel-alt)] text-[var(--text-primary)] font-mono border border-[var(--border)]">
                  {{ h.exit_node_name || '---' }}
                </span>
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="h.entry_rfid"
                  class="inline-flex items-center gap-1 font-mono text-[10px] text-violet-400 bg-violet-500/10 border border-violet-500/20 px-1.5 py-0.5 rounded"
                >
                  <Nfc class="w-3 h-3" />
                  {{ h.entry_rfid }}
                </span>
                <span v-else class="text-[var(--text-muted)] text-[10px]">Tanpa RFID</span>
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="h.exit_rfid"
                  class="inline-flex items-center gap-1 font-mono text-[10px] text-violet-400 bg-violet-500/10 border border-violet-500/20 px-1.5 py-0.5 rounded"
                >
                  <Nfc class="w-3 h-3" />
                  {{ h.exit_rfid }}
                </span>
                <span v-else-if="!h.is_inside" class="text-[var(--text-muted)] text-[10px]">Tanpa RFID</span>
                <span v-else class="text-[var(--text-muted)] text-[10px]">---</span>
              </td>
              <td class="py-3 px-4">
                <template v-if="rfidMatchStatus(h) === 'match'">
                  <span class="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--status-ok)]">
                    <CheckCircle2 class="w-3.5 h-3.5" /> Cocok
                  </span>
                </template>
                <template v-else-if="rfidMatchStatus(h) === 'mismatch'">
                  <span class="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--status-fail)]">
                    <XCircle class="w-3.5 h-3.5" /> Beda
                  </span>
                </template>
                <template v-else-if="rfidMatchStatus(h) === 'incomplete'">
                  <span class="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--status-pending)]">
                    <AlertTriangle class="w-3.5 h-3.5" /> Parsial
                  </span>
                </template>
                <template v-else-if="rfidMatchStatus(h) === 'none'">
                  <span class="text-[var(--text-muted)] text-[10px]">Tanpa RFID</span>
                </template>
                <template v-else>
                  <span class="text-[var(--text-muted)] text-[10px]">---</span>
                </template>
              </td>
              <td class="py-3 px-4">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                    h.is_inside
                      ? 'bg-[var(--status-info)]/10 text-[var(--status-info)] border border-[var(--status-info)]/20'
                      : 'bg-[var(--status-ok)]/10 text-[var(--status-ok)] border border-[var(--status-ok)]/20',
                  ]"
                >
                  {{ h.is_inside ? 'Di Dalam' : 'Keluar' }}
                </span>
              </td>
              <td class="py-3 px-4 text-center">
                <button
                  @click="selectedHistory = h"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-xs transition border border-[var(--border)]"
                  title="Lihat Detail"
                >
                  <Eye class="w-3.5 h-3.5 text-blue-400" />
                  <span>Detail</span>
                </button>
              </td>
            </tr>
            <tr v-if="!history.length && !loading">
              <td colspan="12" class="py-12">
                <div class="flex flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                  <History class="w-8 h-8 opacity-30" />
                  <span class="text-sm">Belum ada data riwayat</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between px-4 py-3 border-t border-[var(--border)]">
        <p class="text-xs text-[var(--text-muted)]">
          Menampilkan {{ page * limit + 1 }}-{{ Math.min((page + 1) * limit, total) }} dari {{ total }}
        </p>
        <div class="flex items-center gap-2">
          <button
            @click="prevPage"
            :disabled="page === 0"
            class="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition disabled:opacity-30"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="text-xs text-[var(--text-muted)]">{{ page + 1 }}</span>
          <button
            @click="nextPage"
            :disabled="(page + 1) * limit >= total"
            class="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition disabled:opacity-30"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <VehicleHistoryDetailModal
      v-if="selectedHistory"
      :history="selectedHistory"
      @close="selectedHistory = null"
    />
  </div>
</template>