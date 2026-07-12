<template>
  <div class="flex h-screen overflow-hidden bg-surface">
    <aside class="z-10 flex w-[200px] min-w-[200px] flex-col border-r border-gray-100 bg-white shadow-sm">
      <div class="border-b border-gray-100 bg-brand-blue-soft px-5 py-5">
        <div class="font-display text-2xl font-bold tracking-tight text-brand-blue">Learnify</div>
        <div class="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-soft">LMS</div>
      </div>

      <button class="mx-3 my-3 flex items-center gap-2.5 rounded-xl bg-brand-blue-soft p-3 text-left" @click="router.push('/profile/setup')">
        <img v-if="profile.image?.file_url" :src="profile.image.file_url" alt="" class="h-9 w-9 flex-shrink-0 rounded-full object-cover" />
        <div v-else class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-blue to-brand-violet text-base font-bold text-white">
          {{ profile.initial }}
        </div>
        <div class="min-w-0">
          <div class="truncate text-[13px] font-semibold text-ink">{{ profile.displayName }}</div>
          <div class="text-[11px] text-ink-soft">Instructor</div>
        </div>
      </button>

      <nav class="flex-1 px-2.5 py-1" aria-label="Teacher navigation">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" custom v-slot="{ isActive, navigate }">
          <button
            type="button"
            @click="navigate"
            :class="[
              'mb-0.5 flex w-full items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-left text-[13.5px] font-medium transition-all',
              isActive
                ? 'bg-brand-blue text-white shadow-md shadow-blue-200'
                : 'text-ink-soft hover:bg-surface hover:text-ink',
            ]"
          >
            <span :class="['nav-icon-box', item.iconClass]" aria-hidden="true"></span>
            {{ item.label }}
          </button>
        </RouterLink>
      </nav>

      <div class="border-t border-gray-100 px-4 py-3.5">
        <button class="w-full rounded-lg bg-surface px-3 py-2 text-xs font-bold text-ink-soft transition-all hover:bg-red-50 hover:text-brand-rose" @click="logout">
          Logout
        </button>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header class="flex flex-shrink-0 items-center gap-3.5 border-b border-gray-100 bg-white px-7 py-3.5">
        <span class="font-display text-[18px] font-semibold text-ink">{{ currentTitle }}</span>
        <div class="ml-auto flex items-center gap-2.5">
          <div class="hidden items-center gap-2 rounded-full border border-gray-200 bg-surface px-4 py-2 transition-all focus-within:border-brand-blue focus-within:ring-2 focus-within:ring-blue-100 md:flex md:w-56">
            <span class="text-sm">Search</span>
            <input class="min-w-0 flex-1 border-0 bg-transparent font-body text-sm text-ink outline-none" placeholder="Search..." />
          </div>
          <button class="rounded-full border border-gray-200 bg-surface px-3 py-2 text-xs font-bold transition-all hover:bg-brand-blue-soft" @click="router.push('/profile/setup')">
            Profile
          </button>
        </div>
      </header>

      <main class="scrollbar-thin flex-1 overflow-y-auto p-7">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()

const navItems = [
  { to: '/teacher/dashboard', label: 'Home', iconClass: 'rounded-full' },
  { to: '/teacher/class', label: 'Class Management', iconClass: 'rounded-sm' },
]

const titleMap: Record<string, string> = {
  TeacherDashboard: 'Home',
  ClassManagement: 'Class Management',
  Modules: 'Learning Materials',
  TeacherActivities: 'Activities',
  Quizzes: 'Quizzes / Activities',
}

const currentTitle = computed(() => titleMap[route.name as string] ?? 'Learnify LMS')

onMounted(() => {
  profile.fetchProfile().catch(() => null)
})

function logout() {
  auth.logout()
  profile.clear()
  router.push('/')
}
</script>

<style scoped>
.page-enter-active, .page-leave-active { transition: opacity .2s, transform .2s; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
