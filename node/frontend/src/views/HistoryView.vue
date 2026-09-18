<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Search, Calendar, Filter, ChevronLeft, ChevronRight,
  RefreshCw, Loader2, History, X, Nfc, SlidersHorizontal,
} from '@lucide/vue'
import PlateDetailModal from '@/components/gate/PlateDetailModal.vue'
import api from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import { useTheme } from '@/composables/useTheme'

const { theme } = useTheme()

const items = ref([])
const total = ref(0)
const loading = ref(false)
const selectedPlate = ref(null)

// Filters & Pagination
const search = ref('')
const direction = ref('')
const startDate = ref('')
const endDate = ref('')
const rfidStatus = ref('')
const rfidSearch = ref('')
const synced = ref('')
const maxConfidence = ref('')
const showAdvancedFilters = ref(false)
const page = ref(1)
const perPage = 20

const emit = defineEmits(['navigate'])

// Search debouncer
let searchTimeout = null

const totalPages = computed(() => Math.ceil(total.value / perPage) || 1)

// BARU: badge status sinkronisasi (mendukung 3 status: pending/terkirim/gagal
// kalau backend sudah kirim field sync_status, kalau belum tetap fallback ke
// boolean item.synced seperti sebelumnya — tidak menghapus logic lama)
const getSyncBadge = (item) => {
  const raw = (item.sync_status || item.synced_status || '').toString().toLowerCase()
  if (raw === 'failed' || raw === 'gagal' || raw === 'error') {
    return { label: 'Gagal', tone: 'var(--status-fail)' }
  }
  if (raw === 'sent' || raw === 'synced' || raw === 'terkirim' || item.synced === true) {
    return { label: 'Terkirim', tone: 'var(--status-ok)' }
  }
  return { label: 'Pending', tone: 'var(--status-pending)' }
}

const fetchHistory = async () => {
  loading.value = true
  try {
    const skip = (page.value - 1) * perPage
    const data = await api.getPlates({
      skip,
      limit: perPage,
      direction: direction.value || undefined,
      search: search.value.trim() || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
      rfid_status: rfidStatus.value || undefined,
      rfid_search: rfidSearch.value.trim() || undefined,
      synced: synced.value === '' ? undefined : synced.value === 'true',
      max_confidence: maxConfidence.value !== '' ? Number(maxConfidence.value) : undefined,
    })
    items.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error('Gagal mengambil data riwayat:', err)
  } finally {
    loading.value = false
  }
}

const handleSearchInput = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    fetchHistory()
  }, 400)
}

const handleFilterChange = () => {
  page.value = 1
  fetchHistory()
}

const resetFilters = () => {
  search.value = ''
  direction.value = ''
  startDate.value = ''
  endDate.value = ''
  rfidStatus.value = ''
  rfidSearch.value = ''
  synced.value = ''
  maxConfidence.value = ''
  page.value = 1
  fetchHistory()
}

