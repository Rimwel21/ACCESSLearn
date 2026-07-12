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
      <h1 class="font-display text-[2rem] font-bold text-ink leading-tight mb-1">
        Create Account
      </h1>
      <p class="text-sm text-ink-soft mb-6">Join as a {{ roleLabel.toLowerCase() }} and start using inclusive learning tools right away.</p>

        <template v-if="role === 'student'">
          <form class="mt-8 grid gap-4" @submit.prevent="submitStudentRegister">
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="field-label" for="student-name">Full name</label>
                <input id="student-name" v-model.trim="studentFullName" class="input-field mt-2" type="text" placeholder="Juan Dela Cruz" required />
              </div>
              <div>
                <label class="field-label" for="student-id">Student ID</label>
                <input id="student-id" v-model.trim="studentId" class="input-field mt-2" type="text" placeholder="e.g. 20240001" required />
              </div>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="field-label" for="grade-level">Grade level</label>
                <input id="grade-level" v-model.trim="studentGradeLevel" class="input-field mt-2" type="text" placeholder="Grade 7" required />
              </div>
              <div>
                <label class="field-label" for="student-email">School email</label>
                <input id="student-email" v-model.trim="studentEmail" class="input-field mt-2" type="email" placeholder="student@school.edu" required />
              </div>
            </div>

            <div>
              <label class="field-label" for="student-password">Password</label>
              <div class="mt-2 grid grid-cols-[1fr_auto] gap-2">
                <input id="student-password" v-model="password" class="input-field" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" maxlength="30" required />
                <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">{{ showPassword ? 'Hide' : 'Show' }}</button>
              </div>
            </div>

            <div>
              <label class="field-label" for="student-confirm">Confirm password</label>
              <input id="student-confirm" v-model="studentConfirmPassword" class="input-field mt-2" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" required />
            </div>

            <p v-if="message" class="status-success" role="status">{{ message }}</p>
            <p v-if="validationError" class="status-error" role="alert">{{ validationError }}</p>
            <p v-if="auth.error" class="status-error" role="alert">{{ auth.error }}</p>

            <button type="submit" class="btn-primary mt-2 w-full justify-center rounded-full" :disabled="auth.loading">
              {{ auth.loading ? 'Creating account...' : 'Create account' }}
            </button>
          </form>
        </template>

        <template v-else>
          <div class="mt-6 flex items-center gap-2">
            <div v-for="s in 3" :key="s" class="flex items-center gap-2">
              <button
                type="button"
                @click="goToStep(s)"
                :disabled="!isStepSelectable(s)"
                :class="[
                  'inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all border-0 outline-none p-0',
                  step >= s ? 'bg-brand-blue text-white shadow-sm' : 'bg-surface-2 text-ink-soft',
                  isStepSelectable(s) ? 'cursor-pointer hover:bg-brand-blue/95 hover:text-white' : 'cursor-not-allowed'
                ]"
              >{{ s }}</button>
              <span v-if="s < 3" :class="['h-0.5 w-6 rounded-full transition-all', step > s ? 'bg-brand-blue' : 'bg-surface-2']" />
            </div>
            <span class="ml-2 text-xs font-semibold text-ink-soft">{{ stepLabel }}</span>
          </div>

          <form v-if="step === 1" class="mt-6 grid gap-4" @submit.prevent="handleRequestOtp">
            <div>
              <label class="field-label" for="teacher-email">Official school email</label>
              <input id="teacher-email" v-model.trim="email" class="input-field mt-2" type="email" autocomplete="email" minlength="5" maxlength="60" required />
            </div>

            <p v-if="requestStatus.message" :class="statusClass(requestStatus.type)" role="status">
              {{ requestStatus.message }}
            </p>

            <button type="submit" class="btn-primary w-full justify-center rounded-full" :disabled="requestLoading">
              {{ requestLoading ? 'Sending OTP...' : 'Send verification code' }}
            </button>
          </form>

          <form v-else-if="step === 2" class="mt-6 grid gap-4" @submit.prevent="handleVerifyOtp">
            <div class="status-success" role="status">
              <p>We sent a 6-digit code to <strong>{{ email }}</strong>.</p>
            </div>

            <p v-if="timerText" :class="['font-bold tracking-wide text-xs px-3 py-2 rounded-lg', timerTextType === 'error' ? 'status-error' : 'status-warning animate-pulse']" role="status">
              {{ timerText }}
            </p>

            <div>
              <label class="field-label">Verification code</label>
              <div class="mt-2 grid grid-cols-6 gap-2" aria-label="6 digit otp code">
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

            <button v-if="!isExpired" type="submit" class="btn-primary w-full justify-center rounded-full" :disabled="!isOtpInputsEnabled || verifyLoading">
              {{ verifyLoading ? 'Verifying...' : 'Verify code' }}
            </button>

            <button v-else type="button" class="btn-primary w-full justify-center rounded-full" :disabled="requestLoading" @click="handleRequestOtp">
              {{ requestLoading ? 'Resending OTP...' : 'Resend OTP' }}
            </button>

            <button type="button" class="btn-secondary w-full justify-center rounded-full text-xs" @click="goBackToStep1">
              Use a different email
            </button>
          </form>

          <form v-else class="mt-6 grid gap-4" @submit.prevent="submitTeacherRegister">
            <div class="status-success" role="status">
              Email verified successfully. Finish your profile details below.
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="field-label" for="teacher-name">Full name</label>
                <input id="teacher-name" v-model.trim="teacherFullName" class="input-field mt-2" type="text" placeholder="Maria Santos" required />
              </div>
              <div>
                <label class="field-label" for="teacher-id">Teacher ID</label>
                <input id="teacher-id" v-model.trim="teacherId" class="input-field mt-2" type="text" placeholder="T-101" required />
              </div>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="field-label" for="teacher-subject">Assigned subject</label>
                <input id="teacher-subject" v-model.trim="teacherSubject" class="input-field mt-2" type="text" placeholder="English" />
              </div>
              <div>
                <label class="field-label" for="teacher-school">School name</label>
                <input id="teacher-school" v-model.trim="teacherSchool" class="input-field mt-2" type="text" placeholder="Happy Valley High School" />
              </div>
            </div>

            <div>
              <label class="field-label" for="teacher-password">Password</label>
              <div class="mt-2 grid grid-cols-[1fr_auto] gap-2">
                <input id="teacher-password" v-model="password" class="input-field" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" maxlength="30" required />
                <button type="button" class="btn-secondary rounded-lg" @click="showPassword = !showPassword">{{ showPassword ? 'Hide' : 'Show' }}</button>
              </div>
            </div>

            <div>
              <label class="field-label" for="teacher-confirm">Confirm password</label>
              <input id="teacher-confirm" v-model="teacherConfirmPassword" class="input-field mt-2" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" required />
            </div>

            <p v-if="formStatus.message" :class="statusClass(formStatus.type)" role="status">
              {{ formStatus.message }}
            </p>

            <button type="submit" class="btn-primary w-full justify-center rounded-full mt-2" :disabled="submitLoading">
              {{ submitLoading ? 'Creating account...' : 'Create account' }}
            </button>
          </form>
        </template>

        <p class="mt-6 text-sm text-ink-soft">
          Already registered?
          <RouterLink :to="`/login?role=${role}`" class="font-bold text-brand-blue transition-colors hover:text-blue-700">Go to login</RouterLink>
        </p>
    </div>
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

