<template>
  <main class="auth-page">
    <section class="auth-card">
      <RouterLink to="/" class="auth-back">Back home</RouterLink>
      <p class="eyebrow">{{ role }}</p>
      <h1 class="auth-title">{{ roleLabel }} Register</h1>

      <!-- ─── Student Registration (single step, unchanged) ─── -->
      <template v-if="role === 'student'">
        <form class="form-stack" @submit.prevent="submitStudentRegister">
          <label class="field-label" for="username">Username</label>
          <input id="username" v-model.trim="username" class="input-field" type="text" autocomplete="username" minlength="5" maxlength="50" required />

          <label class="field-label" for="password">Password</label>
          <div class="grid grid-cols-[1fr_auto] gap-2">
            <input id="password" v-model="password" class="input-field" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" maxlength="30" required />
            <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>

          <p v-if="message" class="status-success" role="status">{{ message }}</p>
          <p v-if="validationError" class="status-error" role="alert">{{ validationError }}</p>
          <p v-if="auth.error" class="status-error" role="alert">{{ auth.error }}</p>

          <button type="submit" class="btn-primary w-full justify-center rounded-lg" :disabled="auth.loading">
            {{ auth.loading ? 'Registering...' : 'Create account' }}
          </button>
        </form>
      </template>

      <!-- ─── Teacher Registration (3-step OTP Wizard) ─── -->
      <template v-else>
        <!-- Step indicators (Design preserved, made interactive) -->
        <div class="mb-6 flex items-center gap-2">
          <div v-for="s in 3" :key="s" class="flex items-center gap-2">
            <button
              type="button"
              @click="goToStep(s)"
              :disabled="!isStepSelectable(s)"
              :class="[
                'inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all border-0 outline-none p-0',
                step >= s
                  ? 'bg-brand-blue text-white shadow-sm'
                  : 'bg-surface-2 text-ink-soft',
                isStepSelectable(s) ? 'cursor-pointer hover:bg-brand-blue/95 hover:text-white' : 'cursor-not-allowed'
              ]"
            >{{ s }}</button>
            <span
              v-if="s < 3"
              :class="[
                'h-0.5 w-6 rounded-full transition-all',
                step > s ? 'bg-brand-blue' : 'bg-surface-2',
              ]"
            />
          </div>
          <span class="ml-2 text-xs font-semibold text-ink-soft">{{ stepLabel }}</span>
        </div>

        <!-- Step 1: Request OTP -->
        <form v-if="step === 1" class="form-stack" @submit.prevent="handleRequestOtp">
          <div>
            <label class="field-label" for="email">Email</label>
            <input
              id="email"
              v-model.trim="email"
              class="input-field mt-1"
              type="email"
              autocomplete="email"
              minlength="5"
              maxlength="50"
              required
            />
          </div>

          <p v-if="requestStatus.message" :class="statusClass(requestStatus.type)" role="status">
            {{ requestStatus.message }}
          </p>

          <button type="submit" class="btn-primary w-full justify-center rounded-lg" :disabled="requestLoading">
            {{ requestLoading ? 'Sending OTP...' : 'Send Verification Code' }}
          </button>
        </form>

        <!-- Step 2: Verify OTP -->
        <form v-else-if="step === 2" class="form-stack" @submit.prevent="handleVerifyOtp">
          <div class="status-success" role="status">
            <p>OTP sent to <strong>{{ email }}</strong></p>
          </div>

          <!-- OTP Timer and Expiration Alert -->
          <p
            v-if="timerText"
            :class="[
              'status font-bold tracking-wide text-xs px-3 py-2 rounded-lg',
              timerTextType === 'error' ? 'status-error' : 'status-warning animate-pulse'
            ]"
            role="status"
          >
            {{ timerText }}
          </p>

          <!-- OTP Input digit fields -->
          <div>
            <label class="field-label">Verification Code</label>
            <div class="grid grid-cols-6 gap-2 mt-1" aria-label="6 digit otp code">
              <input
                v-for="(digit, idx) in otpDigits"
                :key="idx"
                :ref="el => { if (el) otpInputRefs[idx] = el as HTMLInputElement }"
                v-model="otpDigits[idx]"
                type="text"
                class="input-field text-center font-mono text-xl font-bold py-2.5"
                inputmode="numeric"
                maxlength="1"
                :disabled="!isOtpInputsEnabled"
                :aria-label="'OTP digit ' + (idx + 1)"
                @input="handleOtpInput($event, idx)"
                @keydown="handleOtpKeydown($event, idx)"
                @paste="handleOtpPaste($event, idx)"
              />
            </div>
          </div>

          <p v-if="verifyStatus.message" :class="statusClass(verifyStatus.type)" role="status">
            {{ verifyStatus.message }}
          </p>

          <!-- Verify button (disabled when OTP is expired) -->
          <button
            v-if="!isExpired"
            type="submit"
            class="btn-primary w-full justify-center rounded-lg"
            :disabled="!isOtpInputsEnabled || verifyLoading"
          >
            {{ verifyLoading ? 'Verifying...' : 'Verify Code' }}
          </button>

          <!-- Resend button (rendered only when expiration hits) -->
          <button
            v-else
            type="button"
            class="btn-primary w-full justify-center rounded-lg"
            :disabled="requestLoading"
            @click="handleRequestOtp"
          >
            {{ requestLoading ? 'Resending OTP...' : 'Resend OTP' }}
          </button>

          <button type="button" class="btn-secondary w-full justify-center rounded-lg text-xs" @click="goBackToStep1">
            Use a different email
          </button>
        </form>

        <!-- Step 3: Create Account -->
        <form v-else class="form-stack" @submit.prevent="submitTeacherRegister">
          <div class="status-success" role="status">
            Email verified successfully! Now create your password.
          </div>

          <div>
            <label class="field-label">Email</label>
            <input class="input-field bg-surface-2 cursor-not-allowed mt-1" type="email" :value="email" disabled />
          </div>

          <div>
            <label class="field-label" for="teacher-password">Password</label>
            <div class="grid grid-cols-[1fr_auto] gap-2 mt-1">
              <input
                id="teacher-password"
                v-model="password"
                class="input-field"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                minlength="8"
                maxlength="30"
                required
              />
              <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">
                {{ showPassword ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>

          <p v-if="formStatus.message" :class="statusClass(formStatus.type)" role="status">
            {{ formStatus.message }}
          </p>

          <button
            type="submit"
            class="btn-primary w-full justify-center rounded-lg mt-2"
            :disabled="submitLoading"
          >
            {{ submitLoading ? 'Creating account...' : 'Create account' }}
          </button>
        </form>
      </template>

      <p class="mt-5 text-sm text-ink-soft">
        Already registered?
        <RouterLink :to="`/login?role=${role}`" class="font-bold text-brand-blue">Go to login</RouterLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

type Role = 'student' | 'teacher'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const requestedRole = route.query.role === 'student' ? 'student' : 'teacher'
const role = ref<Role>(requestedRole)

// Wizard Step (1 = Request, 2 = Verify, 3 = Create)
const step = ref(1)

// Form fields
const email = ref('')
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const message = ref('')
const validationError = ref('')
const verifiedEmailRef = ref(localStorage.getItem('teacher_verified_email') || '')

// Verification states
const isOtpInputsEnabled = ref(false)
const isRequestButtonEnabled = ref(true)
const isExpired = ref(false)

// OTP digits
const otpDigits = ref(['', '', '', '', '', ''])
const otpInputRefs = ref<(HTMLInputElement | null)[]>([null, null, null, null, null, null])

// Status & timers
const requestStatus = ref({ message: '', type: '' })
const verifyStatus = ref({ message: '', type: '' })
const formStatus = ref({ message: '', type: '' })
const timerText = ref('')
const timerTextType = ref('')

// Countdown
const countdownInterval = ref<any>(null)

// Loading status
const requestLoading = ref(false)
const verifyLoading = ref(false)
const submitLoading = ref(false)

const roleLabel = computed(() => role.value === 'student' ? 'Student' : 'Teacher')

const stepLabel = computed(() => {
  if (step.value === 1) return 'Email Verification'
  if (step.value === 2) return 'Enter Code'
  return 'Create Account'
})

function statusClass(type: string) {
  if (type === 'success') return 'status-success'
  if (type === 'error') return 'status-error'
  if (type === 'info') return 'status-warning'
  return ''
}

// Countdown methods
function stopCountdown() {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
    countdownInterval.value = null
  }
}

function clearOtpSession() {
  stopCountdown()
  localStorage.removeItem('teacher_otp_expires_at')
  localStorage.removeItem('teacher_pending_email')
}

function clearTeacherRegistrationState() {
  clearOtpSession()
  clearOtpValue()
  localStorage.removeItem('teacher_verified_email')
  localStorage.removeItem('teacher_register_step')
  verifiedEmailRef.value = ''
  isOtpInputsEnabled.value = false
  isRequestButtonEnabled.value = true
  isExpired.value = false
  timerText.value = ''
  requestStatus.value = { message: '', type: '' }
  verifyStatus.value = { message: '', type: '' }
  formStatus.value = { message: '', type: '' }
}

function expireOtpSession() {
  stopCountdown()
  clearOtpValue()
  isOtpInputsEnabled.value = false
  isRequestButtonEnabled.value = true
  isExpired.value = true
  timerText.value = "OTP expired. Request a new code."
  timerTextType.value = "error"
  requestStatus.value = { message: "OTP expired. Please request a new code.", type: "error" }
  verifyStatus.value = { message: "", type: "" }
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000))
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0")
  const seconds = String(totalSeconds % 60).padStart(2, "0")
  return `${minutes}:${seconds}`
}

