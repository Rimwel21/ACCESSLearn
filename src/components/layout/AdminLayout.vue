<template>
  <div class="flex h-screen overflow-hidden bg-surface">
    <aside class="z-10 flex w-[200px] min-w-[200px] flex-col border-r border-gray-100 bg-white shadow-sm">
      <div class="border-b border-gray-100 bg-brand-blue-soft px-5 py-5">
        <div class="font-display text-2xl font-bold tracking-tight text-brand-blue">Learnify</div>
        <div class="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-soft">LMS Admin</div>
      </div>

      <div class="mx-3 my-3 flex items-center gap-2.5 rounded-xl bg-brand-blue-soft p-3 text-left">
        <div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-blue to-brand-violet text-base font-bold text-white">
          A
        </div>
        <div class="min-w-0">
          <div class="truncate text-[13px] font-semibold text-ink">Administrator</div>
          <div class="truncate text-[10px] text-ink-soft">{{ auth.accountIdentity }}</div>
        </div>
      </div>

      <nav class="flex-1 px-2.5 py-1" aria-label="Admin navigation">
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
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { to: '/admin/dashboard', label: 'Admin Dashboard', iconClass: 'rounded-full' },
]

const titleMap: Record<string, string> = {
  AdminDashboard: 'Admin Dashboard',
}

const currentTitle = computed(() => titleMap[route.name as string] ?? 'Learnify LMS Admin')

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<style scoped>
.page-enter-active, .page-leave-active { transition: opacity .2s, transform .2s; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
