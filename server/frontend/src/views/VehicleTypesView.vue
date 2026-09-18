<script setup>
import { ref, onMounted } from 'vue'
import { Tag, Plus, Pencil, Trash2, X, Loader2, Check, AlertTriangle } from '@lucide/vue'
import api from '@/services/api'

const types = ref([])
const loading = ref(false)
const showModal = ref(false)
const editingType = ref(null)
const saving = ref(false)
const error = ref('')

const form = ref({
  name: '',
})

const fetchTypes = async () => {
  loading.value = true
  try {
    const data = await api.getVehicleTypes()
    types.value = data.items || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingType.value = null
  form.value = { name: '' }
  error.value = ''
  showModal.value = true
}

const openEdit = (t) => {
  editingType.value = t
  form.value = {
    name: t.name,
  }
  error.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingType.value = null
  error.value = ''
}

const handleSave = async () => {
  saving.value = true
  error.value = ''
  try {
    if (editingType.value) {
      await api.updateVehicleType(editingType.value.id, form.value)
    } else {
      await api.createVehicleType(form.value)
    }
    closeModal()
    await fetchTypes()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

const handleDelete = async (t) => {
  if (!confirm(`Hapus tipe kendaraan '${t.name}'?`)) return
  try {
    await api.deleteVehicleType(t.id)
    await fetchTypes()
  } catch (err) {
    alert(err.message)
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

onMounted(fetchTypes)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Tag class="w-5 h-5 text-[var(--text-muted)]" />
          Tipe Kendaraan
        </h2>
        <p class="text-xs text-[var(--text-muted)] mt-1">Master data tipe kendaraan</p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg text-sm transition"
      >
        <Plus class="w-4 h-4" />
        Tambah Tipe
      </button>
    </div>

    <!-- Table -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-xl shadow-black/40 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">ID</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Nama</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Dibuat</th>
              <th class="text-right py-3 px-4 text-[var(--text-muted)] font-medium">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in types"
              :key="t.id"
              class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] transition-colors"
            >
              <td class="py-3 px-4 text-[var(--text-muted)] font-mono">{{ t.id }}</td>
              <td class="py-3 px-4 font-semibold text-[var(--text-primary)]">{{ t.name }}</td>
              <td class="py-3 px-4 text-[var(--text-muted)] whitespace-nowrap">{{ formatTime(t.created_at) }}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button @click="openEdit(t)" class="p-1.5 rounded text-[var(--text-muted)] hover:text-blue-400 hover:bg-blue-500/10 transition" title="Edit">
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button @click="handleDelete(t)" class="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--status-fail)] hover:bg-[var(--status-fail)]/10 transition" title="Hapus">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!types.length && !loading">
              <td colspan="4" class="py-12">
                <div class="flex flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                  <Tag class="w-8 h-8 opacity-30" />
                  <span class="text-sm">Belum ada tipe kendaraan</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="loading" class="flex items-center justify-center py-4 gap-2 text-[var(--text-muted)]">
        <Loader2 class="w-4 h-4 animate-spin text-[var(--accent)]" />
        <span class="text-xs">Memuat...</span>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" @click.self="closeModal">
      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-2xl shadow-2xl shadow-black/60 w-full max-w-md">
        <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h3 class="text-lg font-bold text-[var(--text-primary)]">{{ editingType ? 'Edit Tipe Kendaraan' : 'Tambah Tipe Kendaraan' }}</h3>
          <button @click="closeModal" class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSave" class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Nama Tipe</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="misal: Mobil, Motor, Truk"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
              required
            />
          </div>

          <div v-if="error" class="flex items-start gap-2 bg-[var(--status-fail)]/10 border border-[var(--status-fail)]/30 rounded-lg px-3 py-2">
            <AlertTriangle class="w-4 h-4 text-[var(--status-fail)] mt-0.5 shrink-0" />
            <p class="text-xs text-[var(--status-fail)]">{{ error }}</p>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="closeModal" class="px-4 py-2 text-sm rounded-lg border border-[var(--border)] bg-[var(--bg-panel-alt)] text-[var(--text-primary)] hover:bg-[var(--border)] transition">
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
              <Check v-else class="w-4 h-4" />
              {{ saving ? 'Menyimpan...' : editingType ? 'Simpan Perubahan' : 'Tambah Tipe' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>