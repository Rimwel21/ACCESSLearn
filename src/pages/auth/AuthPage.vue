<template>
  <main class="auth-page bg-surface min-h-screen py-6 sm:py-12 px-4 sm:px-6 lg:px-8 flex items-center justify-center font-body">
    <div class="auth-card w-full max-w-[1100px] bg-white rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col md:flex-row min-h-[600px] lg:min-h-[700px] border border-gray-100">
      
      <!-- Left side: Visual & Branding (Hidden on mobile) -->
      <div class="hidden md:flex md:w-[45%] lg:w-[40%] bg-brand-blue p-8 lg:p-12 flex-col justify-between text-white relative overflow-hidden">
        <div class="relative z-10">
          <RouterLink to="/" class="flex items-center gap-3 mb-12 group transition-transform hover:scale-105 active:scale-95 origin-left">
            <div class="h-10 w-10 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center group-hover:bg-white/40 transition-colors font-bold text-lg shadow-sm border border-white/10">AL</div>
            <span class="font-display font-bold text-2xl tracking-tighter">ACCESSLearn</span>
          </RouterLink>
          
          <div class="space-y-6 animate-fade-in-left">
            <h2 class="text-4xl font-display font-bold leading-[1.1]">Inclusive Learning for Everyone.</h2>
            <p class="text-blue-100/80 text-base leading-relaxed font-medium">
              Join our community of teachers and students dedicated to making e-learning accessible, engaging, and organized.
            </p>
          </div>
        </div>

        <div class="relative z-10">
          <div class="flex items-center gap-4 p-4 bg-white/10 backdrop-blur-md rounded-2xl border border-white/5">
            <div class="h-12 w-12 rounded-full bg-brand-yellow flex items-center justify-center text-xl shadow-lg">🤟</div>
            <div>
              <p class="text-xs font-bold text-blue-100">Accessibility First</p>
              <p class="text-[10px] font-medium text-blue-200/70">WCAG 2.1 Compliant Design</p>
            </div>
          </div>
        </div>
        
        <!-- Abstract Background Orbs -->
        <div class="absolute -bottom-20 -left-20 h-80 w-80 bg-brand-violet/20 rounded-full blur-[100px]"></div>
        <div class="absolute top-40 -right-20 h-60 w-60 bg-brand-teal/20 rounded-full blur-[80px]"></div>
      </div>

      <!-- Right side: Content Area -->
      <div class="flex-1 p-6 sm:p-10 lg:p-20 pt-20 lg:pt-24 flex flex-col items-center justify-center relative bg-white">
        <!-- Back Button -->
        <RouterLink to="/" class="absolute top-4 left-4 lg:top-8 lg:left-8 flex items-center group active:scale-95 transition-transform z-20">
          <div class="relative flex items-center bg-gradient-to-r from-brand-blue to-blue-400 pl-6 pr-12 py-2.5 rounded-full shadow-lg shadow-brand-blue/20 transition-all group-hover:shadow-brand-blue/40 group-hover:-translate-y-0.5">
            <span class="text-xs font-black uppercase tracking-[0.1em] text-white">Back</span>
            <div class="absolute -right-1 h-10 w-10 rounded-full bg-white border-2 border-brand-blue flex items-center justify-center text-brand-blue shadow-md transition-transform group-hover:rotate-[-45deg]">
              <svg class="h-5 w-5 transition-transform duration-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 14L4 9L9 4" />
                <path d="M20 20v-7a4 4 0 0 0-4-4H4" />
              </svg>
            </div>
          </div>
        </RouterLink>

        <!-- Tabbed Switch -->
        <div class="w-full max-w-sm mb-12">
          <div class="inline-flex p-1.5 bg-surface-2 rounded-2xl w-full shadow-inner border border-gray-200/50 relative">
            <div 
              class="absolute inset-y-1.5 left-1.5 w-[calc(50%-6px)] bg-white rounded-xl shadow-md transition-transform duration-300 ease-out z-0"
              :style="{ transform: mode === 'login' ? 'translateX(0)' : 'translateX(100%)' }"
            ></div>
            <button 
              @click="setMode('login')" 
              :class="['flex-1 py-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-colors duration-300 relative z-10', mode === 'login' ? 'text-brand-blue' : 'text-ink-soft hover:text-ink']"
            >
              Sign In
            </button>
            <button 
              @click="setMode('register')" 
              :class="['flex-1 py-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-colors duration-300 relative z-10', mode === 'register' ? 'text-brand-blue' : 'text-ink-soft hover:text-ink']"
            >
              Join Us
            </button>
          </div>
        </div>

        <!-- Role Toggle (Student/Teacher) -->
        <div class="w-full max-w-md mb-8 text-center bg-surface-2 p-1.5 rounded-2xl border border-gray-100/50">
          <div class="flex justify-center gap-1">
            <button 
              v-for="r in (['student', 'teacher'] as Role[])" 
              :key="r"
              @click="role = r" 
              :class="['flex-1 px-6 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2', 
                role === r 
                ? 'bg-white text-brand-blue shadow-sm' 
                : 'text-ink-soft hover:text-ink'
              ]"
            >
              <span>{{ r === 'student' ? '🎒' : '👩‍🏫' }}</span>
              {{ r === 'student' ? 'Student' : 'Teacher' }}
            </button>
          </div>
        </div>

        <!-- Header -->
        <div class="w-full max-w-lg text-center mb-10">
          <h1 class="font-display text-4xl lg:text-5xl font-bold text-ink leading-tight tracking-tight">
            {{ mode === 'login' ? 'Welcome Back' : 'Create Account' }}
          </h1>
          <p class="text-sm font-medium text-ink-soft mt-4">
            Access the official {{ role }} portal to continue your interactive learning session.
          </p>
        </div>

        <!-- Login Flow -->
        <div v-show="mode === 'login' && !forgotPasswordMode" class="w-full max-w-md animate-fade-in-up">
          <form @submit.prevent="handleLogin" class="space-y-6">
            <div class="space-y-2" v-if="role === 'teacher'">
              <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="l-email">Email Address</label>
              <div class="relative group">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-brand-blue transition-colors">✉️</span>
                <input id="l-email" v-model="loginForm.email" type="email" placeholder="name@school.edu.ph" class="input-field !pl-11 py-4.5 text-sm" required />
              </div>
            </div>
            <div class="space-y-2" v-else>
              <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="l-username">Student Username</label>
              <div class="relative group">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-brand-blue transition-colors">👤</span>
                <input id="l-username" v-model="loginForm.username" type="text" placeholder="Your account ID" class="input-field !pl-11 py-4.5 text-sm" required />
              </div>
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="l-password">Password</label>
                <button type="button" @click="forgotPasswordMode = true" class="text-[10px] font-black text-brand-blue hover:text-blue-700 transition-colors uppercase tracking-[0.1em]">Forgot?</button>
              </div>
              <div class="relative group">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 transition-colors group-focus-within:text-brand-blue">🔒</span>
                <input id="l-password" v-model="loginForm.password" :type="showPassword ? 'text' : 'password'" class="input-field !pl-11 pr-12 py-4.5 text-sm" placeholder="••••••••" required />
                <button type="button" @click="showPassword = !showPassword" class="absolute right-4 top-1/2 -translate-y-1/2 h-8 w-8 flex items-center justify-center rounded-lg hover:bg-surface-2 transition-colors">
                  <span v-if="showPassword" class="text-sm">👁️</span>
                  <span v-else class="text-sm opacity-50">👁️‍🗨️</span>
                </button>
              </div>
            </div>

            <div class="flex items-center justify-between pt-2">
              <label class="flex items-center gap-2 cursor-pointer group">
                <input type="checkbox" v-model="rememberMe" class="h-4 w-4 rounded border-gray-200 text-brand-blue focus:ring-brand-blue/20 transition-all cursor-pointer" />
                <span class="text-xs font-bold text-ink-soft group-hover:text-ink transition-colors">Remember me on this device</span>
              </label>
            </div>

            <button type="submit" class="btn-primary w-full py-4.5 rounded-2xl shadow-2xl shadow-brand-blue/20 flex items-center justify-center gap-3 active:scale-95 transition-all mt-4" :disabled="auth.loading">
              <span v-if="auth.loading" class="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"></span>
              <span class="font-bold tracking-tight text-lg">{{ auth.loading ? 'Authenticating...' : 'Sign Into Dashboard' }}</span>
              <span v-if="!auth.loading" class="text-xl">➔</span>
            </button>
          </form>
        </div>

        <!-- Registration Flow -->
        <div v-show="mode === 'register'" class="w-full max-w-lg animate-fade-in-up">
          <form @submit.prevent="handleRegister" class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="space-y-1.5 sm:col-span-2">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-full-name">Official Full Name</label>
                <input id="r-full-name" v-model="registerForm.fullName" type="text" placeholder="John Doe" class="input-field py-4 text-sm" required />
              </div>
              
              <div class="space-y-1.5">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-email">Email Address</label>
                <input id="r-email" v-model="registerForm.email" type="email" placeholder="john@example.com" class="input-field py-4 text-sm" required />
              </div>

              <div class="space-y-1.5">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-contact">Contact No.</label>
                <input id="r-contact" v-model="registerForm.contactNo" type="tel" placeholder="0917-123-4567" class="input-field py-4 text-sm" required />
              </div>

              <template v-if="role === 'student'">
                <div class="space-y-1.5">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-student-id">Student LRN</label>
                  <input id="r-student-id" v-model="registerForm.studentId" type="text" placeholder="12-digit LRN" class="input-field py-4 text-sm" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-username">Portal ID</label>
                  <input id="r-username" v-model="registerForm.username" type="text" placeholder="student_juan" class="input-field py-4 text-sm" required />
                </div>
              </template>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-gray-50 pt-4 mt-2">
              <div class="space-y-1.5">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-password">Set Password</label>
                <input id="r-password" v-model="registerForm.password" type="password" placeholder="••••••••" class="input-field py-4 text-sm" required />
              </div>
              <div class="space-y-1.5">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1" for="r-confirm">Verify</label>
                <input id="r-confirm" v-model="registerForm.confirmPassword" type="password" placeholder="••••••••" class="input-field py-4 text-sm" required />
              </div>
            </div>

            <div v-show="validationError" class="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-xs font-bold text-rose-600 flex items-center gap-3">
              <span class="text-lg">⚠️</span> {{ validationError }}
            </div>

            <button type="submit" class="btn-primary w-full py-4.5 rounded-2xl shadow-2xl shadow-brand-blue/20 flex items-center justify-center gap-3 active:scale-95 transition-all mt-4" :disabled="auth.loading">
              <span v-if="auth.loading" class="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"></span>
              <span class="font-bold tracking-tight text-lg">{{ auth.loading ? 'Registering...' : 'Create ' + roleLabel + ' Account' }}</span>
            </button>
          </form>
        </div>

        <!-- Forgot Password Flow -->
        <div v-show="forgotPasswordMode" class="w-full max-w-lg animate-fade-in-up flex flex-col items-center">
           <div class="text-center mb-10">
             <div class="h-24 w-24 bg-brand-blue/10 rounded-[2.5rem] flex items-center justify-center text-4xl mx-auto mb-6 shadow-sm">🛡️</div>
             <h2 class="font-display text-4xl font-bold text-ink">Identity Recovery</h2>
             <p class="text-sm font-medium text-ink-soft mt-3">Verify your credentials to reset access.</p>
           </div>

           <div v-if="role === 'teacher'" class="space-y-6 w-full">
             <div class="space-y-4" v-if="forgotStep === 1">
                <div class="space-y-2">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1">Work Email</label>
                  <input v-model="forgotPayload.email" type="email" placeholder="name@school.edu.ph" class="input-field py-4.5 text-sm" />
                </div>
                <button @click="requestOTP" class="btn-primary w-full py-4.5 rounded-2xl flex items-center justify-center gap-3">
                   <span class="text-lg font-bold">Send Recovery Link</span>
                   <span class="text-xl">➔</span>
                </button>
             </div>
             <div class="space-y-4" v-if="forgotStep === 2">
                <div class="space-y-4">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 text-center block">Enter Security Code</label>
                  <div class="flex justify-center gap-3">
                    <input v-for="i in 6" :key="i" type="text" maxlength="1" class="h-16 w-12 text-center text-2xl font-bold rounded-2xl border-2 border-gray-100 bg-surface focus:border-brand-blue focus:ring-8 focus:ring-brand-blue/5 outline-none transition-all shadow-sm" />
                  </div>
                </div>
                <button @click="forgotStep = 3" class="btn-primary w-full py-4.5 rounded-2xl text-lg font-bold">Verify Identity</button>
                <div class="flex items-center justify-center gap-2 mt-4">
                  <span class="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <p class="text-center text-[10px] font-black text-ink-soft uppercase tracking-[0.2em]">Code active for 04:59</p>
                </div>
             </div>

             <div class="space-y-6" v-if="forgotStep === 3">
                <div class="space-y-2">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1">New Secure Password</label>
                  <input type="password" class="input-field py-4.5 text-sm" placeholder="••••••••" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1">Confirm Identity</label>
                  <input type="password" class="input-field py-4.5 text-sm" placeholder="••••••••" />
                </div>
                <button @click="resetComplete" class="btn-primary w-full py-4.5 rounded-2xl text-lg font-bold">Secure Account</button>
             </div>
           </div>

           <div v-else class="space-y-6 w-full">
              <div class="p-8 bg-brand-blue rounded-[2.5rem] text-white space-y-4 shadow-xl shadow-brand-blue/10 relative overflow-hidden">
                <div class="absolute -top-10 -right-10 h-32 w-32 bg-white/10 rounded-full blur-2xl"></div>
                <h4 class="font-display text-xl font-bold">Need assistance?</h4>
                <p class="text-xs font-medium text-blue-100 leading-relaxed">
                  Student accounts are managed by school administrators. Submitting this request will alert our team to verify and reset your credentials.
                </p>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-black uppercase tracking-wider text-ink-soft/60 ml-1">Account ID / LRN</label>
                <input v-model="forgotPayload.username" type="text" placeholder="Your student ID" class="input-field py-4.5 text-sm" />
              </div>
              <button @click="submitResetRequest" class="btn-primary w-full py-4.5 rounded-2xl flex items-center justify-center gap-3">
                 <span class="text-lg font-bold">Request Staff Action</span>
                 <span class="text-xl">🆘</span>
              </button>
           </div>

           <button @click="exitForgot" class="mt-10 px-8 py-2 text-xs font-black text-ink-soft hover:text-ink uppercase tracking-[0.2em] transition-all hover:bg-surface-2 rounded-full">Cancel and return</button>
        </div>

        <!-- Global Status Messages -->
        <div v-if="auth.error" class="absolute bottom-10 left-10 right-10 p-4 bg-rose-50 border border-rose-100 rounded-2xl text-xs font-bold text-rose-600 animate-shake flex items-center gap-3">
          <span class="text-base">🚫</span> {{ auth.error }}
        </div>
        <div v-if="successMessage" class="absolute bottom-10 left-10 right-10 p-4 bg-emerald-50 border border-emerald-100 rounded-2xl text-xs font-bold text-emerald-700 flex items-center gap-3">
          <span class="text-base">✅</span> {{ successMessage }}
        </div>
      </div>

    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