function updateCountdown(expiresAt: number) {
  const remaining = expiresAt - Date.now()
  if (remaining <= 0) {
    expireOtpSession()
    return
  }
  timerText.value = `OTP expires in ${formatRemaining(remaining)}`
  timerTextType.value = "info"
}

function startCountdown(expiresAt: number) {
  stopCountdown()
  isExpired.value = false
  updateCountdown(expiresAt)
  countdownInterval.value = setInterval(() => {
    updateCountdown(expiresAt)
  }, 1000)
}

function clearOtpValue() {
  otpDigits.value = ['', '', '', '', '', '']
}

function focusOtpDigit(index: number) {
  const target = otpInputRefs.value[index]
  if (target) {
    target.focus()
    target.select()
  }
}

function setOtpDigitStateFromPaste(index: number, pastedValue: string) {
  const digits = pastedValue.replace(/\D/g, "").slice(0, 6 - index).split("")
  digits.forEach((digit, offset) => {
    if (index + offset < 6) {
      otpDigits.value[index + offset] = digit
    }
  })

  const nextIndex = Math.min(index + digits.length, 5)
  focusOtpDigit(nextIndex)
}

function handleOtpInput(event: Event, index: number) {
  const target = event.target as HTMLInputElement
  const cleaned = target.value.replace(/\D/g, "")

  if (!cleaned) {
    otpDigits.value[index] = ""
    return
  }

  if (cleaned.length > 1) {
    setOtpDigitStateFromPaste(index, cleaned)
    return
  }

  otpDigits.value[index] = cleaned.slice(0, 1)

  if (index < 5) {
    focusOtpDigit(index + 1)
  }
}

