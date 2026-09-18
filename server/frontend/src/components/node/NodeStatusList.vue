<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Radio, Camera, Zap, Clock } from '@lucide/vue'
import api from '@/services/api'

const nodes = ref([])
const loading = ref(false)
const now = ref(Date.now())
let fetchTimer = null
let tickTimer = null

const fetchNodes = async () => {
  loading.value = true
  try {
    const data = await api.getNodes()
    nodes.value = data.items || data || []
  } catch (err) {
    console.error('Gagal mengambil data node:', err)
  } finally {
    loading.value = false
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

const formatBeat = (iso) => {
  if (!iso) return '---'
  const diffMs = now.value - new Date(iso).getTime()
  const diffSec = Math.max(0, Math.floor(diffMs / 1000))
  if (diffSec < 60) return `${diffSec}s lalu`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m lalu`
  const diffHour = Math.floor(diffMin / 60)
  return `${diffHour}j lalu`
}

onMounted(() => {
  fetchNodes()
  fetchTimer = setInterval(fetchNodes, 15000)
  tickTimer = setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (fetchTimer) clearInterval(fetchTimer)
  if (tickTimer) clearInterval(tickTimer)
})
</script>

<template>
  <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 shadow-xl shadow-black/40">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
        <Radio class="w-4 h-4 text-[var(--text-muted)]" />
        Status Pos Satpam
      </h3>
      <span class="text-xs text-[var(--text-muted)]">{{ nodes.length }} node</span>
    </div>

    <div v-if="!nodes.length && !loading" class="text-center py-6 text-[var(--text-muted)] text-sm">
      Belum ada pos satpam terdaftar
    </div>

    <div class="space-y-3">
      <div
        v-for="node in nodes"
        :key="node.id"
        class="bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg p-3 hover:border-[var(--text-muted)] transition"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span
              :class="[
                'w-2.5 h-2.5 rounded-full',
                node.status === 'online' ? 'bg-[var(--status-ok)]' : 'bg-[var(--status-fail)]',
              ]"
            ></span>
            <span class="text-sm font-bold text-[var(--text-primary)]">{{ node.name }}</span>
          </div>
          <span
            :class="[
              'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
              node.status === 'online'
                ? 'bg-[var(--status-ok)]/10 text-[var(--status-ok)] border border-[var(--status-ok)]/20'
                : 'bg-[var(--status-fail)]/10 text-[var(--status-fail)] border border-[var(--status-fail)]/20',
            ]"
          >
            {{ node.status }}
          </span>
        </div>

        <!-- ID -->
        <p class="text-[10px] text-[var(--text-muted)] font-mono mb-2">{{ node.id }}</p>

        <!-- Last Seen + Heartbeat -->
        <div class="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
          <div class="flex items-center gap-1.5">
            <Clock class="w-3 h-3" />
            <span>Terakhir terlihat: {{ formatTime(node.last_seen_at) }}</span>
          </div>
          <div class="flex items-center gap-1 text-[var(--text-muted)]">
            <Zap class="w-3 h-3" />
            <span>Beat: {{ formatBeat(node.last_seen_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>