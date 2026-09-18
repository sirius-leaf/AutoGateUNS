<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock, LogOut, User, Sun, Moon } from '@lucide/vue'
import { useTheme } from '@/composables/useTheme'

const props = defineProps({
  user: Object,
})

const emit = defineEmits(['logout'])

const { theme, toggleTheme } = useTheme()

const currentTime = ref('')
let timer = null

const updateTime = () => {
  const now = new Date()
  const dateStr = now.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  currentTime.value = `${dateStr} - ${timeStr}`
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <header class="h-16 border-b border-[var(--border)] bg-[var(--bg-panel)]/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
    <div class="min-w-0">
      <h2 class="text-base sm:text-lg font-bold text-[var(--text-primary)] tracking-tight truncate">Dashboard Monitoring Server</h2>
      <p class="text-xs text-[var(--text-muted)] hidden sm:block">Monitoring status pos satpam & riwayat kendaraan</p>
    </div>
    <div class="flex items-center gap-2 sm:gap-4 shrink-0">
      <!-- Clock -->
      <div class="hidden md:flex items-center gap-2 bg-[var(--bg-panel-alt)] border border-[var(--border)] px-3 py-1.5 rounded-lg text-xs font-mono text-[var(--text-primary)]">
        <Clock class="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span>{{ currentTime }}</span>
      </div>

      <!-- BARU: Theme Toggle -->
      <button
        @click="toggleTheme"
        class="p-2 rounded-lg border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
        :title="theme === 'dark' ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'"
      >
        <Sun v-if="theme === 'dark'" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
      </button>

      <!-- User Info + Logout -->
      <div class="flex items-center gap-2 sm:gap-3">
        <div class="flex items-center gap-2 bg-[var(--bg-panel-alt)] border border-[var(--border)] px-2.5 py-1.5 rounded-lg text-xs">
          <User class="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <span class="text-[var(--text-primary)] font-medium hidden xs:inline">{{ user?.name }}</span>
          <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-[var(--border)] text-[var(--text-muted)] uppercase">{{ user?.role }}</span>
        </div>
        <button
          @click="emit('logout')"
          class="p-2 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 transition"
          title="Logout"
        >
          <LogOut class="w-4 h-4" />
        </button>
      </div>
    </div>
  </header>
</template>