function handleOtpKeydown(event: KeyboardEvent, index: number) {
  const target = event.target as HTMLInputElement
  if (event.key === "Backspace" && !target.value && index > 0) {
    focusOtpDigit(index - 1)
  }
}

function handleOtpPaste(event: ClipboardEvent, index: number) {
  event.preventDefault()
  const pasted = event.clipboardData?.getData("text") || ""
  setOtpDigitStateFromPaste(index, pasted)
}

function isStepSelectable(targetStep: number) {
  const savedStep = localStorage.getItem('teacher_register_step')
  const hasRequested = savedStep === '2' && !!localStorage.getItem('teacher_pending_email')
  const hasVerified = savedStep === '3' && !!localStorage.getItem('teacher_verified_email')

  let maxStep = 1
  if (hasVerified) maxStep = 3
  else if (hasRequested) maxStep = 2

  return targetStep <= maxStep
}

function goToStep(targetStep: number) {
  if (isStepSelectable(targetStep)) {
    step.value = targetStep
    localStorage.setItem('teacher_register_step', String(targetStep))
  }
}

function goBackToStep1() {
  clearTeacherRegistrationState()
  step.value = 1
}

// Restore active registration steps & details on mount/refresh
function restoreOtpSession() {
  const savedStep = localStorage.getItem('teacher_register_step')
  const savedExpiry = Number(localStorage.getItem('teacher_otp_expires_at'))
  const savedEmail = localStorage.getItem('teacher_pending_email')
  const verifiedEmail = localStorage.getItem('teacher_verified_email')

  if (savedStep === '3' && verifiedEmail) {
    email.value = verifiedEmail
    step.value = 3
    return
  }

  if (savedStep === '2' && savedEmail) {
    email.value = savedEmail
    step.value = 2

    if (!savedExpiry || savedExpiry <= Date.now()) {
      expireOtpSession()
    } else {
      isOtpInputsEnabled.value = true
      isRequestButtonEnabled.value = false
      startCountdown(savedExpiry)
      requestStatus.value = {
        message: "OTP already sent. Check your email and verify before it expires.",
        type: "success"
      }
    }
    return
  }

  // Fallback to step 1
  clearTeacherRegistrationState()
  step.value = 1
}

