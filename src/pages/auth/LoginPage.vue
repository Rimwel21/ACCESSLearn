<template>
  <main class="auth-page">
    <section class="auth-card">
      <RouterLink to="/" class="auth-back">Back home</RouterLink>
      <p class="eyebrow">{{ role }}</p>
      <h1 class="auth-title">{{ roleLabel }} Login</h1>

      <form class="form-stack" @submit.prevent="submitLogin">
        <template v-if="role === 'teacher' || role === 'admin'">
          <label class="field-label" for="email">Email</label>
          <input id="email" v-model.trim="email" class="input-field" type="email" autocomplete="email" minlength="5" maxlength="50" required />
        </template>

        <template v-else>
          <label class="field-label" for="username">Username</label>
          <input id="username" v-model.trim="username" class="input-field" type="text" autocomplete="username" minlength="5" maxlength="50" required />
        </template>

        <label class="field-label" for="password">Password</label>
        <div class="grid grid-cols-[1fr_auto] gap-2">
          <input id="password" v-model="password" class="input-field" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" minlength="8" maxlength="30" required />
          <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>

        <!-- Pending admin approval (amber warning) -->
        <div v-if="isPendingApproval" class="status-warning" role="status">
          <p class="font-bold">⏳ Account Pending Approval</p>
          <p class="mt-1 text-xs font-normal opacity-80">Your account is waiting for admin verification. You'll be able to login once an administrator approves your account.</p>
        </div>

        <!-- Blocked account (red error) -->
        <div v-else-if="isBlocked" class="status-error" role="alert">
          <p class="font-bold">🚫 Account Blocked</p>
          <p class="mt-1 text-xs font-normal opacity-80">Your account has been blocked by the system administrator. Please contact support if you believe this is a mistake.</p>
        </div>

        <!-- Generic errors -->
        <p v-else-if="auth.error" class="status-error" role="alert">{{ auth.error }}</p>

        <button type="submit" class="btn-primary w-full justify-center rounded-lg" :disabled="auth.loading">
          {{ auth.loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <p v-if="role !== 'admin'" class="mt-5 text-sm text-ink-soft">
        Need an account?
        <RouterLink :to="`/register?role=${role}`" class="font-bold text-brand-blue">Create one</RouterLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/lib/api'

type Role = 'student' | 'teacher' | 'admin'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const requestedRole = route.query.role === 'student' ? 'student' : (route.query.role === 'admin' ? 'admin' : 'teacher')
const role = ref<Role>(requestedRole)
const email = ref('')
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isPendingApproval = ref(false)
const isBlocked = ref(false)

const roleLabel = computed(() => {
  if (role.value === 'student') return 'Student'
  if (role.value === 'admin') return 'Admin'
  return 'Teacher'
})

async function submitLogin() {
  const isEmailAuth = role.value === 'teacher' || role.value === 'admin'

  // Reset status flags on each attempt
  isPendingApproval.value = false
  isBlocked.value = false
  auth.error = ''

  try {
    const data = await auth.login({
      email: isEmailAuth ? email.value : null,
      username: isEmailAuth ? null : username.value,
      password: password.value,
    }, role.value)

    if (role.value === 'admin') {
      router.push('/admin/dashboard')
      return
    }

    if (!data.profile_completed) {
      router.push('/profile/setup')
      return
    }

    router.push(role.value === 'teacher' ? '/teacher/class' : '/student/dashboard')
  } catch (err) {
    // Detect specific 403 statuses from the backend
    if (err instanceof ApiError && err.status === 403) {
      if (err.message.toLowerCase().includes('admin approval') || err.message.toLowerCase().includes('wait for admin')) {
        isPendingApproval.value = true
        auth.error = '' // Clear generic error so only the warning banner shows
        return
      }
      if (err.message.toLowerCase().includes('blocked')) {
        isBlocked.value = true
        auth.error = '' // Clear generic error so only the blocked banner shows
        return
      }
    }
    // For other errors, the auth store owns the visible error message.
  }
}
</script>
