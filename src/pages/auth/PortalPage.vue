<template>
  <div class="min-h-screen bg-[#f2f4f8] font-body flex flex-col">

    <!-- Top Navbar -->
    <header class="bg-white border-b border-gray-100 px-5 sm:px-8 py-3.5 flex items-center justify-between shadow-[0_1px_12px_rgba(0,0,0,0.04)]">
      <div class="flex items-center gap-3 group">
        <!-- Triple-click the AL badge to access admin login -->
        <div
          class="h-9 w-9 rounded-full bg-brand-blue flex items-center justify-center font-black text-white text-sm shadow-md group-hover:scale-105 transition-transform cursor-pointer select-none"
          @click="handleLogoClick"
          title="ACCESSLearn"
        >AL</div>
        <RouterLink to="/" class="leading-none">
          <p class="font-display font-bold text-sm text-ink">ACCESSLearn</p>
          <p class="text-[9px] font-extrabold text-brand-blue uppercase tracking-widest">Inclusive E-Learning</p>
        </RouterLink>
      </div>
      <RouterLink to="/" class="flex items-center gap-1.5 text-xs font-bold text-ink-soft hover:text-ink transition-colors group">
        <svg class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
        </svg>
        Back to Home
      </RouterLink>
    </header>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col items-center justify-center px-4 py-10 sm:py-14">

      <!-- Heading -->
      <div class="text-center mb-10">
        <h1 class="font-display font-extrabold text-[2.4rem] sm:text-5xl text-ink leading-[1.15] tracking-tight">
          Find the right
        </h1>
        <h2 class="font-display font-extrabold text-[2.4rem] sm:text-5xl text-brand-blue leading-[1.15] tracking-tight mb-5">
          Student or Teacher flow
        </h2>
        <p class="text-sm text-ink-soft font-medium max-w-sm sm:max-w-md mx-auto leading-relaxed">
          Choose the right path for your role to register or log in with the correct access options.
        </p>
      </div>

      <!-- Role Cards -->
      <div class="w-full max-w-[860px] px-2">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">

          <!-- Student Card -->
          <article class="bg-white rounded-3xl p-7 sm:p-8 border border-blue-100 shadow-[0_4px_24px_rgba(21,101,255,0.07)] relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
            <div class="absolute top-0 left-0 w-[3px] h-full bg-brand-blue rounded-l-3xl"></div>

            <div class="h-14 w-14 bg-gray-50 rounded-2xl flex items-center justify-center text-3xl mb-5 shadow-sm border border-gray-100">🎒</div>

            <p class="text-[10px] font-black text-brand-blue uppercase tracking-[0.22em] mb-2">Student Access</p>
            <h3 class="font-display text-[1.4rem] font-bold text-ink leading-snug mb-2">Join lessons and activities</h3>
            <p class="text-xs text-ink-soft font-medium leading-relaxed mb-7">
              Register or sign in to begin inclusive learning, audio support, and adaptive quizzes.
            </p>

            <div class="flex flex-wrap gap-3">
              <RouterLink
                to="/register?role=student"
                id="student-register-btn"
                class="bg-brand-blue hover:bg-blue-700 text-white px-6 py-2.5 rounded-full font-bold text-sm shadow-md shadow-blue-500/20 transition-all hover:scale-105 active:scale-95">
                Student Register
              </RouterLink>
              <RouterLink
                to="/login?role=student"
                id="student-login-btn"
                class="bg-white text-ink border-2 border-gray-200 hover:border-brand-blue hover:text-brand-blue px-6 py-2.5 rounded-full font-bold text-sm transition-all hover:scale-105 active:scale-95">
                Student Login
              </RouterLink>
            </div>
          </article>

          <!-- Teacher Card -->
          <article class="bg-amber-50 rounded-3xl p-7 sm:p-8 border border-amber-100 shadow-[0_4px_24px_rgba(245,158,11,0.08)] relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
            <div class="absolute top-0 left-0 w-[3px] h-full bg-amber-500 rounded-l-3xl"></div>

            <div class="h-14 w-14 bg-white rounded-2xl flex items-center justify-center text-3xl mb-5 shadow-sm border border-amber-100">👩‍🏫</div>

            <p class="text-[10px] font-black text-amber-600 uppercase tracking-[0.22em] mb-2">Teacher Access</p>
            <h3 class="font-display text-[1.4rem] font-bold text-ink leading-snug mb-2">Manage your classroom</h3>
            <p class="text-xs text-ink-soft font-medium leading-relaxed mb-7">
              Create your teacher account or sign in to track lessons, students, and classroom progress.
            </p>

            <div class="flex flex-wrap gap-3">
              <RouterLink
                to="/register?role=teacher"
                id="teacher-register-btn"
                class="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2.5 rounded-full font-bold text-sm shadow-md shadow-amber-500/20 transition-all hover:scale-105 active:scale-95">
                Teacher Register
              </RouterLink>
              <RouterLink
                to="/login?role=teacher"
                id="teacher-login-btn"
                class="bg-white text-ink border-2 border-amber-200 hover:border-amber-500 hover:text-amber-600 px-6 py-2.5 rounded-full font-bold text-sm transition-all hover:scale-105 active:scale-95">
                Teacher Login
              </RouterLink>
            </div>
          </article>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()

// Triple-click the AL badge to secretly access admin login
const logoClickCount = ref(0)
let logoClickTimer: ReturnType<typeof setTimeout> | null = null

function handleLogoClick() {
  logoClickCount.value++
  if (logoClickTimer) clearTimeout(logoClickTimer)

  if (logoClickCount.value >= 3) {
    logoClickCount.value = 0
    router.push('/admin/login')
    return
  }

  logoClickTimer = setTimeout(() => {
    if (logoClickCount.value < 3) router.push('/')
    logoClickCount.value = 0
  }, 400)
}
</script>