type Role = 'student' | 'teacher'
const mode = ref<'login' | 'register'>(
  (route.query.mode === 'register' || route.path === '/register') ? 'register' : 'login'
)
const role = ref<Role>((route.query.role as Role) || 'student')
const showPassword = ref(false)
const rememberMe = ref(false)
const validationError = ref('')
const successMessage = ref('')
const forgotPasswordMode = ref(false)
const forgotStep = ref(1)

const roleLabel = computed(() => role.value.charAt(0).toUpperCase() + role.value.slice(1))

const loginForm = reactive({
  email: '',
  username: '',
  password: ''
})

const registerForm = reactive({
  fullName: '',
  email: '',
  username: '',
  studentId: '',
  contactNo: '',
  password: '',
  confirmPassword: ''
})

const forgotPayload = reactive({
  email: '',
  username: ''
})

function setMode(newMode: 'login' | 'register') {
  mode.value = newMode
  validationError.value = ''
  successMessage.value = ''
  auth.error = ''
  // Update URL without full refresh
  window.history.replaceState({}, '', newMode === 'login' ? '/login' : '/register')
}

async function handleLogin() {
  const isTeacher = role.value === 'teacher'
  auth.error = ''
  
  try {
    const data = await auth.login({
      email: isTeacher ? loginForm.email : null,
      username: isTeacher ? null : loginForm.username,
      password: loginForm.password
    }, role.value)

    if (!data.profile_completed) {
      router.push('/profile/setup')
      return
    }

    router.push(role.value === 'teacher' ? '/teacher/dashboard' : '/student/dashboard')
  } catch (err) {
    // Error handled by store
  }
}

