<script setup>
import { ref, onMounted } from 'vue'
import { Activity, Search, Filter, Camera, ArrowDownRight, ArrowUpRight, Loader2, Nfc } from '@lucide/vue'
import api from '@/services/api'

const events = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(0)
const limit = 50

const filterPlate = ref('')
const filterDirection = ref('')

const fetchEvents = async () => {
  loading.value = true
  try {
    const params = { skip: page.value * limit, limit }
    if (filterPlate.value) params.plate_number = filterPlate.value
    if (filterDirection.value) params.direction = filterDirection.value
    const data = await api.getEvents(params)
    events.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 0
  fetchEvents()
}

const nextPage = () => {
  if ((page.value + 1) * limit < total.value) {
    page.value++
    fetchEvents()
  }
}

const prevPage = () => {
  if (page.value > 0) {
    page.value--
    fetchEvents()
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

const imageUrl = (path) => {
  if (!path) return null
  const filename = path.split('/').pop()
  return `/storage/captures/${filename}`
}

onMounted(fetchEvents)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Activity class="w-5 h-5 text-[var(--text-muted)]" />
          Event Kendaraan
        </h2>
        <p class="text-xs text-[var(--text-muted)] mt-1">Semua event masuk/keluar dari semua node</p>
      </div>
      <span class="text-xs text-[var(--text-muted)] bg-[var(--bg-panel-alt)] border border-[var(--border)] px-2.5 py-1 rounded-full">{{ total }} event</span>
    </div>

    <!-- Filter -->
    <div class="mb-4 flex gap-2 flex-wrap">
      <div class="relative flex-1 max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
        <input
          v-model="filterPlate"
          type="text"
          placeholder="Cari plat..."
          @keyup.enter="handleSearch"
          class="w-full bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
        />
      </div>
      <select
        v-model="filterDirection"
        @change="handleSearch"
        class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
      >
        <option value="">Semua Arah</option>
        <option value="masuk">Masuk</option>
        <option value="keluar">Keluar</option>
      </select>
      <button @click="handleSearch" class="px-4 py-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-sm rounded-lg transition border border-[var(--border)]">
        <Filter class="w-4 h-4" />
      </button>
    </div>

    <!-- Table -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-xl shadow-black/40 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Waktu</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Plat</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Arah</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Node</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">RFID</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Confidence</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Gambar</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="e in events"
              :key="e.id"
              class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] transition-colors"
            >
              <td class="py-3 px-4 text-[var(--text-muted)] whitespace-nowrap">{{ formatTime(e.captured_at || e.created_at) }}</td>
              <td class="py-3 px-4 font-mono font-bold text-[var(--text-primary)]">{{ e.plate_number }}</td>
              <td class="py-3 px-4">
                <span
                  v-if="e.direction === 'masuk'"
                  class="inline-flex items-center gap-1 text-[var(--status-ok)] bg-[var(--status-ok)]/10 px-2 py-0.5 rounded-full text-[10px] font-medium"
                >
                  <ArrowDownRight class="w-3 h-3" /> Masuk
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1 text-[var(--status-fail)] bg-[var(--status-fail)]/10 px-2 py-0.5 rounded-full text-[10px] font-medium"
                >
                  <ArrowUpRight class="w-3 h-3" /> Keluar
                </span>
              </td>
              <td class="py-3 px-4 text-[var(--text-muted)] font-mono text-[10px]">{{ e.node_name || e.node_id }}</td>
              <td class="py-3 px-4">
                <span
                  v-if="e.rfid_uid"
                  class="inline-flex items-center gap-1 font-mono text-[10px] text-violet-400 bg-violet-500/10 border border-violet-500/20 px-1.5 py-0.5 rounded"
                >
                  <Nfc class="w-3 h-3" />
                  {{ e.rfid_uid }}
                </span>
                <span v-else class="text-[var(--text-muted)]">---</span>
              </td>
              <td class="py-3 px-4 text-[var(--text-muted)]">{{ e.confidence ? `${e.confidence}%` : '---' }}</td>
              <td class="py-3 px-4">
                <div class="flex gap-1">
                  <a
                    v-if="e.plate_image_url"
                    :href="e.plate_image_url"
                    target="_blank"
                    class="text-blue-400 hover:text-blue-300 transition"
                    title="Plat"
                  >
                    <Camera class="w-3.5 h-3.5" />
                  </a>
                  <a
                    v-if="e.scene_image_url"
                    :href="e.scene_image_url"
                    target="_blank"
                    class="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
                    title="Scene"
                  >
                    <Camera class="w-3.5 h-3.5" />
                  </a>
                  <span v-if="!e.plate_image_url && !e.scene_image_url" class="text-[var(--text-muted)]">---</span>
                </div>
              </td>
            </tr>
            <tr v-if="!events.length && !loading">
              <td colspan="7" class="py-12">
                <div class="flex flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                  <Activity class="w-8 h-8 opacity-30" />
                  <span class="text-sm">Belum ada event</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-4 gap-2 text-[var(--text-muted)]">
        <Loader2 class="w-4 h-4 animate-spin text-[var(--accent)]" />
        <span class="text-xs">Memuat...</span>
      </div>

      <!-- Pagination -->
      <div v-if="total > limit" class="flex items-center justify-between px-4 py-3 border-t border-[var(--border)]">
        <span class="text-xs text-[var(--text-muted)]">Halaman {{ page + 1 }} dari {{ Math.ceil(total / limit) }}</span>
        <div class="flex gap-1">
          <button
            @click="prevPage"
            :disabled="page === 0"
            class="px-3 py-1 text-xs bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] rounded disabled:opacity-30 transition border border-[var(--border)]"
          >Prev</button>
          <button
            @click="nextPage"
            :disabled="(page + 1) * limit >= total"
            class="px-3 py-1 text-xs bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] rounded disabled:opacity-30 transition border border-[var(--border)]"
          >Next</button>
        </div>
      </div>
    </div>
  </div>
</template>