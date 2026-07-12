<template>
  <div class="flex h-screen overflow-hidden bg-white">
    <aside class="flex w-[180px] min-w-[180px] flex-col border-r-[3px] border-black bg-white">
      <div class="border-b-[3px] border-black bg-[#FFE135] px-4 py-3.5">
        <div class="font-display text-2xl font-black leading-none tracking-tight">Learnify</div>
        <div class="mt-0.5 font-mono text-[9px] uppercase tracking-[3px] text-gray-700">LMS</div>
      </div>

      <button class="mx-2.5 mt-3 flex items-center gap-2 border-[2px] border-black bg-gray-50 p-2 text-left" @click="router.push('/profile/setup')">
        <img v-if="profile.image?.file_url" :src="profile.image.file_url" alt="" class="h-9 w-9 rounded-full object-cover" />
        <div v-else class="grid h-9 w-9 place-items-center rounded-full bg-[#1565FF] text-sm font-black text-white">
          {{ profile.initial }}
        </div>
        <div class="min-w-0">
          <div class="truncate text-xs font-black">{{ profile.displayName }}</div>
          <div class="text-[10px] font-bold text-gray-500">Student</div>
        </div>
      </button>

      <nav class="flex-1 px-2.5 py-3" aria-label="Student navigation">
        <button
          v-for="item in navItems"
          :key="item.label"
          type="button"
          @click="item.to ? router.push(item.to) : null"
          :class="[
            'mb-1.5 flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-[13px] font-bold transition-all',
            item.to && route.path === item.to
              ? 'border-[2px] border-black bg-[#1565FF] text-white'
              : item.to
                ? 'text-gray-700 hover:bg-gray-50'
                : 'cursor-default text-gray-400',
          ]"
        >
          <span :class="['h-5 w-5 flex-shrink-0 border-[2px] border-current bg-current/10', item.iconClass]" aria-hidden="true"></span>
          {{ item.label }}
        </button>
      </nav>

      <div class="border-t-[3px] border-black px-4 py-3">
        <button class="w-full border-[2px] border-black bg-white px-3 py-2 text-xs font-bold hover:bg-gray-50" @click="logout">
          Logout
        </button>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <main class="scrollbar-thin flex-1 overflow-y-auto">
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
import { onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()

const navItems = [
  { to: '/student/dashboard', label: 'Home', iconClass: 'rounded-full' },
  { to: '/student/quiz', label: 'Quizzes', iconClass: 'rounded' },
  { to: '/student/activities', label: 'Activities', iconClass: 'rounded-sm' },
]

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
.page-enter-active, .page-leave-active { transition: opacity .18s, transform .18s; }
.page-enter-from { opacity: 0; transform: translateY(6px); }
.page-leave-to { opacity: 0; }
</style>