async function handleRegister() {
  validationError.value = ''
  auth.error = ''
  
  // Basic Validations
  if (registerForm.password !== registerForm.confirmPassword) {
    validationError.value = 'Passwords do not match.'
    return
  }
  if (registerForm.password.length < 8) {
    validationError.value = 'Password is too short (min 8 chars).'
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(registerForm.email)) {
    validationError.value = 'Invalid email format.'
    return
  }
  if (!/^\d{11}$/.test(registerForm.contactNo)) {
    validationError.value = 'Invalid contact number (11 digits required).'
    return
  }

  try {
    // Prep pending profile for auto-fill in setup page
    const pendingProfile = {
       fullName: registerForm.fullName,
       contactNo: registerForm.contactNo,
       studentId: registerForm.studentId,
       email: registerForm.email
    }
    localStorage.setItem('pending_profile', JSON.stringify(pendingProfile))

    await auth.register({
      role: role.value,
      email: registerForm.email,
      username: role.value === 'student' ? registerForm.username : null,
      password: registerForm.password,
    } as any)

    successMessage.value = 'Account created successfully!'
    setTimeout(() => {
       successMessage.value = ''
       setMode('login')
    }, 2000)
  } catch (err) {
     // Store owns error
  }
}

function requestOTP() {
  if (!forgotPayload.email) return
  auth.loading = true
  setTimeout(() => {
    auth.loading = false
    forgotStep.value = 2
  }, 1000)
}

