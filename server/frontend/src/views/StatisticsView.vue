<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import api from '@/services/api'

Chart.register(...registerables)

const loading = ref(true)
const errorMsg = ref('')
const data = ref(null)

const donutCanvas = ref(null)
const barCanvas = ref(null)
let donutChart = null
let barChart = null

const TYPE_COLORS = ['#7f77dd', '#1d9e75', '#f5821f', '#d4537e', '#378add']

const nodeTrafficTotal = computed(() => {
  if (!data.value?.node_traffic) return 0
  return data.value.node_traffic.reduce((sum, n) => sum + n.masuk + n.keluar, 0)
})

function formatDuration(minutes) {
  const total = Math.round(minutes)
  const h = Math.floor(total / 60)
  const m = total % 60
  if (h <= 0) return `${m}m`
  return `${h}j ${m}m`
}

function renderCharts() {
  if (!data.value) return

  if (donutChart) donutChart.destroy()
  if (barChart) barChart.destroy()

  const types = data.value.vehicle_type_distribution
  donutChart = new Chart(donutCanvas.value, {
    type: 'doughnut',
    data: {
      labels: types.map(t => t.type),
      datasets: [{
        data: types.map(t => t.count),
        backgroundColor: types.map((_, i) => TYPE_COLORS[i % TYPE_COLORS.length]),
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: { legend: { display: false } },
    },
  })

  const hours = data.value.busy_hours
  const peak = hours.reduce((max, h) => (h.count > max.count ? h : max), hours[0] || { count: 0 })
  barChart = new Chart(barCanvas.value, {
    type: 'bar',
    data: {
      labels: hours.map(h => h.hour),
      datasets: [{
        data: hours.map(h => h.count),
        backgroundColor: hours.map(h => (h.hour === peak.hour ? '#f5821f' : '#8a8f9c55')),
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { display: false, beginAtZero: true },
      },
    },
  })
}

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    data.value = await api.getStatisticsSummary()
    loading.value = false
    await nextTick()
    renderCharts()
  } catch (err) {
    errorMsg.value = err.message || 'Gagal memuat data statistik'
    loading.value = false
  }
}

function pct(part, total) {
  if (!total) return 0
  return Math.round((part / total) * 100)
}

onMounted(load)
onBeforeUnmount(() => {
  if (donutChart) donutChart.destroy()
  if (barChart) barChart.destroy()
})
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-lg font-bold text-[var(--text-primary)]">Statistika Kendaraan</h1>
      <p class="text-sm text-[var(--text-muted)]">Ringkasan data lalu lintas parkir hari ini</p>
    </div>

    <div v-if="loading" class="text-[var(--text-muted)] text-sm">Memuat data...</div>
    <div v-else-if="errorMsg" class="text-red-500 text-sm">{{ errorMsg }}</div>

    <template v-else-if="data">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 flex gap-3">
          <div class="w-10 h-10 rounded-lg bg-[var(--accent)]/15 flex items-center justify-center shrink-0">
            <span class="text-[var(--accent)] font-bold">🚗</span>
          </div>
          <div>
            <p class="text-xl font-bold text-[var(--accent)]">{{ data.summary.total_masuk }}</p>
            <p class="text-xs font-semibold text-[var(--text-primary)]">Total kendaraan masuk</p>
            <p class="text-[10px] text-[var(--text-muted)]">Semua tipe hari ini</p>
          </div>
        </div>

        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 flex gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-500/15 flex items-center justify-center shrink-0">
            <span class="text-blue-500 font-bold">+</span>
          </div>
          <div>
            <p class="text-xl font-bold text-blue-500">{{ data.summary.masih_di_dalam }}</p>
            <p class="text-xs font-semibold text-[var(--text-primary)]">Masih di dalam</p>
            <p class="text-[10px] text-[var(--text-muted)]">Belum keluar</p>
          </div>
        </div>

        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 flex gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-500/15 flex items-center justify-center shrink-0">
            <span class="text-green-500 font-bold">✓</span>
          </div>
          <div>
            <p class="text-xl font-bold text-green-500">{{ data.summary.selesai }}</p>
            <p class="text-xs font-semibold text-[var(--text-primary)]">Selesai parkir</p>
            <p class="text-[10px] text-[var(--text-muted)]">Sudah keluar</p>
          </div>
        </div>

        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 flex gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-500/15 flex items-center justify-center shrink-0">
            <span class="text-red-500 font-bold">!</span>
          </div>
          <div>
            <p class="text-xl font-bold text-red-500">{{ data.summary.rfid_tidak_cocok }}</p>
            <p class="text-xs font-semibold text-[var(--text-primary)]">RFID tidak cocok</p>
            <p class="text-[10px] text-[var(--text-muted)]">Perlu diperiksa</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex justify-between items-start mb-4">
            <div>
              <p class="text-sm font-semibold text-[var(--text-primary)]">Distribusi tipe kendaraan</p>
              <p class="text-[11px] text-[var(--text-muted)]">Perbandingan tipe kendaraan hari ini</p>
            </div>
            <span class="text-[10px] font-semibold bg-[var(--accent)]/15 text-[var(--accent)] rounded px-2 py-1">
              {{ data.summary.total_masuk }} total
            </span>
          </div>
          <div class="flex items-center gap-6">
            <div class="relative w-32 h-32 shrink-0">
              <canvas ref="donutCanvas"></canvas>
              <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span class="text-lg font-bold text-[var(--text-primary)]">{{ data.summary.total_masuk }}</span>
                <span class="text-[9px] text-[var(--text-muted)]">kendaraan</span>
              </div>
            </div>
            <div class="flex-1 text-xs space-y-2">
              <div v-for="(t, i) in data.vehicle_type_distribution" :key="t.type" class="flex justify-between items-center">
                <span class="flex items-center gap-2 text-[var(--text-primary)]">
                  <span class="w-2 h-2 rounded-full" :style="{ background: TYPE_COLORS[i % TYPE_COLORS.length] }"></span>
                  {{ t.type }}
                </span>
                <span class="text-[var(--text-muted)]">{{ t.count }}  {{ pct(t.count, data.summary.total_masuk) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex justify-between items-start mb-4">
            <div>
              <p class="text-sm font-semibold text-[var(--text-primary)]">Jam sibuk masuk</p>
              <p class="text-[11px] text-[var(--text-muted)]">Jumlah kendaraan per jam (07.00-16.00)</p>
            </div>
            <span class="text-[10px] font-semibold bg-[var(--accent)]/15 text-[var(--accent)] rounded px-2 py-1">
              puncak {{ data.busy_hours.reduce((m, h) => (h.count > m.count ? h : m), data.busy_hours[0] || { hour: '-', count: 0 }).hour }}.00
            </span>
          </div>
          <div class="h-28">
            <canvas ref="barCanvas"></canvas>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4">
          <p class="text-sm font-semibold text-[var(--text-primary)]">Breakdown status</p>
          <p class="text-[11px] text-[var(--text-muted)] mb-4">Proporsi tiap status kendaraan</p>

          <div class="space-y-3 text-xs mb-4">
            <div v-for="status in [
              { label: 'Selesai', key: 'selesai', color: 'green' },
              { label: 'Di dalam', key: 'di_dalam', color: 'blue' },
              { label: 'Tidak cocok', key: 'tidak_cocok', color: 'red' },
            ]" :key="status.key">
              <div class="flex justify-between mb-1">
                <span class="text-[var(--text-primary)]">
                  <span class="inline-block w-2 h-2 rounded-full mr-1" :class="`bg-${status.color}-500`"></span>{{ status.label }}
                </span>
                <span class="font-semibold" :class="`text-${status.color}-500`">
                  {{ data.status_breakdown[status.key] }}  {{ pct(data.status_breakdown[status.key], data.summary.total_masuk) }}%
                </span>
              </div>
              <div class="h-1.5 rounded bg-[var(--border)] overflow-hidden">
                <div class="h-full" :class="`bg-${status.color}-500`" :style="{ width: pct(data.status_breakdown[status.key], data.summary.total_masuk) + '%' }"></div>
              </div>
            </div>
          </div>

          <div class="border-t border-[var(--border)] pt-3 flex justify-between items-center">
            <div>
              <p class="text-[11px] text-[var(--text-muted)]">Rata-rata durasi parkir</p>
              <p class="text-[10px] text-[var(--text-muted)]">Dari {{ data.status_breakdown.selesai }} kendaraan selesai</p>
            </div>
            <p class="text-base font-bold text-[var(--accent)]">{{ formatDuration(data.avg_duration_minutes) }}</p>
          </div>
        </div>

        <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4">
          <p class="text-sm font-semibold text-[var(--text-primary)]">Trafik per node</p>
          <p class="text-[11px] text-[var(--text-muted)] mb-4">Jumlah kendaraan masuk per pos satpam</p>

          <div class="space-y-3 text-xs mb-4">
            <div v-for="(n, i) in data.node_traffic" :key="n.node_id">
              <div class="flex justify-between mb-1">
                <span class="text-[var(--text-primary)]">
                  <span class="font-semibold text-[var(--accent)] mr-1">{{ i + 1 }}</span>{{ n.node_name }}
                </span>
                <span class="font-semibold text-[10px]">
                  <span class="text-[var(--accent)]">{{ n.masuk }} masuk</span>
                  <span class="text-[var(--text-muted)]"> · </span>
                  <span class="text-blue-500">{{ n.keluar }} keluar</span>
                </span>
              </div>
              <div class="h-1.5 rounded bg-[var(--border)] overflow-hidden flex">
                <div class="h-full bg-[var(--accent)]" :style="{ width: pct(n.masuk, nodeTrafficTotal) + '%' }"></div>
                <div class="h-full bg-blue-500" :style="{ width: pct(n.keluar, nodeTrafficTotal) + '%' }"></div>
              </div>
            </div>
            <p v-if="!data.node_traffic.length" class="text-[var(--text-muted)]">Belum ada node terdaftar.</p>
          </div>

          <div class="border-t border-[var(--border)] pt-3 flex gap-6">
            <div>
              <p class="text-base font-bold text-[var(--accent)]">{{ data.active_nodes }}</p>
              <p class="text-[10px] text-[var(--text-muted)]">Node aktif</p>
            </div>
            <div>
              <p class="text-base font-bold text-[var(--accent)]">{{ data.unique_vehicle_types }}</p>
              <p class="text-[10px] text-[var(--text-muted)]">Tipe unik</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

