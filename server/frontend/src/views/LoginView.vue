<script setup>
import { ref } from 'vue'
import { Lock, User, Loader2, AlertTriangle, Server, Sun, Moon } from '@lucide/vue'
import api from '@/services/api'
import { useTheme } from '@/composables/useTheme'

const emit = defineEmits(['login-success'])

const { theme, toggleTheme } = useTheme()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = 'Username dan password wajib diisi'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await api.login(username.value, password.value)
    emit('login-success', data.user)
  } catch (err) {
    error.value = err.message || 'Login gagal'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[var(--bg-base)] flex items-center justify-center p-4 relative">
    <!-- BARU: Theme Toggle -->
    <button
      @click="toggleTheme"
      class="absolute top-4 right-4 p-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition"
      :title="theme === 'dark' ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'"
    >
      <Sun v-if="theme === 'dark'" class="w-4 h-4" />
      <Moon v-else class="w-4 h-4" />
    </button>

    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto rounded-2xl bg-[var(--bg-panel-alt)] border border-[var(--border)] flex items-center justify-center mb-4 shadow-xl shadow-black/30">
          <Server class="w-8 h-8 text-[var(--accent)]" />
        </div>
        <h1 class="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
          AutoGate <span style="color: var(--accent)">Parkir</span>
        </h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">Server Monitoring — Login</p>
      </div>

      <!-- Form -->
      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-6 shadow-xl shadow-black/20">
        <form @submit.prevent="handleLogin" class="space-y-4">
          <!-- Username -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1.5">Username</label>
            <div class="relative">
              <User class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
              <input
                v-model="username"
                type="text"
                placeholder="Masukkan username"
                autocomplete="username"
                class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30 transition"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1.5">Password</label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
              <input
                v-model="password"
                type="password"
                placeholder="Masukkan password"
                autocomplete="current-password"
                class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30 transition"
              />
            </div>
          </div>

          <!-- Error -->
          <div v-if="error" class="flex items-start gap-2 rounded-lg px-3 py-2 border"
               :style="{ borderColor: 'var(--status-fail)', backgroundColor: 'color-mix(in srgb, var(--status-fail) 12%, transparent)' }">
            <AlertTriangle class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: 'var(--status-fail)' }" />
            <p class="text-xs" :style="{ color: 'var(--status-fail)' }">{{ error }}</p>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-semibold py-2.5 px-4 rounded-lg text-sm transition active:scale-[0.98] disabled:opacity-50"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            <Lock v-else class="w-4 h-4" />
            <span>{{ loading ? 'Masuk...' : 'Masuk' }}</span>
          </button>
        </form>
      </div>

      <!-- Footer -->
      <p class="text-center text-[11px] text-[var(--text-muted)] mt-6">
        AutoGate Parkir — Sistem Monitoring Museum
      </p>
    </div>
  </div>
</template>