const goToPage = (newPage) => {
  if (newPage < 1 || newPage > totalPages.value) return
  page.value = newPage
  fetchHistory()
}

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="p-4 sm:p-6 space-y-6">
    <PageHeader
      title="Riwayat Kendaraan Lengkap"
      subtitle="Daftar seluruh kendaraan yang tercatat di Pos Satpam"
      @navigate="emit('navigate', $event)"
    >
      <template #actions>
        <button
          @click="fetchHistory"
          :disabled="loading"
          class="flex items-center justify-center gap-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-xs font-semibold px-4 py-2.5 rounded-lg border border-[var(--border)] transition disabled:opacity-50"
        >
          <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
          <RefreshCw v-else class="w-4 h-4 text-[var(--accent)]" />
          <span>Refresh Data</span>
        </button>
      </template>
    </PageHeader>

    <!-- Filter Bar -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/20 space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <!-- Search Plat -->
        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Cari Plat Nomor</label>
          <div class="relative">
            <input
              v-model="search"
              @input="handleSearchInput"
              type="text"
              placeholder="Contoh: AD1234AB..."
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] uppercase font-mono placeholder:normal-case placeholder:font-sans focus:outline-none focus:border-[var(--accent)]"
            />
            <Search class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        <!-- Filter Arah -->
        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Arah Pintu</label>
          <div class="relative">
            <select
              v-model="direction"
              @change="handleFilterChange"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
            >
              <option value="">Semua Arah</option>
              <option value="masuk">Masuk</option>
              <option value="keluar">Keluar</option>
            </select>
            <Filter class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        <!-- Tanggal Mulai -->
        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Dari Tanggal</label>
          <div class="relative cursor-pointer" @click="$refs.startDateInput?.showPicker()">
            <input
              ref="startDateInput"
              v-model="startDate"
              @change="handleFilterChange"
              @focus="$event.target.showPicker && $event.target.showPicker()"
              type="date"
              :style="{ colorScheme: theme }"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] cursor-pointer"
            />
            <Calendar class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        <!-- Tanggal Akhir -->
        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Sampai Tanggal</label>
          <div class="relative cursor-pointer" @click="$refs.endDateInput?.showPicker()">
            <input
              ref="endDateInput"
              v-model="endDate"
              @change="handleFilterChange"
              @focus="$event.target.showPicker && $event.target.showPicker()"
              type="date"
              :style="{ colorScheme: theme }"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] cursor-pointer"
            />
            <Calendar class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      <!-- Toggle Filter Lanjutan -->
      <div class="flex justify-end">
        <button
          @click="showAdvancedFilters = !showAdvancedFilters"
          class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition"
          :style="showAdvancedFilters
            ? { color: 'var(--accent)', borderColor: 'var(--accent)', backgroundColor: 'color-mix(in srgb, var(--accent) 12%, transparent)' }
            : { color: 'var(--text-muted)', borderColor: 'var(--border)', backgroundColor: 'var(--bg-panel-alt)' }"
        >
          <SlidersHorizontal class="w-3.5 h-3.5" />
          <span>Filter Lanjutan</span>
        </button>
      </div>

      <!-- Advanced Filters Panel -->
      <div v-if="showAdvancedFilters" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-[var(--border)]">
        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Status RFID</label>
          <select
            v-model="rfidStatus"
            @change="handleFilterChange"
            class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
          >
            <option value="">Semua Status</option>
            <option value="ada">Ada RFID</option>
            <option value="tanpa">Tanpa RFID</option>
            <option value="menunggu">Menunggu Input</option>
          </select>
        </div>

        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Cari RFID UID</label>
          <div class="relative">
            <input
              v-model="rfidSearch"
              @input="handleSearchInput"
              type="text"
              placeholder="Contoh: 04A2B1C3..."
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] uppercase font-mono placeholder:normal-case placeholder:font-sans focus:outline-none focus:border-[var(--accent)]"
            />
            <Nfc class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Status Sync</label>
          <select
            v-model="synced"
            @change="handleFilterChange"
            class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
          >
            <option value="">Semua Status</option>
            <option value="true">Terkirim</option>
            <option value="false">Pending</option>
          </select>
        </div>

        <div>
          <label class="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Confidence Maks (%)</label>
          <input
            v-model="maxConfidence"
            @change="handleFilterChange"
            type="number"
            min="0"
            max="100"
            placeholder="Contoh: 80"
            class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
          />
        </div>
      </div>

      <!-- Active Filters Reset -->
      <div v-if="search || direction || startDate || endDate || rfidStatus || rfidSearch || synced || maxConfidence" class="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs">
        <span class="text-[var(--text-muted)]">Filter aktif diterapkan</span>
        <button
          @click="resetFilters"
          class="flex items-center gap-1 font-medium hover:opacity-80"
          :style="{ color: 'var(--accent)' }"
        >
          <X class="w-3.5 h-3.5" />
          <span>Reset Filter</span>
        </button>
      </div>
    </div>

    <!-- Table Section -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/20 space-y-4">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">ID Kejadian</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Waktu Capture</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Arah</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Foto Plat</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Plat Nomor</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Kartu RFID</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Keyakinan</th>
              <th class="text-left py-3 px-3 text-[var(--text-muted)] font-semibold">Status Sinkronisasi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.id"
              class="border-b border-[var(--border)] hover:bg-[var(--bg-panel-alt)] cursor-pointer transition"
              @click="selectedPlate = item"
            >
              <td class="py-2.5 px-3 font-mono text-[10px] text-[var(--text-muted)]">
                {{ item.event_id ? item.event_id.substring(0, 8) + '...' : '---' }}
              </td>
              <td class="py-2.5 px-3 font-mono text-[var(--text-primary)]">
                {{ item.created_at ? new Date(item.created_at).toLocaleString('id-ID') : '---' }}
              </td>
              <td class="py-2.5 px-3">
                <span
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold capitalize"
                  :style="item.direction === 'masuk'
                    ? { color: 'var(--status-ok)', backgroundColor: 'color-mix(in srgb, var(--status-ok) 15%, transparent)' }
                    : { color: 'var(--accent)', backgroundColor: 'color-mix(in srgb, var(--accent) 15%, transparent)' }"
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full"
                    :style="{ backgroundColor: item.direction === 'masuk' ? 'var(--status-ok)' : 'var(--accent)' }"
                  ></span>
                  {{ item.direction }}
                </span>
              </td>
              <td class="py-2.5 px-3">
                <img
                  v-if="item.scene_image_url"
                  :src="item.scene_image_url"
                  alt="Plat"
                  class="w-16 h-10 object-contain rounded border border-[var(--border)] bg-[var(--bg-panel-alt)]"
                />
                <span v-else class="text-[var(--text-muted)] opacity-60">---</span>
              </td>
              <td class="py-2.5 px-3 font-mono font-bold text-[var(--text-primary)] text-sm tracking-wider">
                {{ item.plate_number }}
              </td>
              <td class="py-2.5 px-3">
                <span
                  v-if="item.rfid_uid === '-'"
                  class="inline-flex items-center gap-1 font-mono text-[11px] text-[var(--text-muted)] border border-[var(--border)] bg-[var(--bg-panel-alt)] px-2 py-1 rounded"
                >
                  Tanpa RFID
                </span>
                <span
                  v-else-if="item.rfid_uid"
                  class="inline-flex items-center gap-1 font-mono text-[11px] px-2 py-1 rounded border"
                  :style="{ color: 'var(--accent)', borderColor: 'var(--accent)' }"
                >
                  <Nfc class="w-3 h-3" />
                  {{ item.rfid_uid }}
                </span>
                <span v-else class="text-[var(--text-muted)] text-xs italic opacity-60">---</span>
              </td>
              <td class="py-2.5 px-3 text-[var(--text-primary)]">
                {{ item.confidence ? `${item.confidence.toFixed(1)}%` : '---' }}
              </td>
              <td class="py-2.5 px-3">
                <span
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                  :style="{ color: getSyncBadge(item).tone, backgroundColor: 'color-mix(in srgb, ' + getSyncBadge(item).tone + ' 15%, transparent)' }"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: getSyncBadge(item).tone }"></span>
                  {{ getSyncBadge(item).label }}
                </span>
              </td>
            </tr>
            <tr v-if="!loading && !items.length">
              <td colspan="8" class="py-8 text-center text-[var(--text-muted)]">
                Tidak ada data riwayat yang ditemukan.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Bar (20 item per halaman) -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3 border-t border-[var(--border)] text-xs">
        <div class="text-[var(--text-muted)] font-medium">
          Menampilkan <span class="text-[var(--text-primary)] font-bold">{{ items.length ? (page - 1) * perPage + 1 : 0 }}</span> -
          <span class="text-[var(--text-primary)] font-bold">{{ Math.min(page * perPage, total) }}</span> dari
          <span class="text-[var(--text-primary)] font-bold">{{ total }}</span> riwayat
        </div>

        <div class="flex items-center gap-1.5">
          <button
            @click="goToPage(page - 1)"
            :disabled="page <= 1 || loading"
            class="p-2 rounded-lg bg-[var(--bg-panel-alt)] border border-[var(--border)] hover:bg-[var(--border)] text-[var(--text-primary)] disabled:opacity-30 disabled:hover:bg-[var(--bg-panel-alt)] transition"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <span class="px-3 py-1.5 bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] font-mono">
            {{ page }} / {{ totalPages }}
          </span>
          <button
            @click="goToPage(page + 1)"
            :disabled="page >= totalPages || loading"
            class="p-2 rounded-lg bg-[var(--bg-panel-alt)] border border-[var(--border)] hover:bg-[var(--border)] text-[var(--text-primary)] disabled:opacity-30 disabled:hover:bg-[var(--bg-panel-alt)] transition"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Detail -->
    <PlateDetailModal
      v-if="selectedPlate"
      :plate="selectedPlate"
      @close="selectedPlate = null"
    />
  </div>
</template>