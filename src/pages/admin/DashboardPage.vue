<template>
  <div class="space-y-6">
    <!-- Hero Banner -->
    <div class="relative gradient-brand rounded-2xl p-8 flex items-center justify-between overflow-hidden shadow-sm">
      <div class="absolute inset-0 opacity-5" style="background-image:radial-gradient(circle,#fff 1px,transparent 1px);background-size:28px 28px;" />
      <div class="relative z-10">
        <h1 class="font-display text-3xl font-bold text-white leading-tight mb-2">Welcome Back, Admin! 🛡️</h1>
        <p class="text-white/75 text-sm max-w-md leading-relaxed">
          Manage teacher registrations, verify qualifications, and maintain system security from your command center.
        </p>
      </div>
      <div class="text-6xl relative z-10" style="animation: float 4s ease-in-out infinite;">⚙️</div>
    </div>

    <!-- Info Banner / Alert Panel -->
    <div v-if="successMsg" class="status-success flex items-center justify-between px-4 py-3 shadow-sm border border-emerald-200">
      <span>{{ successMsg }}</span>
      <button @click="successMsg = ''" class="text-emerald-700 hover:text-emerald-900 font-bold ml-2">×</button>
    </div>
    <div v-if="errorMsg" class="status-error flex items-center justify-between px-4 py-3 shadow-sm border border-red-200">
      <span>{{ errorMsg }}</span>
      <button @click="errorMsg = ''" class="text-rose-700 hover:text-rose-900 font-bold ml-2">×</button>
    </div>

    <!-- Stat Summary -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="card p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-yellow" />
        <div class="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-lg mb-3">⏳</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">{{ pendingAccounts.length }}</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Pending Teacher Accounts</div>
      </div>
      <div class="card p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-green" />
        <div class="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-lg mb-3">✅</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">{{ actionCounts.approved }}</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Approved This Session</div>
      </div>
      <div class="card p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-rose" />
        <div class="w-10 h-10 rounded-xl bg-rose-100 flex items-center justify-center text-lg mb-3">🚫</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">{{ actionCounts.blocked }}</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Blocked This Session</div>
      </div>
    </div>

    <!-- Main Content Panel -->
    <div class="card">
      <div class="px-5 py-4 border-b border-gray-50 flex items-center justify-between bg-white">
        <span class="font-display font-semibold text-base text-ink">Pending Verification Requests</span>
        <button @click="loadPendingAccounts" :disabled="loading" class="text-xs font-semibold text-brand-blue bg-brand-blue-soft px-3.5 py-2 rounded-full hover:bg-brand-blue hover:text-white transition-all disabled:opacity-50">
          {{ loading ? 'Refreshing...' : 'Refresh List' }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="p-12 text-center text-ink-soft font-medium">
        <div class="inline-block w-8 h-8 border-4 border-brand-blue border-t-transparent rounded-full animate-spin mb-3"></div>
        <p class="text-sm">Fetching pending registrations...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="pendingAccounts.length === 0" class="p-12 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h3 class="text-lg font-bold text-ink mb-1">All Caught Up!</h3>
        <p class="text-sm text-ink-soft max-w-sm mx-auto">There are no teacher accounts currently waiting for administrative review.</p>
      </div>

      <!-- Data Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr>
              <th class="table-th">Account Details</th>
              <th class="table-th">Role</th>
              <th class="table-th">Joined Date</th>
              <th class="table-th">Verification Status</th>
              <th class="table-th text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="teacher in pendingAccounts" :key="teacher.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="table-td">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-gradient-to-br from-brand-yellow to-brand-amber flex items-center justify-center text-white font-bold text-sm">
                    {{ teacher.email?.charAt(0).toUpperCase() ?? 'T' }}
                  </div>
                  <div>
                    <div class="text-[13px] font-semibold text-ink">{{ teacher.email }}</div>
                    <div class="text-[10px] text-ink-soft font-mono">ID: {{ teacher.id }}</div>
                  </div>
                </div>
              </td>
              <td class="table-td">
                <span class="badge badge-amber">Teacher</span>
              </td>
              <td class="table-td font-mono text-xs text-ink-soft">
                {{ formatDate(teacher.created_at) }}
              </td>
              <td class="table-td">
                <span class="badge bg-amber-100 text-amber-700 animate-pulse">Pending Review</span>
              </td>
              <td class="table-td text-right">
                <div v-if="confirmingId === teacher.id" class="inline-flex items-center gap-2">
                  <span class="text-xs font-semibold text-ink-soft mr-1">
                    Confirm {{ confirmingAction === 'approve' ? 'verify' : 'block' }}?
                  </span>
                  <button
                    @click="confirmAction"
                    :disabled="submittingId === teacher.id"
                    class="px-3.5 py-1.5 text-xs font-bold text-white bg-brand-green rounded-lg hover:bg-emerald-600 active:scale-95 transition-all disabled:opacity-60"
                  >
                    Yes
                  </button>
                  <button
                    @click="cancelConfirmation"
                    :disabled="submittingId === teacher.id"
                    class="px-3.5 py-1.5 text-xs font-bold text-ink bg-surface-2 rounded-lg hover:bg-gray-300 active:scale-95 transition-all disabled:opacity-60"
                  >
                    No
                  </button>
                </div>
                <div v-else class="inline-flex gap-2">
                  <button 
                    @click="initiateAction(teacher.id, 'approve')" 
                    :disabled="submittingId !== null"
                    class="px-4 py-2 text-xs font-bold text-white bg-brand-green rounded-lg hover:bg-emerald-600 active:scale-95 transition-all disabled:opacity-60"
                  >
                    Verify
                  </button>
                  <button 
                    @click="initiateAction(teacher.id, 'block')" 
                    :disabled="submittingId !== null"
                    class="px-4 py-2 text-xs font-bold text-white bg-brand-rose rounded-lg hover:bg-rose-600 active:scale-95 transition-all disabled:opacity-60"
                  >
                    Block
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch, ApiError } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface PendingTeacher {
  id: number
  email: string
  role: string
  verification_status: string
  created_at: string
}