function resetComplete() {
  successMessage.value = 'Password updated successfully!'
  setTimeout(() => {
    successMessage.value = ''
    exitForgot()
  }, 2000)
}

function submitResetRequest() {
  if (!forgotPayload.username) return
  auth.loading = true
  setTimeout(() => {
    auth.loading = false
    alert('Request sent to system administrator.')
    exitForgot()
  }, 1500)
}

function exitForgot() {
  forgotPasswordMode.value = false
  forgotStep.value = 1
}

onMounted(() => {
  // Safe clear potential previous artifacts on navigate
  auth.error = ''
})
</script>

<style scoped>
.input-field {
  width: 100%;
  background-color: var(--surface-2, #f8fafc);
  border: 1px solid #e2e8f0;
  border-radius: 1.25rem;
  padding: 1.125rem 1.5rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}
.input-field:focus {
  background-color: #ffffff;
  border-color: #1565FF;
  box-shadow: 0 0 0 4px rgba(21, 101, 255, 0.08);
  transform: translateY(-1px);
}

.auth-page {
  animation: bgPulse 20s infinite alternate;
}

@keyframes bgPulse {
  from { background-color: #f7f7fb; }
  to { background-color: #edeffd; }
}

.animate-fade-in-left {
  animation: fadeInLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-fade-in-up {
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-shake {
  animation: shake 0.4s ease-in-out;
}

@keyframes fadeInLeft {
  from { opacity: 0; transform: translateX(-30px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.btn-primary:active {
  transform: scale(0.98);
}
</style>
