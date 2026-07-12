<template>
  <main class="min-h-screen bg-[#f0f2f8] flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-md bg-white rounded-[24px] shadow-[0_8px_40px_rgba(15,23,42,0.10)] p-8">

      <!-- Back link -->
      <RouterLink to="/portal" class="inline-flex items-center gap-1.5 text-sm font-bold text-brand-blue hover:text-blue-700 transition-colors mb-6">
        ← Back
      </RouterLink>

      <!-- Role badge -->
      <p class="text-[11px] font-black uppercase tracking-[0.22em] mb-1" :class="role === 'teacher' ? 'text-amber-600' : 'text-brand-blue'">
        {{ roleLabel }}
      </p>

      <!-- Title -->
      <h1 class="font-display text-[2rem] font-bold text-ink leading-tight mb-6">
        {{ roleLabel }} Login
      </h1>

      <form class="grid gap-4" @submit.prevent="submitLogin">

        <div>
          <label class="field-label" :for="role === 'teacher' ? 'email' : 'account'">
            {{ role === 'teacher' ? 'Email' : 'Student ID or email' }}
          </label>
          <input
            :id="role === 'teacher' ? 'email' : 'account'"
            v-model.trim="accountIdentityInput"
            class="input-field mt-2"
            :type="role === 'teacher' ? 'email' : 'text'"
            :autocomplete="role === 'teacher' ? 'email' : 'username'"
            :placeholder="role === 'teacher' ? 'teacher@school.edu' : 'Enter student ID or email'"
            minlength="3" maxlength="60" required
          />
        </div>

        <div>
          <label class="field-label" for="password">Password</label>
          <div class="mt-2 grid grid-cols-[1fr_auto] gap-2">
            <input id="password" v-model="password" class="input-field"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password" minlength="8" maxlength="30" required />
            <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <div class="flex justify-end text-sm">
          <button type="button" class="font-semibold text-brand-blue hover:text-blue-700 transition-colors" @click="handleForgotPassword">
            Forgot Password
          </button>
        </div>

        <div v-if="isPendingApproval" class="status-warning" role="status">
          <p class="font-bold">⏳ Account Pending Approval</p>
          <p class="mt-1 text-xs font-normal opacity-80">Your account is waiting for admin verification.</p>
        </div>

        <div v-else-if="isBlocked" class="status-error" role="alert">
          <p class="font-bold">🚫 Account Blocked</p>
          <p class="mt-1 text-xs font-normal opacity-80">Please contact support if you believe this is a mistake.</p>
        </div>

        <p v-else-if="auth.error" class="status-error" role="alert">{{ auth.error }}</p>
        <p v-else-if="recoveryMessage" class="status-warning" role="status">{{ recoveryMessage }}</p>

        <button type="submit" class="btn-primary w-full justify-center rounded-xl py-3 mt-1 text-sm font-bold" :disabled="auth.loading">
          {{ auth.loading ? 'Signing in...' : 'Login' }}
        </button>
      </form>

      <p class="mt-6 text-sm text-ink-soft">
        Need an account?
        <RouterLink :to="`/register?role=${role}`" class="font-bold text-brand-blue hover:text-blue-700 transition-colors">Create one</RouterLink>
      </p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/lib/api'

type Role = 'student' | 'teacher'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const role = ref<Role>(route.query.role === 'teacher' ? 'teacher' : 'student')
const accountIdentityInput = ref('')
const password = ref('')
const showPassword = ref(false)
const isPendingApproval = ref(false)
const isBlocked = ref(false)
const recoveryMessage = ref('')

const roleLabel = computed(() => role.value === 'teacher' ? 'Teacher' : 'Student')

function handleForgotPassword() {
  recoveryMessage.value = 'Please contact your school administrator or support team to reset your password.'
  auth.error = ''
}

async function submitLogin() {
  isPendingApproval.value = false
  isBlocked.value = false
  auth.error = ''
  recoveryMessage.value = ''

  try {
    const data = await auth.login({
      email: role.value === 'teacher' ? accountIdentityInput.value : null,
      username: role.value === 'student' ? accountIdentityInput.value : null,
      password: password.value,
    }, role.value)

    if (!data.profile_completed) {
      router.push('/profile/setup')
      return
    }

    router.push(role.value === 'teacher' ? '/teacher/class' : '/student/dashboard')
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) {
      if (err.message.toLowerCase().includes('admin approval') || err.message.toLowerCase().includes('wait for admin')) {
        isPendingApproval.value = true
        auth.error = ''
        return
      }
      if (err.message.toLowerCase().includes('blocked')) {
        isBlocked.value = true
        auth.error = ''
        return
      }
    }
  }
}
</script>