// Listen to email changes to clear active registration sessions
watch(email, (newValue) => {
  if (step.value !== 1) return // Watcher applies only on email step modification

  const currentEmail = newValue.trim()
  const pendingEmail = localStorage.getItem('teacher_pending_email')
  const verifiedEmail = localStorage.getItem('teacher_verified_email')

  if (verifiedEmail && verifiedEmail !== currentEmail) {
    clearTeacherRegistrationState()
    return
  }

  if (pendingEmail && pendingEmail !== currentEmail) {
    clearTeacherRegistrationState()
  }
})

// ─── Student Registration ───
async function submitStudentRegister() {
  validationError.value = ''
  message.value = ''
  auth.error = ''

  if (!/^[A-Z]/.test(username.value)) {
    validationError.value = 'Username must start with an uppercase letter.'
    return
  }

  if (password.value.toLowerCase() === username.value.toLowerCase()) {
    validationError.value = 'Password must not be the same as username.'
    return
  }

  try {
    await auth.register({
      role: 'student',
      email: null,
      username: username.value,
      password: password.value,
    })

    message.value = 'Account created. You can now login.'
    password.value = ''
  } catch {
    // auth store owns the error
  }
}

// ─── Teacher: Step 1 (Request OTP) / Step 2 (Resend OTP) ───
async function handleRequestOtp() {
  const currentEmail = email.value.trim()
  requestStatus.value = { message: '', type: '' }
  verifyStatus.value = { message: '', type: '' }
  formStatus.value = { message: '', type: '' }
  timerText.value = ''

  if (!currentEmail) {
    requestStatus.value = { message: "Email is required.", type: "error" }
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(currentEmail)) {
    requestStatus.value = { message: "Enter a valid email address.", type: "error" }
    return
  }

  requestLoading.value = true
  try {
    await auth.requestTeacherOtp(currentEmail)

    const expiresAt = Date.now() + 5 * 60 * 1000
    localStorage.setItem('teacher_pending_email', currentEmail)
    localStorage.setItem('teacher_otp_expires_at', String(expiresAt))
    localStorage.setItem('teacher_register_step', '2')

    isOtpInputsEnabled.value = true
    isRequestButtonEnabled.value = false
    isExpired.value = false
    clearOtpValue()
    startCountdown(expiresAt)
    step.value = 2

    setTimeout(() => focusOtpDigit(0), 50)

    requestStatus.value = {
      message: "OTP sent. Check your email and enter the 6 digits below.",
      type: "success"
    }
    verifyStatus.value = {
      message: "Enter the code before the timer ends.",
      type: "info"
    }
  } catch (err: any) {
    const errMsg = err instanceof Error ? err.message : String(err)

    if (errMsg.includes("Email already registered") || errMsg.includes("Account already exists")) {
      clearTeacherRegistrationState()
      requestStatus.value = {
        message: "This email has already been registered. Please log in.",
        type: "error"
      }
      return
    }

    requestStatus.value = {
      message: errMsg,
      type: "error"
    }
  } finally {
    requestLoading.value = false
  }
}

