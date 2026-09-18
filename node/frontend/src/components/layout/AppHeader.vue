<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock, Settings, LayoutDashboard, Sun, Moon } from '@lucide/vue'
import api from '@/services/api'
import { useTheme } from '@/composables/useTheme'

const props = defineProps({
  currentView: String,
})

const emit = defineEmits(['navigate'])

const { theme, toggleTheme } = useTheme()

const currentTime = ref('')
const nodeStatus = ref(null)
let timer = null
let statusTimer = null

const updateTime = () => {
  const now = new Date()
  const dateStr = now.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  currentTime.value = `${dateStr} - ${timeStr}`
}

const fetchStatus = async () => {
  try {
    nodeStatus.value = await api.getStatus()
  } catch (err) {
    nodeStatus.value = null
  }
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  fetchStatus()
  statusTimer = setInterval(fetchStatus, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<template>
  <header class="min-h-[4rem] border-b border-[var(--border)] bg-[var(--bg-panel)]/90 backdrop-blur-md px-4 sm:px-6 py-2.5 sm:py-0 flex flex-wrap sm:flex-nowrap items-center justify-between gap-3 sticky top-0 z-20">
    <!-- Brand / Title & Nav Tabs -->
    <div class="flex items-center gap-3 sm:gap-6 min-w-0">
      <div class="min-w-0">
        <h2 class="text-base sm:text-lg font-bold text-[var(--text-primary)] tracking-tight truncate">
          Pos Satpam
        </h2>
        <p class="text-[11px] text-[var(--text-muted)] hidden md:block">Kontrol gerbang & monitoring kamera</p>
      </div>

      <!-- Nav Tabs -->
      <nav class="flex items-center gap-1 shrink-0">
        <button
          @click="emit('navigate', 'dashboard')"
          :class="[
            'flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium transition',
            currentView === 'dashboard'
              ? 'bg-[var(--accent)] text-white font-semibold'
              : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)]',
          ]"
        >
          <LayoutDashboard class="w-3.5 h-3.5" />
          <span>Dashboard</span>
        </button>
        <button
          @click="emit('navigate', 'settings')"
          :class="[
            'flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium transition',
            currentView === 'settings'
              ? 'bg-[var(--accent)] text-white font-semibold'
              : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)]',
          ]"
        >
          <Settings class="w-3.5 h-3.5" />
          <span>Settings</span>
        </button>
      </nav>
    </div>

    <!-- Status & Time -->
    <div class="flex items-center gap-2 sm:gap-4 shrink-0 ml-auto sm:ml-0">
      <!-- Status Indicator -->
      <div v-if="nodeStatus" class="flex items-center gap-2 sm:gap-3 bg-[var(--bg-panel-alt)] border border-[var(--border)] px-2.5 py-1.5 rounded-lg text-[11px] sm:text-xs">
        <div class="flex items-center gap-1.5" :title="nodeStatus.camera_in_active ? 'Kamera Masuk Aktif' : 'Kamera Masuk Nonaktif'">
          <span :class="['w-2 h-2 rounded-full', nodeStatus.camera_in_active ? 'bg-emerald-400' : 'bg-red-400']"></span>
          <span class="text-[var(--text-muted)]">Cam In</span>
        </div>
        <div class="flex items-center gap-1.5" :title="nodeStatus.camera_out_active ? 'Kamera Keluar Aktif' : 'Kamera Keluar Nonaktif'">
          <span :class="['w-2 h-2 rounded-full', nodeStatus.camera_out_active ? 'bg-emerald-400' : 'bg-red-400']"></span>
          <span class="text-[var(--text-muted)]">Cam Out</span>
        </div>
      </div>

      <!-- Time -->
      <div class="hidden lg:flex items-center gap-2 bg-[var(--bg-panel-alt)] border border-[var(--border)] px-3 py-1.5 rounded-lg text-xs font-mono text-[var(--text-primary)]">
        <Clock class="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span>{{ currentTime }}</span>
      </div>

      <!-- Theme Toggle -->
      <button
        @click="toggleTheme"
        class="p-2 rounded-lg border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
        :title="theme === 'dark' ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'"
      >
        <Sun v-if="theme === 'dark'" class="w-3.5 h-3.5" />
        <Moon v-else class="w-3.5 h-3.5" />
      </button>
    </div>
  </header>
</template>
