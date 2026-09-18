<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Cloud, CloudOff, RefreshCw, Check, AlertTriangle, Loader2, Camera } from '@lucide/vue'
import api from '@/services/api'

const syncStatus = ref({
  server_online: false,
  pending: 0,
  sent: 0,
  failed: 0,
})
const loading = ref(false)
const syncing = ref(false)
let timer = null

// BARU: status kamera untuk panel "Status Kamera"
const nodeStatus = ref(null)

const fetchStatus = async () => {
  try {
    syncStatus.value = await api.getSyncStatus()
  } catch (err) {
    syncStatus.value.server_online = false
  }
}

// BARU
const fetchNodeStatus = async () => {
  try {
    nodeStatus.value = await api.getStatus()
  } catch (err) {
    nodeStatus.value = null
  }
}

const handleManualSync = async () => {
  syncing.value = true
  try {
    await api.manualSync()
    await fetchStatus()
  } catch (err) {
    console.error('Manual sync failed:', err)
  } finally {
    syncing.value = false
  }
}

onMounted(() => {
  fetchStatus()
  fetchNodeStatus()
  timer = setInterval(() => {
    fetchStatus()
    fetchNodeStatus()
  }, 10000) // refresh setiap 10 detik
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="space-y-4">
    <!-- Panel 1: Status Sinkronisasi -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/20">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
          <Cloud class="w-4 h-4 text-[var(--text-muted)]" />
          Status Sinkronisasi
        </h3>
        <button
          @click="handleManualSync"
          :disabled="syncing"
          class="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition disabled:opacity-50"
          title="Sync Manual"
        >
          <Loader2 v-if="syncing" class="w-4 h-4 animate-spin" />
          <RefreshCw v-else class="w-4 h-4" />
        </button>
      </div>

      <!-- Server Status -->
      <div class="flex items-center gap-2 mb-3">
        <span
          class="w-2.5 h-2.5 rounded-full"
          :style="{ backgroundColor: syncStatus.server_online ? 'var(--status-ok)' : 'var(--status-fail)' }"
        ></span>
        <span
          class="text-xs font-medium"
          :style="{ color: syncStatus.server_online ? 'var(--status-ok)' : 'var(--status-fail)' }"
        >
          {{ syncStatus.server_online ? 'Server Pusat Online' : 'Server Pusat Offline' }}
        </span>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 gap-2">
        <div class="bg-[var(--bg-panel-alt)] rounded-lg p-2 text-center border border-[var(--border)]">
          <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Pending</p>
          <p class="text-lg font-bold font-mono" :style="{ color: 'var(--status-pending)' }">{{ syncStatus.pending }}</p>
        </div>
        <div class="bg-[var(--bg-panel-alt)] rounded-lg p-2 text-center border border-[var(--border)]">
          <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Terkirim</p>
          <p class="text-lg font-bold font-mono" :style="{ color: 'var(--status-ok)' }">{{ syncStatus.sent }}</p>
        </div>
        <div class="bg-[var(--bg-panel-alt)] rounded-lg p-2 text-center border border-[var(--border)]">
          <p class="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">Gagal</p>
          <p class="text-lg font-bold font-mono" :style="{ color: 'var(--status-fail)' }">{{ syncStatus.failed }}</p>
        </div>
      </div>
    </div>

    <!-- BARU — Panel 2: Status Kamera -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/20">
      <h3 class="text-sm font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 mb-3">
        <Camera class="w-4 h-4 text-[var(--text-muted)]" />
        Status Kamera
      </h3>

      <div class="space-y-2">
        <div class="flex items-center justify-between bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
          <span class="text-xs text-[var(--text-muted)]">Kamera Masuk</span>
          <div class="flex items-center gap-1.5">
            <span
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: nodeStatus && nodeStatus.camera_in_active ? 'var(--status-ok)' : 'var(--status-fail)' }"
            ></span>
            <span
              class="text-[11px] font-semibold"
              :style="{ color: nodeStatus && nodeStatus.camera_in_active ? 'var(--status-ok)' : 'var(--status-fail)' }"
            >
              {{ nodeStatus && nodeStatus.camera_in_active ? 'Terhubung' : 'Tidak Terhubung' }}
            </span>
          </div>
        </div>

        <div class="flex items-center justify-between bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2">
          <span class="text-xs text-[var(--text-muted)]">Kamera Keluar</span>
          <div class="flex items-center gap-1.5">
            <span
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: nodeStatus && nodeStatus.camera_out_active ? 'var(--status-ok)' : 'var(--status-fail)' }"
            ></span>
            <span
              class="text-[11px] font-semibold"
              :style="{ color: nodeStatus && nodeStatus.camera_out_active ? 'var(--status-ok)' : 'var(--status-fail)' }"
            >
              {{ nodeStatus && nodeStatus.camera_out_active ? 'Terhubung' : 'Tidak Terhubung' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>