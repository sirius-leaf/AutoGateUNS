<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock, ChevronLeft, Sun, Moon } from '@lucide/vue'
import { useTheme } from '@/composables/useTheme'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
const emit = defineEmits(['navigate'])

const { theme, toggleTheme } = useTheme()

const currentTime = ref('')
let timer = null
const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('id-ID', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
    <div>
      <h2 class="text-xl font-bold text-[var(--text-primary)] tracking-tight">{{ title }}</h2>
      <p v-if="subtitle" class="text-xs text-[var(--text-muted)] mt-1">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2 shrink-0 flex-wrap">
      <slot name="actions" />
      <div class="flex items-center gap-1.5 bg-[var(--bg-panel-alt)] border border-[var(--border)] px-3 py-1.5 rounded-lg text-xs font-mono text-[var(--text-primary)]">
        <Clock class="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span>{{ currentTime }}</span>
      </div>
      <button
        @click="toggleTheme"
        class="p-2 rounded-lg border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
        :title="theme === 'dark' ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'"
      >
        <Sun v-if="theme === 'dark'" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
      </button>
      <button
        @click="emit('navigate', 'dashboard')"
        class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
      >
        <ChevronLeft class="w-3.5 h-3.5" />
        Beranda
      </button>
    </div>
  </div>
</template>