const role = ref<Role>(route.query.role === 'student' ? 'student' : 'teacher')

const step = ref(1)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const message = ref('')
const validationError = ref('')
const verifiedEmailRef = ref(localStorage.getItem('teacher_verified_email') || '')

const studentFullName = ref('')
const studentId = ref('')
const studentGradeLevel = ref('')
const studentEmail = ref('')
const studentConfirmPassword = ref('')
const teacherFullName = ref('')
const teacherId = ref('')
const teacherSubject = ref('')
const teacherSchool = ref('')
const teacherConfirmPassword = ref('')

const isOtpInputsEnabled = ref(false)
const isRequestButtonEnabled = ref(true)
const isExpired = ref(false)
const otpDigits = ref(['', '', '', '', '', ''])
const otpInputRefs = ref<(HTMLInputElement | null)[]>([null, null, null, null, null, null])
const requestStatus = ref({ message: '', type: '' })
const verifyStatus = ref({ message: '', type: '' })
const formStatus = ref({ message: '', type: '' })
const timerText = ref('')
const timerTextType = ref('')
const countdownInterval = ref<any>(null)
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
  timerText.value = 'OTP expired. Request a new code.'
  timerTextType.value = 'error'
  requestStatus.value = { message: 'OTP expired. Please request a new code.', type: 'error' }
  verifyStatus.value = { message: '', type: '' }
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000))
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
  const seconds = String(totalSeconds % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

function updateCountdown(expiresAt: number) {
  const remaining = expiresAt - Date.now()
  if (remaining <= 0) {
    expireOtpSession()
    return
  }
  timerText.value = `OTP expires in ${formatRemaining(remaining)}`
  timerTextType.value = 'info'
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
  const digits = pastedValue.replace(/\D/g, '').slice(0, 6 - index).split('')
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
  const cleaned = target.value.replace(/\D/g, '')

  if (!cleaned) {
    otpDigits.value[index] = ''
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
  if (event.key === 'Backspace' && !target.value && index > 0) {
    focusOtpDigit(index - 1)
  }
}

function handleOtpPaste(event: ClipboardEvent, index: number) {
  event.preventDefault()
  const pasted = event.clipboardData?.getData('text') || ''
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
        message: 'OTP already sent. Check your email and verify before it expires.',
        type: 'success',
      }
    }
    return
  }

  clearTeacherRegistrationState()
  step.value = 1
}

