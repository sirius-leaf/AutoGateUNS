<script setup>
import { ref, onMounted } from 'vue'
import { Radio, Plus, Pencil, Trash2, X, Loader2, AlertTriangle, Check, Copy, Eye, EyeOff } from '@lucide/vue'
import api from '@/services/api'

const nodes = ref([])
const loading = ref(false)
const showModal = ref(false)
const editingNode = ref(null)
const saving = ref(false)
const error = ref('')
const showApiKey = ref({})
const copiedKey = ref(null)

const form = ref({
  name: '',
  location: '',
})

const fetchNodes = async () => {
  loading.value = true
  try {
    const data = await api.getNodes()
    nodes.value = data.items || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingNode.value = null
  form.value = { name: '', location: '' }
  error.value = ''
  showModal.value = true
}

const openEdit = (node) => {
  editingNode.value = node
  form.value = { name: node.name, location: node.location || '' }
  error.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingNode.value = null
  error.value = ''
}

const handleSave = async () => {
  saving.value = true
  error.value = ''
  try {
    if (editingNode.value) {
      await api.updateNode(editingNode.value.id, form.value)
    } else {
      await api.createNode(form.value)
    }
    closeModal()
    await fetchNodes()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

const handleDelete = async (node) => {
  if (!confirm(`Hapus node '${node.name}'?`)) return
  try {
    await api.deleteNode(node.id)
    await fetchNodes()
  } catch (err) {
    alert(err.message)
  }
}

const copyApiKey = (nodeId, apiKey) => {
  navigator.clipboard.writeText(apiKey)
  copiedKey.value = nodeId
  setTimeout(() => { copiedKey.value = null }, 2000)
}

const toggleApiKey = (nodeId) => {
  showApiKey.value[nodeId] = !showApiKey.value[nodeId]
}

const maskKey = (key) => {
  if (!key) return ''
  return key.substring(0, 8) + '...' + key.substring(key.length - 4)
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

onMounted(fetchNodes)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Radio class="w-5 h-5 text-[var(--text-muted)]" />
          Kelola Node
        </h2>
        <p class="text-xs text-[var(--text-muted)] mt-1">Manajemen pos satpam dan API key</p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg text-sm transition"
      >
        <Plus class="w-4 h-4" />
        Tambah Node
      </button>
    </div>

    <!-- Table -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-xl shadow-black/40 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Nama</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">ID</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">API Key</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Lokasi</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Status</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Terakhir</th>
              <th class="text-right py-3 px-4 text-[var(--text-muted)] font-medium">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="n in nodes"
              :key="n.id"
              class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] transition-colors"
            >
              <td class="py-3 px-4 font-medium text-[var(--text-primary)]">{{ n.name }}</td>
              <td class="py-3 px-4 font-mono text-[var(--text-muted)] text-[10px]">{{ n.id.substring(0, 8) }}...</td>
              <td class="py-3 px-4">
                <div class="flex items-center gap-1">
                  <code class="text-[10px] text-[var(--text-muted)] font-mono">
                    {{ showApiKey[n.id] ? n.api_key : maskKey(n.api_key) }}
                  </code>
                  <button @click="toggleApiKey(n.id)" class="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition">
                    <Eye v-if="!showApiKey[n.id]" class="w-3 h-3" />
                    <EyeOff v-else class="w-3 h-3" />
                  </button>
                  <button
                    @click="copyApiKey(n.id, n.api_key)"
                    class="p-1 transition"
                    :class="copiedKey === n.id ? 'text-[var(--status-ok)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'"
                    title="Copy API Key"
                  >
                    <Check v-if="copiedKey === n.id" class="w-3 h-3" />
                    <Copy v-else class="w-3 h-3" />
                  </button>
                </div>
              </td>
              <td class="py-3 px-4 text-[var(--text-muted)]">{{ n.location || '---' }}</td>
              <td class="py-3 px-4">
                <div class="flex items-center gap-1.5">
                  <span class="relative flex w-2 h-2">
                    <span
                      v-if="n.status === 'online'"
                      class="absolute inline-flex w-full h-full rounded-full bg-[var(--status-ok)] opacity-60 animate-ping"
                    ></span>
                    <span
                      :class="[
                        'relative inline-flex w-2 h-2 rounded-full',
                        n.status === 'online' ? 'bg-[var(--status-ok)]' : 'bg-[var(--status-fail)]',
                      ]"
                    ></span>
                  </span>
                  <span class="text-[var(--text-primary)]">{{ n.status }}</span>
                </div>
              </td>
              <td class="py-3 px-4 text-[var(--text-muted)] font-mono text-[10px]">{{ formatTime(n.last_seen_at) }}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button @click="openEdit(n)" class="p-1.5 rounded text-[var(--text-muted)] hover:text-blue-400 hover:bg-blue-500/10 transition" title="Edit">
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button @click="handleDelete(n)" class="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--status-fail)] hover:bg-[var(--status-fail)]/10 transition" title="Hapus">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!nodes.length && !loading">
              <td colspan="7" class="py-12">
                <div class="flex flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                  <Radio class="w-8 h-8 opacity-30" />
                  <span class="text-sm">Belum ada node</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" @click.self="closeModal">
      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-2xl shadow-2xl shadow-black/60 w-full max-w-md">
        <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h3 class="text-lg font-bold text-[var(--text-primary)]">{{ editingNode ? 'Edit Node' : 'Tambah Node' }}</h3>
          <button @click="closeModal" class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSave" class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Nama Node</label>
            <input v-model="form.name" type="text" placeholder="Contoh: Gerbang Depan" class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]" />
          </div>
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Lokasi (opsional)</label>
            <input v-model="form.location" type="text" placeholder="Contoh: Depan Fakultas MIPA" class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]" />
          </div>

          <div v-if="!editingNode" class="bg-[var(--status-info)]/10 border border-[var(--status-info)]/30 rounded-lg px-3 py-2">
            <p class="text-xs text-[var(--status-info)]">UUID dan API key akan di-generate otomatis oleh server.</p>
          </div>

          <div v-if="error" class="flex items-start gap-2 bg-[var(--status-fail)]/10 border border-[var(--status-fail)]/30 rounded-lg px-3 py-2">
            <AlertTriangle class="w-4 h-4 text-[var(--status-fail)] mt-0.5 shrink-0" />
            <p class="text-xs text-[var(--status-fail)]">{{ error }}</p>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="closeModal" class="px-4 py-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-sm font-medium rounded-lg transition border border-[var(--border)]">Batal</button>
            <button type="submit" :disabled="saving" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition disabled:opacity-50">
              <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
              <Check v-else class="w-4 h-4" />
              {{ editingNode ? 'Simpan' : 'Buat' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>