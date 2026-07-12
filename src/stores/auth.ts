import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiFetch } from '@/lib/api'

type Role = 'student' | 'teacher' | 'admin'

interface RegisterPayload {
  username?: string | null
  email?: string | null
  password: string
  role: Exclude<Role, 'admin'>
}

export interface LoginPayload {
  username?: string | null
  email?: string | null
  password: string
}

interface AccountResponse {
  id: number
  username: string | null
  email: string | null
  role: Role
  created_at: string
  updated_at: string
}

interface TokenResponse {
  access_token: string
  token_type: string
  profile_completed: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token'))
  const tokenType = ref(localStorage.getItem('token_type') ?? 'bearer')
  const role = ref<Role | null>((localStorage.getItem('role') as Role | null) ?? null)
  const accountIdentity = ref(localStorage.getItem('account_identity') ?? '')
  const profileCompleted = ref(localStorage.getItem('profile_completed') === 'true')
  const loading = ref(false)
  const error = ref('')
  const otpVerified = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value))
  const authorizationHeader = computed(() =>
    token.value ? `${tokenType.value} ${token.value}` : ''
  )

  async function requestTeacherOtp(email: string) {
    loading.value = true
    error.value = ''

    try {
      const data = await apiFetch<{ message: string }>('/otp/teacher/request', {
        method: 'POST',
        body: JSON.stringify({ email, role: 'teacher' }),
      })
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to send OTP'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function verifyTeacherOtp(email: string, otp: string) {
    loading.value = true
    error.value = ''

    try {
      const data = await apiFetch<{ message: string }>('/otp/teacher/verify', {
        method: 'POST',
        body: JSON.stringify({ email, otp, role: 'teacher' }),
      })
      otpVerified.value = true
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'OTP verification failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    error.value = ''

    try {
      const account = await apiFetch<AccountResponse>('/auth/account/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      localStorage.setItem('selectedRole', payload.role)
      return account
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Registration failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function login(payload: LoginPayload, selectedRole: Role) {
    loading.value = true
    error.value = ''

    try {
      const data = await apiFetch<TokenResponse>('/auth/account/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      token.value = data.access_token
      tokenType.value = data.token_type
      role.value = selectedRole
      accountIdentity.value = selectedRole === 'student' ? payload.username ?? '' : payload.email ?? ''
      const isCompleted = selectedRole === 'admin' ? true : data.profile_completed
      profileCompleted.value = isCompleted

      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('token_type', data.token_type)
      localStorage.setItem('role', selectedRole)
      localStorage.setItem('selectedRole', selectedRole)
      localStorage.setItem('account_identity', accountIdentity.value)
      localStorage.setItem('profile_completed', String(isCompleted))

      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    tokenType.value = 'bearer'
    role.value = null
    accountIdentity.value = ''
    profileCompleted.value = false
    otpVerified.value = false
    localStorage.removeItem('access_token')
    localStorage.removeItem('token_type')
    localStorage.removeItem('role')
    localStorage.removeItem('selectedRole')
    localStorage.removeItem('account_identity')
    localStorage.removeItem('profile_completed')
    localStorage.removeItem('profile_data')
    localStorage.removeItem('profile_image')
    localStorage.removeItem('teacher_pending_email')
    localStorage.removeItem('teacher_otp_expires_at')
    localStorage.removeItem('teacher_verified_email')
    localStorage.removeItem('teacher_register_step')
  }

  function setProfileCompleted(completed: boolean) {
    profileCompleted.value = completed
    localStorage.setItem('profile_completed', String(completed))
  }

  return {
    token,
    tokenType,
    role,
    accountIdentity,
    profileCompleted,
    loading,
    error,
    otpVerified,
    isAuthenticated,
    authorizationHeader,
    requestTeacherOtp,
    verifyTeacherOtp,
    register,
    login,
    logout,
    setProfileCompleted,
  }
})