// ─── Teacher: Step 2 (Verify OTP) ───
async function handleVerifyOtp() {
  const currentEmail = email.value.trim()
  const otpVal = otpDigits.value.join("").trim()

  requestStatus.value = { message: '', type: '' }
  verifyStatus.value = { message: '', type: '' }
  formStatus.value = { message: '', type: '' }

  if (!currentEmail) {
    verifyStatus.value = { message: "Email is required.", type: "error" }
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(currentEmail)) {
    verifyStatus.value = { message: "Enter a valid email address.", type: "error" }
    return
  }

  const savedExpiry = Number(localStorage.getItem('teacher_otp_expires_at'))
  if (!savedExpiry || savedExpiry <= Date.now()) {
    expireOtpSession()
    return
  }

  if (!/^\d{6}$/.test(otpVal)) {
    verifyStatus.value = { message: "OTP must be exactly 6 digits.", type: "error" }
    focusOtpDigit(0)
    return
  }

  verifyLoading.value = true
  try {
    await auth.verifyTeacherOtp(currentEmail, otpVal)

    localStorage.setItem('teacher_verified_email', currentEmail)
    localStorage.setItem('teacher_register_step', '3')
    verifiedEmailRef.value = currentEmail

    clearOtpSession()
    timerText.value = ''
    isRequestButtonEnabled.value = true
    isOtpInputsEnabled.value = false
    isExpired.value = false
    
    verifyStatus.value = {
      message: "OTP verified. You can now create the account.",
      type: "success"
    }

    step.value = 3
    
    setTimeout(() => {
      const pwdInput = document.getElementById('teacher-password')
      if (pwdInput) pwdInput.focus()
    }, 50)
  } catch (err: any) {
    const errMsg = err instanceof Error ? err.message : String(err)
    
    if (errMsg.includes("OTP not found") || errMsg.includes("otp already used") || errMsg.includes("OTP is expired!")) {
      verifyStatus.value = {
        message: "OTP is no longer valid. Please request a new code.",
        type: "error"
      }
      return
    }

    if (errMsg.includes("Email already registered") || errMsg.includes("Account already exists")) {
      clearTeacherRegistrationState()
      verifyStatus.value = {
        message: "This email has already been registered. Please log in.",
        type: "error"
      }
      return
    }
    
    verifyStatus.value = {
      message: errMsg,
      type: "error"
    }
  } finally {
    verifyLoading.value = false
  }
}

// ─── Teacher: Step 3 (Submit Registration) ───
async function submitTeacherRegister() {
  const currentEmail = email.value.trim()
  const currentPassword = password.value.trim()
  const verifiedEmail = localStorage.getItem('teacher_verified_email')

  formStatus.value = { message: '', type: '' }

  if (verifiedEmail && verifiedEmail.trim().toLowerCase() !== currentEmail.toLowerCase()) {
    formStatus.value = {
      message: "Verify the same email before creating the account.",
      type: "error"
    }
    return
  }

  if (currentPassword.length < 8 || currentPassword.length > 30) {
    formStatus.value = {
      message: "Password must be between 8 and 30 characters.",
      type: "error"
    }
    return
  }

  submitLoading.value = true
  try {
    await auth.register({
      role: 'teacher',
      email: currentEmail,
      username: null,
      password: currentPassword,
    })

    localStorage.removeItem('teacher_pending_email')
    localStorage.removeItem('teacher_otp_expires_at')
    localStorage.removeItem('teacher_verified_email')
    localStorage.removeItem('teacher_register_step')

    formStatus.value = {
      message: "Teacher account created. Redirecting to login...",
      type: "success"
    }
    password.value = ''

    setTimeout(() => {
      router.push('/login?role=teacher')
    }, 800)
  } catch (err: any) {
    formStatus.value = {
      message: err instanceof Error ? err.message : "Registration failed",
      type: "error"
    }
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  if (role.value === 'teacher') {
    restoreOtpSession()
  }
})

onUnmounted(() => {
  stopCountdown()
})
</script>
