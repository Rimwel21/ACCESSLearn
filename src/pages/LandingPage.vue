<template>
  <div class="flex flex-col lg:flex-row min-h-screen bg-white font-body w-full">
    
    <!-- Mobile Header (Visible only on small screens) -->
    <header class="lg:hidden flex items-center justify-between p-4 border-b border-gray-100 bg-white z-50">
      <div class="flex items-center gap-2">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-blue font-sans font-black text-white text-xs">AL</div>
        <span class="font-display text-lg font-bold text-ink">ACCESSLearn</span>
      </div>
      <button @click="isMobileMenuOpen = !isMobileMenuOpen" class="text-gray-500 hover:text-ink">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
      </button>
    </header>

    <!-- Mobile Menu Overlay -->
    <div v-if="isMobileMenuOpen" class="fixed inset-0 bg-white z-40 pt-20 px-6 lg:hidden flex flex-col space-y-3">
       <RouterLink to="/" @click="isMobileMenuOpen=false" class="flex items-center gap-3 px-4 py-3 bg-gray-100 rounded-xl text-ink font-bold">Home</RouterLink>
       <RouterLink to="/portal" @click="isMobileMenuOpen=false" class="flex items-center gap-3 px-4 py-3 rounded-xl text-ink-soft font-bold">Register</RouterLink>
       <RouterLink to="/portal" @click="isMobileMenuOpen=false" class="flex items-center gap-3 px-4 py-3 rounded-xl text-ink-soft font-bold">Log in</RouterLink>
    </div>

    <!-- Sidebar (Desktop) -->
    <aside class="hidden lg:flex w-[260px] bg-white border-r border-gray-100 flex-col justify-between shrink-0 relative z-20 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
      <div>
        <!-- Logo Area -->
        <div class="flex flex-col items-center pt-10 pb-8 px-6 text-center">
          <div class="mb-3 text-brand-blue">
            <svg class="w-20 h-20" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M50 15C38 15 30 25 30 35C30 45 40 50 50 55C60 50 70 45 70 35C70 25 62 15 50 15Z" fill="#FFA726"/>
              <path d="M30 40C20 40 15 48 15 55C15 62 22 68 30 70C35 71 42 68 50 62C58 68 65 71 70 70C78 68 85 62 85 55C85 48 80 40 70 40C64 40 58 43 50 48C42 43 36 40 30 40Z" fill="#29B6F6"/>
              <path d="M50 60C40 68 35 75 35 85H65C65 75 60 68 50 60Z" fill="#1565FF"/>
              <path d="M50 75L10 85V90H90V85L50 75Z" fill="#1A237E"/>
            </svg>
          </div>
          <h1 class="font-display font-black text-2xl text-ink leading-tight">ACCESSLearn</h1>
          <p class="text-[10px] font-bold text-ink-soft mt-1 uppercase tracking-widest">Inclusive Classroom</p>
        </div>

        <!-- Navigation -->
        <nav class="px-4 space-y-2">
          <a href="#" class="flex items-center gap-3 px-4 py-3 bg-gray-100 rounded-xl text-ink font-bold hover:bg-gray-200 transition-colors">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
            Home
          </a>
          <RouterLink to="/portal" class="flex items-center gap-3 px-4 py-3 rounded-xl text-ink-soft font-bold hover:bg-gray-50 hover:text-ink transition-colors">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
            Register
          </RouterLink>
          <RouterLink to="/portal" class="flex items-center gap-3 px-4 py-3 rounded-xl text-ink-soft font-bold hover:bg-gray-50 hover:text-ink transition-colors">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
            Log in
          </RouterLink>
        </nav>
      </div>

      <!-- Bottom illustration -->
      <div class="p-6 opacity-80 pointer-events-none self-center">
        <svg class="w-32 h-auto" viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="80" r="30" stroke="#1565FF" stroke-width="6" stroke-dasharray="6 6"/>
          <path d="M70 120 C 80 145, 120 145, 130 120" stroke="#FFA726" stroke-width="8" stroke-linecap="round"/>
          <circle cx="100" cy="80" r="18" fill="#29B6F6"/>
          <path d="M60 40 L40 60 L60 80" stroke="#4CAF50" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M140 40 L160 60 L140 80" stroke="#9C27B0" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col relative grid-bg h-full lg:overflow-y-auto overflow-x-hidden">
      


      <!-- Content Area -->
      <div class="p-6 lg:px-8 lg:pb-12 w-full max-w-[1300px] mx-auto space-y-6 flex-1 flex flex-col justify-center relative">
        
        <!-- Hero Banner -->
        <div class="relative w-full rounded-[24px] bg-gradient-to-r from-brand-blue to-brand-violet shadow-xl overflow-hidden min-h-[300px] flex flex-col justify-center">
          <!-- Desktop Illustration -->
          <img src="@/assets/hero_illustration.png" alt="Students learning" class="hidden lg:block absolute left-8 bottom-0 w-[42%] max-w-[480px] object-contain drop-shadow-2xl z-10 scale-105 origin-bottom" />
          
          <!-- Banner Content -->
          <div class="relative z-20 text-white w-full px-8 py-10 lg:pl-[48%] lg:pr-12">
            <!-- Mobile Illustration (Shows above text on small screens) -->
            <img src="@/assets/hero_illustration.png" alt="Students learning" class="lg:hidden w-full max-w-[320px] mx-auto object-contain drop-shadow-xl mb-6" />

            <h2 class="font-display text-2xl sm:text-3xl lg:text-3xl xl:text-4xl font-extrabold mb-4 leading-[1.2] w-full text-shadow-sm tracking-tight text-white">
              Learning that adapts to every child, every ability, every classroom.
            </h2>
            <p class="text-white/95 text-[13px] sm:text-sm mb-8 max-w-[500px] font-medium leading-relaxed">
              AccessLearn combines audio lessons, sign-language videos, subtitles, and adaptive quizzes to create equitable learning in Philippine schools.
            </p>
            <div class="flex flex-wrap items-center gap-4">
              <RouterLink to="/portal" class="bg-[#00E676] hover:bg-[#00c853] text-white px-8 py-3 rounded-full font-bold text-sm shadow-lg transition-transform hover:scale-105 text-center flex-1 sm:flex-none">Get Started</RouterLink>
              <a href="#features" class="bg-white hover:bg-gray-50 text-brand-blue px-8 py-3 rounded-full font-bold text-sm shadow-lg transition-transform hover:scale-105 text-center flex-1 sm:flex-none border-0">See Features</a>
            </div>
          </div>
        </div>

        <!-- Feature Cards -->
        <div id="features" class="grid grid-cols-2 lg:grid-cols-5 gap-3 lg:gap-4 relative z-20 xl:-mt-10">
          <!-- Card 1 -->
          <div class="bg-white rounded-2xl p-4 lg:p-5 flex flex-col items-center text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-gray-100/50 hover:-translate-y-1 transition-transform group">
            <div class="text-3xl lg:text-4xl mb-3 h-12 flex items-center justify-center group-hover:scale-110 transition-transform">🧏💬</div>
            <h3 class="font-bold text-ink text-[13px] lg:text-sm mb-2 leading-tight">Sign & Captions</h3>
            <p class="text-[10px] lg:text-[11px] text-ink-soft leading-relaxed font-medium">For hearing support learners.<br/> Each module includes sign‑language videos, subtitles, and transcript toggles.</p>
          </div>
          <!-- Card 2 -->
          <div class="bg-white rounded-2xl p-4 lg:p-5 flex flex-col items-center text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-gray-100/50 hover:-translate-y-1 transition-transform group">
            <div class="text-3xl lg:text-4xl mb-3 h-12 flex items-center justify-center group-hover:scale-110 transition-transform">🎯📚</div>
            <h3 class="font-bold text-ink text-[13px] lg:text-sm mb-2 leading-tight">Adaptive Activities</h3>
            <p class="text-[10px] lg:text-[11px] text-ink-soft leading-relaxed font-medium">Personalized interactive tasks.<br/> Adjust to each learner’s progress, ensuring engagement and mastery of skills.</p>
          </div>
          <!-- Card 3 -->
          <div class="bg-white rounded-2xl p-4 lg:p-5 flex flex-col items-center text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-gray-100/50 hover:-translate-y-1 transition-transform group">
            <div class="text-3xl lg:text-4xl mb-3 h-12 flex items-center justify-center group-hover:scale-110 transition-transform">✅⚙️</div>
            <h3 class="font-bold text-ink text-[13px] lg:text-sm mb-2 leading-tight">Adaptive Quizzes</h3>
            <p class="text-[10px] lg:text-[11px] text-ink-soft leading-relaxed font-medium">Smart assessments.<br/> Adapt difficulty based on performance, guiding learners toward review or advancement.</p>
          </div>
          <!-- Card 4 -->
          <div class="bg-white rounded-2xl p-4 lg:p-5 flex flex-col items-center text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-gray-100/50 hover:-translate-y-1 transition-transform group">
            <div class="text-3xl lg:text-4xl mb-3 h-12 flex items-center justify-center group-hover:scale-110 transition-transform">👩🏫📊</div>
            <h3 class="font-bold text-ink text-[13px] lg:text-sm mb-2 leading-tight">Teacher Dashboard</h3>
            <p class="text-[10px] lg:text-[11px] text-ink-soft leading-relaxed font-medium">Class insights.<br/> Track progress, scores, and upload new inclusive lessons.</p>
          </div>
          <!-- Card 5 -->
          <div class="col-span-2 lg:col-span-1 bg-white rounded-2xl p-4 lg:p-5 flex flex-col items-center text-center shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-gray-100/50 hover:-translate-y-1 transition-transform group">
            <div class="text-3xl lg:text-4xl mb-3 h-12 flex items-center justify-center group-hover:scale-110 transition-transform">☁️💾</div>
            <h3 class="font-bold text-ink text-[13px] lg:text-sm mb-2 leading-tight">Offline‑Ready</h3>
            <p class="text-[10px] lg:text-[11px] text-ink-soft leading-relaxed font-medium">Low bandwidth support.<br/> Download lesson briefs for classrooms with limited connectivity.</p>
          </div>
        </div>


        <!-- Footer -->
        <div class="mt-auto pt-8 pb-4">
          <div class="text-center text-[10px] sm:text-xs font-bold text-gray-400">
            © {{ new Date().getFullYear() }} ACCESSLearn Inc. | Philippine Schools Initiative | WCAG 2.2 Compliant
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const isMobileMenuOpen = ref(false)
</script>

<style scoped>
.grid-bg {
  background-color: #fafbfc;
  background-image: 
    linear-gradient(#e2e8f0 1px, transparent 1px),
    linear-gradient(90deg, #e2e8f0 1px, transparent 1px);
  background-size: 32px 32px;
  background-position: -1px -1px;
}
.text-shadow-sm {
  text-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
</style>
