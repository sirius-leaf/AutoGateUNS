<script setup>
import { ref, onMounted } from 'vue'
import { Car, Search, Loader2, ChevronLeft, ChevronRight, Pencil, X, Check, AlertTriangle } from '@lucide/vue'
import api from '@/services/api'

const vehicles = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(0)
const limit = 50
const searchQ = ref('')

const showModal = ref(false)
const editingVehicle = ref(null)
const saving = ref(false)
const error = ref('')
const vehicleTypes = ref([])

const form = ref({
  vehicle_type: '',
  cc: null,
  engine_type: '',
  owner_name: '',
  owner_address: '',
  owner_phone: '',
})

const fetchVehicles = async () => {
  loading.value = true
  try {
    const data = await api.getVehicles({ q: searchQ.value, skip: page.value * limit, limit })
    vehicles.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const fetchVehicleTypes = async () => {
  try {
    const data = await api.getVehicleTypes()
    vehicleTypes.value = data.items || []
  } catch {
    vehicleTypes.value = []
  }
}

const handleSearch = () => {
  page.value = 0
  fetchVehicles()
}

const nextPage = () => {
  if ((page.value + 1) * limit < total.value) {
    page.value++
    fetchVehicles()
  }
}

const prevPage = () => {
  if (page.value > 0) {
    page.value--
    fetchVehicles()
  }
}

const openEdit = (v) => {
  editingVehicle.value = v
  form.value = {
    vehicle_type: v.vehicle_type || '',
    cc: v.cc ?? null,
    engine_type: v.engine_type || '',
    owner_name: v.owner_name || '',
    owner_address: v.owner_address || '',
    owner_phone: v.owner_phone || '',
  }
  error.value = ''
  showModal.value = true
  fetchVehicleTypes()
}

const closeModal = () => {
  showModal.value = false
  editingVehicle.value = null
  error.value = ''
}

const handleSave = async () => {
  saving.value = true
  error.value = ''
  try {
    const payload = {}
    if (form.value.vehicle_type !== (editingVehicle.value.vehicle_type || '')) {
      payload.vehicle_type = form.value.vehicle_type || null
    }
    if (form.value.cc !== (editingVehicle.value.cc ?? null)) {
      payload.cc = form.value.cc
    }
    if (form.value.engine_type !== (editingVehicle.value.engine_type || '')) {
      payload.engine_type = form.value.engine_type || null
    }
    if (form.value.owner_name !== (editingVehicle.value.owner_name || '')) {
      payload.owner_name = form.value.owner_name
    }
    if (form.value.owner_address !== (editingVehicle.value.owner_address || '')) {
      payload.owner_address = form.value.owner_address
    }
    if (form.value.owner_phone !== (editingVehicle.value.owner_phone || '')) {
      payload.owner_phone = form.value.owner_phone
    }
    if (Object.keys(payload).length === 0) {
      closeModal()
      return
    }
    await api.updateVehicle(editingVehicle.value.id, payload)
    closeModal()
    await fetchVehicles()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

const formatTime = (iso) => {
  if (!iso) return '---'
  return new Date(iso).toLocaleString('id-ID')
}

onMounted(fetchVehicles)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Car class="w-5 h-5 text-[var(--text-muted)]" />
          Kendaraan
        </h2>
        <p class="text-xs text-[var(--text-muted)] mt-1">Daftar kendaraan yang tercatat dari semua node</p>
      </div>
      <span class="text-xs text-[var(--text-muted)] bg-[var(--bg-panel-alt)] border border-[var(--border)] px-2.5 py-1 rounded-full">{{ total }} kendaraan</span>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <div class="flex gap-2 max-w-sm">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            v-model="searchQ"
            type="text"
            placeholder="Cari plat nomor..."
            @keyup.enter="handleSearch"
            class="w-full bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] font-mono"
          />
        </div>
        <button @click="handleSearch" class="px-4 py-2 bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] text-sm rounded-lg transition border border-[var(--border)]">
          Cari
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-xl shadow-black/40 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[var(--border)]">
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium w-16">ID</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Plat Nomor</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Pemilik</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Tipe</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Tipe Mesin</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">CC</th>
              <th class="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Terdaftar</th>
              <th class="text-right py-3 px-4 text-[var(--text-muted)] font-medium">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="v in vehicles"
              :key="v.id"
              class="border-b border-[var(--border)]/50 hover:bg-[var(--bg-panel-alt)] transition-colors"
            >
              <td class="py-3 px-4 text-[var(--text-muted)] font-mono">{{ v.id }}</td>
              <td class="py-3 px-4 font-mono font-bold text-[var(--text-primary)]">{{ v.plate_number }}</td>
              <td class="py-3 px-4 text-[var(--text-primary)]">{{ v.owner_name || '---' }}</td>
              <td class="py-3 px-4 text-[var(--text-muted)]">{{ v.vehicle_type || '---' }}</td>
              <td class="py-3 px-4 text-[var(--text-muted)] capitalize">{{ v.engine_type || '---' }}</td>
              <td class="py-3 px-4 text-[var(--text-muted)]">{{ v.cc ? `${v.cc} cc` : '---' }}</td>
              <td class="py-3 px-4 text-[var(--text-muted)] whitespace-nowrap">{{ formatTime(v.created_at) }}</td>
              <td class="py-3 px-4 text-right">
                <button @click="openEdit(v)" class="p-1.5 rounded text-[var(--text-muted)] hover:text-blue-400 hover:bg-blue-500/10 transition" title="Edit kendaraan">
                  <Pencil class="w-3.5 h-3.5" />
                </button>
              </td>
            </tr>
            <tr v-if="!vehicles.length && !loading">
              <td colspan="8" class="py-12">
                <div class="flex flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                  <Car class="w-8 h-8 opacity-30" />
                  <span class="text-sm">Belum ada kendaraan tercatat</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-4 gap-2 text-[var(--text-muted)]">
        <Loader2 class="w-4 h-4 animate-spin text-[var(--accent)]" />
        <span class="text-xs">Memuat...</span>
      </div>

      <!-- Pagination -->
      <div v-if="total > limit" class="flex items-center justify-between px-4 py-3 border-t border-[var(--border)]">
        <span class="text-xs text-[var(--text-muted)]">
          {{ page * limit + 1 }}–{{ Math.min((page + 1) * limit, total) }} dari {{ total }}
        </span>
        <div class="flex gap-1">
          <button
            @click="prevPage"
            :disabled="page === 0"
            class="p-1.5 rounded bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] disabled:opacity-30 transition border border-[var(--border)]"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
            @click="nextPage"
            :disabled="(page + 1) * limit >= total"
            class="p-1.5 rounded bg-[var(--bg-panel-alt)] hover:bg-[var(--border)] text-[var(--text-primary)] disabled:opacity-30 transition border border-[var(--border)]"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Edit -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" @click.self="closeModal">
      <div class="bg-[var(--bg-panel)] border border-[var(--border)] rounded-2xl shadow-2xl shadow-black/60 w-full max-w-md">
        <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h3 class="text-lg font-bold text-[var(--text-primary)]">Edit Kendaraan</h3>
          <button @click="closeModal" class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-panel-alt)] transition">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSave" class="p-6 space-y-4">
          <!-- Plat Nomor (read-only) -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Plat Nomor</label>
            <div class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-muted)] font-mono">
              {{ editingVehicle?.plate_number }}
            </div>
          </div>

          <!-- Tipe Kendaraan (dropdown) -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Tipe Kendaraan</label>
            <select
              v-model="form.vehicle_type"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
            >
              <option value="">-- Pilih tipe --</option>
              <option
                v-for="t in vehicleTypes"
                :key="t.id"
                :value="t.name"
              >
                {{ t.name }}
              </option>
            </select>
            <p class="text-[10px] text-[var(--text-muted)] mt-1">Tipe diambil dari master data Tipe Kendaraan</p>
          </div>

          <!-- Tipe Mesin (dropdown) -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Tipe Mesin</label>
            <select
              v-model="form.engine_type"
              class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
            >
              <option value="">-- Pilih tipe mesin --</option>
              <option value="disel">Disel</option>
              <option value="bensin">Bensin</option>
              <option value="listrik">Listrik</option>
            </select>
          </div>

          <!-- CC -->
          <div>
            <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">CC</label>
            <div class="relative">
              <input
                v-model.number="form.cc"
                type="number"
                min="0"
                max="9999"
                placeholder="misal: 1500"
                class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 pr-10 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
              />
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-[var(--text-muted)]">cc</span>
            </div>
          </div>

          <div class="border-t border-[var(--border)] my-2 pt-3">
             <h4 class="text-sm font-bold text-[var(--text-primary)] mb-3 flex items-center gap-2">
               <span class="w-1 h-3.5 rounded-full bg-[var(--accent)]"></span>
               Data Pemilik
             </h4>

             <div class="space-y-3">
               <div>
                 <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Nama Pemilik</label>
                 <input v-model="form.owner_name" type="text" class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]" />
               </div>
               <div>
                 <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Alamat</label>
                 <input v-model="form.owner_address" type="text" class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]" />
               </div>
               <div>
                 <label class="block text-xs font-medium text-[var(--text-muted)] mb-1">Telepon</label>
                 <input v-model="form.owner_phone" type="text" class="w-full bg-[var(--bg-panel-alt)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]" />
               </div>
             </div>
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
              Simpan
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>