const auth = useAuthStore()

const pendingAccounts = ref<PendingTeacher[]>([])
const loading = ref(false)
const submittingId = ref<number | null>(null)
const successMsg = ref('')
const errorMsg = ref('')

const confirmingId = ref<number | null>(null)
const confirmingAction = ref<'approve' | 'block' | null>(null)

const actionCounts = ref({
  approved: 0,
  blocked: 0,
})

function initiateAction(teacherId: number, action: 'approve' | 'block') {
  confirmingId.value = teacherId
  confirmingAction.value = action
}

function cancelConfirmation() {
  confirmingId.value = null
  confirmingAction.value = null
}

async function confirmAction() {
  if (confirmingId.value === null || confirmingAction.value === null) return
  const id = confirmingId.value
  const act = confirmingAction.value
  cancelConfirmation()
  if (act === 'approve') {
    await approveAccount(id)
  } else if (act === 'block') {
    await blockAccount(id)
  }
}

async function loadPendingAccounts() {
  confirmingId.value = null
  confirmingAction.value = null
  loading.value = true
  errorMsg.value = ''
  try {
    const data = await apiFetch<PendingTeacher[]>('/admin/teachers/pendings', {
      token: auth.token,
    })
    pendingAccounts.value = data
  } catch (err) {
    errorMsg.value = err instanceof ApiError ? err.message : 'Failed to fetch pending teacher accounts.'
  } finally {
    loading.value = false
  }
}

async function approveAccount(teacherId: number) {
  submittingId.value = teacherId
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await apiFetch<{ message: string }>(`/admin/teachers/${teacherId}/approve`, {
      method: 'PATCH',
      token: auth.token,
    })
    successMsg.value = res.message || 'Teacher verified successfully!'
    actionCounts.value.approved++
    // Remove from the list immediately
    pendingAccounts.value = pendingAccounts.value.filter(a => a.id !== teacherId)
  } catch (err) {
    errorMsg.value = err instanceof ApiError ? err.message : 'Failed to verify account.'
  } finally {
    submittingId.value = null
  }
}

async function blockAccount(teacherId: number) {
  submittingId.value = teacherId
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await apiFetch<{ message: string }>(`/admin/teachers/${teacherId}/block`, {
      method: 'PATCH',
      token: auth.token,
    })
    successMsg.value = res.message || 'Teacher blocked successfully!'
    actionCounts.value.blocked++
    // Remove from the list immediately
    pendingAccounts.value = pendingAccounts.value.filter(a => a.id !== teacherId)
  } catch (err) {
    errorMsg.value = err instanceof ApiError ? err.message : 'Failed to block account.'
  } finally {
    submittingId.value = null
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadPendingAccounts()
})
</script>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(-3deg); }
  50% { transform: translateY(-10px) rotate(3deg); }
}
</style>