watch(email, (newValue) => {
  if (step.value !== 1) return

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


async function submitStudentRegister() {
  validationError.value = ''
  message.value = ''
  auth.error = ''

  if (!studentFullName.value.trim()) {
    validationError.value = 'Please enter your full name.'
    return
  }

  if (!studentId.value.trim()) {
    validationError.value = 'Please enter your student ID.'
    return
  }

  if (!studentGradeLevel.value.trim()) {
    validationError.value = 'Please choose a grade level.'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(studentEmail.value.trim())) {
    validationError.value = 'Enter a valid school email address.'
    return
  }

  if (password.value.length < 8 || !/^(?=.*[A-Za-z])(?=.*\d).+/.test(password.value)) {
    validationError.value = 'Password must be at least 8 characters and include letters and numbers.'
    return
  }

  if (password.value !== studentConfirmPassword.value) {
    validationError.value = 'Passwords do not match.'
    return
  }

  try {
    await auth.register({
      role: 'student',
      email: studentEmail.value.trim(),
      username: studentId.value.trim(),
      password: password.value,
    })

    message.value = 'Your student account was created. You can now sign in.'
    studentFullName.value = ''
    studentId.value = ''
    studentGradeLevel.value = ''
    studentEmail.value = ''
    studentConfirmPassword.value = ''
    password.value = ''
  } catch {
    // auth store owns the visible error
  }
}

async function handleRequestOtp() {
  const currentEmail = email.value.trim()
  requestStatus.value = { message: '', type: '' }
  verifyStatus.value = { message: '', type: '' }
  formStatus.value = { message: '', type: '' }
  timerText.value = ''

  if (!currentEmail) {
    requestStatus.value = { message: 'Email is required.', type: 'error' }
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(currentEmail)) {
    requestStatus.value = { message: 'Enter a valid school email address.', type: 'error' }
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
      message: 'OTP sent. Check your email and enter the 6-digit code below.',
      type: 'success',
    }
    verifyStatus.value = {
      message: 'Enter the code before the timer ends.',
      type: 'info',
    }
  } catch (err: any) {
    const errMsg = err instanceof Error ? err.message : String(err)

    if (errMsg.includes('pending email')) {
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

      setTimeout(() => focusOtpDigit(0), 55)

      requestStatus.value = {
        message: 'A verification code is already active for this email. Check your email and enter the code below.',
        type: 'success',
      }
      verifyStatus.value = {
        message: 'Enter the pending code.',
        type: 'info',
      }
      return
    }

    if (errMsg.includes('Email already registered') || errMsg.includes('Account already exists')) {
      clearTeacherRegistrationState()
      requestStatus.value = {
        message: 'This email has already been registered. Please log in.',
        type: 'error',
      }
      return
    }

    requestStatus.value = {
      message: errMsg,
      type: 'error',
    }
  } finally {
    requestLoading.value = false
  }
}

async function handleVerifyOtp() {
  const currentEmail = email.value.trim()
  const otpVal = otpDigits.value.join('').trim()

  requestStatus.value = { message: '', type: '' }
  verifyStatus.value = { message: '', type: '' }
  formStatus.value = { message: '', type: '' }

  if (!currentEmail) {
    verifyStatus.value = { message: 'Email is required.', type: 'error' }
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(currentEmail)) {
    verifyStatus.value = { message: 'Enter a valid email address.', type: 'error' }
    return
  }

  const savedExpiry = Number(localStorage.getItem('teacher_otp_expires_at'))
  if (!savedExpiry || savedExpiry <= Date.now()) {
    expireOtpSession()
    return
  }

  if (!/^\d{6}$/.test(otpVal)) {
    verifyStatus.value = { message: 'OTP must be exactly 6 digits.', type: 'error' }
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
      message: 'OTP verified. You can now complete the account setup.',
      type: 'success',
    }

    step.value = 3

    setTimeout(() => {
      const pwdInput = document.getElementById('teacher-password')
      if (pwdInput) pwdInput.focus()
    }, 50)
  } catch (err: any) {
    const errMsg = err instanceof Error ? err.message : String(err)

    if (errMsg.includes('OTP not found') || errMsg.includes('otp already used') || errMsg.includes('OTP is expired!')) {
      verifyStatus.value = {
        message: 'OTP is no longer valid. Please request a new code.',
        type: 'error',
      }
      return
    }

    if (errMsg.includes('Email already registered') || errMsg.includes('Account already exists')) {
      clearTeacherRegistrationState()
      verifyStatus.value = {
        message: 'This email has already been registered. Please log in.',
        type: 'error',
      }
      return
    }

    verifyStatus.value = {
      message: errMsg,
      type: 'error',
    }
  } finally {
    verifyLoading.value = false
  }
}

