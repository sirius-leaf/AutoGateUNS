<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  LayoutDashboard,
  Settings,
  ShieldCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Clock,
  History,
} from '@lucide/vue'
import api from '@/services/api'

const props = defineProps({
  currentView: {
    type: String,
    default: 'dashboard',
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['navigate', 'toggle'])

const currentTime = ref('')
let timer = null

const updateTime = () => {
  const now = new Date()
  const dateStr = now.toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short' })
  const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  currentTime.value = `${dateStr} - ${timeStr}`
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'history', label: 'Riwayat', icon: History },
  { id: 'settings', label: 'Settings', icon: Settings },
]
</script>

<template>
  <aside
    :class="[
      'bg-[var(--bg-panel)] border-r border-[var(--border)] flex flex-col justify-between h-screen sticky top-0 z-30 select-none transition-all duration-300 shrink-0',
      collapsed ? 'w-16 sm:w-20' : 'w-64'
    ]"
  >
    <!-- Top Section -->
    <div>
      <!-- Header / Logo & Collapse Button -->
      <div
        :class="[
          'px-4 py-4 flex items-center border-b border-[var(--border)]',
          collapsed ? 'justify-center' : 'justify-between'
        ]"
      >
        <div v-if="!collapsed" class="flex items-center gap-3 overflow-hidden">
          <div class="w-9 h-9 shrink-0 rounded-lg bg-[var(--bg-panel-alt)] border border-[var(--border)] flex items-center justify-center shadow-md shadow-black/20">
            <ShieldCheck class="w-5 h-5 text-emerald-400" />
          </div>
          <div class="min-w-0">
            <h1 class="text-base font-bold text-[var(--text-primary)] tracking-wider flex items-center gap-1.5 whitespace-nowrap">
              Pos Satpam
            </h1>
            <p class="text-[11px] text-[var(--text-muted)] font-medium whitespace-nowrap">AutoGate Parkir</p>
          </div>
        </div>

        <button
          @click="emit('toggle')"
          class="p-2 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] border border-transparent hover:border-[var(--border)] transition shrink-0"
          :title="collapsed ? 'Buka Sidebar' : 'Tutup Sidebar'"
        >
          <PanelLeftOpen v-if="collapsed" class="w-5 h-5 text-emerald-400" />
          <PanelLeftClose v-else class="w-5 h-5" />
        </button>
      </div>

      <!-- Navigation -->
      <div class="p-3">
        <p v-if="!collapsed" class="px-3 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-3">
          Menu Utama
        </p>

        <nav class="space-y-1.5">
          <button
            v-for="item in navItems"
            :key="item.id"
            @click="emit('navigate', item.id)"
            :class="[
              'w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-sm font-semibold transition-all duration-150',
              collapsed ? 'justify-center px-0' : '',
              currentView === item.id
                ? 'bg-[var(--accent)] text-white shadow-sm'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)]',
            ]"
            :title="item.label"
          >
            <component :is="item.icon" class="w-5 h-5 shrink-0" />
            <span v-if="!collapsed" class="whitespace-nowrap">{{ item.label }}</span>
          </button>
        </nav>
      </div>
    </div>

    <!-- Bottom Section: Clock -->
    <div class="p-3 border-t border-[var(--border)] space-y-2">
      <div v-if="!collapsed" class="px-2 py-1 text-[11px] font-mono text-[var(--text-muted)] flex items-center gap-1.5">
        <Clock class="w-3.5 h-3.5 shrink-0" />
        <span class="truncate">{{ currentTime }}</span>
      </div>
    </div>
  </aside>
</template>