async function submitTeacherRegister() {
  const currentEmail = email.value.trim()
  const currentPassword = password.value.trim()
  const verifiedEmail = localStorage.getItem('teacher_verified_email')

  formStatus.value = { message: '', type: '' }

  if (!teacherFullName.value.trim()) {
    formStatus.value = { message: 'Please enter your full name.', type: 'error' }
    return
  }

  if (!teacherId.value.trim()) {
    formStatus.value = { message: 'Please enter your teacher ID.', type: 'error' }
    return
  }

  if (verifiedEmail && verifiedEmail.trim().toLowerCase() !== currentEmail.toLowerCase()) {
    formStatus.value = { message: 'Verify the same email before creating the account.', type: 'error' }
    return
  }

  if (currentPassword.length < 8 || !/^(?=.*[A-Za-z])(?=.*\d).+/.test(currentPassword)) {
    formStatus.value = { message: 'Password must be at least 8 characters and include letters and numbers.', type: 'error' }
    return
  }

  if (currentPassword !== teacherConfirmPassword.value) {
    formStatus.value = { message: 'Passwords do not match.', type: 'error' }
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
      message: 'Teacher account created. Redirecting to login...',
      type: 'success',
    }
    password.value = ''
    teacherConfirmPassword.value = ''

    setTimeout(() => {
      router.push('/login?role=teacher')
    }, 800)
  } catch (err: any) {
    formStatus.value = {
      message: err instanceof Error ? err.message : 'Registration failed',
      type: 'error',
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
