<template>
  <div class="min-h-screen bg-white">
    <div class="space-y-5 px-5 py-5 xl:px-7">
      <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_250px]">
        <div class="flex min-w-0 items-center gap-2 border-[3px] border-black bg-white px-4 py-2.5" style="box-shadow:4px 4px 0 #000">
          <input v-model="search" type="text" placeholder="Search" class="min-w-0 flex-1 border-0 bg-transparent text-sm font-bold text-gray-700 outline-none" />
          <span class="text-xs font-black text-gray-500">SEARCH</span>
        </div>

        <div class="flex items-center justify-end gap-3">
          <button
            class="grid h-[42px] w-[42px] place-items-center border-[3px] border-black bg-white text-[10px] font-black transition-all hover:-translate-x-[1px] hover:-translate-y-[1px]"
            style="box-shadow:3px 3px 0 #000"
            type="button"
            aria-label="Open profile setup"
            @click="router.push('/profile/setup')"
          >
            PR
          </button>
          <button
            class="grid h-[42px] w-[42px] place-items-center border-[3px] border-black bg-white text-[10px] font-black transition-all hover:-translate-x-[1px] hover:-translate-y-[1px]"
            style="box-shadow:3px 3px 0 #000"
            type="button"
            aria-label="Logout"
            @click="logout"
          >
            OUT
          </button>

          <div class="relative">
            <button
              class="grid h-[42px] w-[42px] place-items-center overflow-hidden rounded-full border-[3px] border-black bg-white font-black"
              style="box-shadow:3px 3px 0 #000"
              aria-label="Open student profile"
              @click="showProfileMenu = !showProfileMenu"
            >
              <img v-if="profile.image?.file_url" :src="profile.image.file_url" alt="" class="h-full w-full object-cover" />
              <span v-else>{{ profile.initial }}</span>
            </button>

            <div v-if="showProfileMenu" class="absolute right-0 top-12 z-40 w-72 border-[3px] border-black bg-white p-4 text-left" style="box-shadow:5px 5px 0 #000">
              <div class="flex items-center gap-3 border-b-[3px] border-black pb-3">
                <img v-if="profile.image?.file_url" :src="profile.image.file_url" alt="" class="h-12 w-12 rounded-full border-[2px] border-black object-cover" />
                <div v-else class="grid h-12 w-12 place-items-center rounded-full border-[2px] border-black bg-[#1565FF] font-black text-white">{{ profile.initial }}</div>
                <div class="min-w-0">
                  <div class="truncate font-black">{{ profile.displayName }}</div>
                  <div class="truncate font-mono text-[10px] text-gray-500">{{ auth.accountIdentity || 'Student account' }}</div>
                </div>
              </div>
              <dl class="mt-3 grid gap-2 text-xs">
                <div class="flex justify-between gap-3"><dt class="font-black text-gray-500">Role</dt><dd class="font-bold">Student</dd></div>
                <div class="flex justify-between gap-3"><dt class="font-black text-gray-500">Email</dt><dd class="truncate font-bold">{{ studentEmail }}</dd></div>
                <div class="flex justify-between gap-3"><dt class="font-black text-gray-500">Type</dt><dd class="truncate font-bold">{{ studentType }}</dd></div>
              </dl>
              <div class="mt-4 grid grid-cols-2 gap-2">
                <button class="border-[2px] border-black bg-[#FFE135] px-3 py-2 text-xs font-black" @click="router.push('/profile/setup')">Profile</button>
                <button class="border-[2px] border-black bg-white px-3 py-2 text-xs font-black" @click="logout">Logout</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_250px]">
        <div class="min-w-0 space-y-6">
          <section class="border-[3px] border-black bg-[#1565FF] px-6 py-5" style="box-shadow:5px 5px 0 #000">
            <div class="flex min-h-[88px] items-center">
              <div>
                <h1 class="font-display text-[28px] font-black leading-tight text-white md:text-[32px]">Welcome, {{ store.studentName }}!</h1>
                <p class="font-mono text-[11px] tracking-widest text-white">READY TO STUDY?</p>
              </div>
            </div>
          </section>

          <section>
            <div class="mb-4 flex items-center gap-3">
              <h2 class="font-display text-sm font-black uppercase tracking-widest">Modules</h2>
              <div class="h-[2.5px] flex-1 bg-black" />
            </div>
            <div v-if="content.loading" class="border-[3px] border-black bg-white p-6 text-sm font-black" style="box-shadow:4px 4px 0 #000">Loading modules...</div>
            <div v-else-if="filteredModules.length === 0" class="border-[3px] border-black bg-white p-8 text-center" style="box-shadow:4px 4px 0 #000">
              <h3 class="font-display text-lg font-black">No learning materials are available yet.</h3>
              <p class="mt-2 text-sm text-gray-500">Published teacher uploads will appear here automatically.</p>
            </div>
            <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <article
                v-for="module in filteredModules.slice(0, 4)"
                :key="module.id"
                class="cursor-pointer overflow-hidden border-[3px] border-black transition-all hover:-translate-x-[3px] hover:-translate-y-[3px]"
                style="box-shadow:5px 5px 0 #000"
                @click="router.push(`/student/modules/${module.id}`)"
              >
                <div class="flex h-[96px] items-center justify-center bg-[#FFE135] text-sm font-black uppercase tracking-widest">Module</div>
                <div class="border-t-[3px] border-black bg-white p-2.5">
                  <div class="truncate font-display text-[11px] font-black uppercase tracking-wide">{{ module.title }}</div>
                  <div class="mt-0.5 truncate font-mono text-[9px] text-gray-500">{{ module.topics.length }} topics | {{ module.file_name || 'Learning material' }}</div>
                </div>
              </article>
            </div>
          </section>

          <section>
            <div class="mb-4 flex items-center gap-3">
              <h2 class="font-display text-sm font-black uppercase tracking-widest">Continue Progress</h2>
              <div class="h-[2.5px] flex-1 bg-black" />
            </div>
            <div v-if="content.modules.length === 0" class="border-[3px] border-black bg-white p-6 text-sm font-black" style="box-shadow:4px 4px 0 #000">Start a module to track your progress here.</div>
            <div v-else class="space-y-3">
              <article v-for="module in content.modules.slice(0, 3)" :key="module.id" class="flex flex-wrap items-center gap-4 border-[3px] border-black bg-white p-4 sm:flex-nowrap" style="box-shadow:5px 5px 0 #000">
                <div class="flex h-11 w-11 flex-shrink-0 items-center justify-center border-[3px] border-black bg-[#D6E4FF] text-xs font-black">LM</div>
                <div class="min-w-[180px] flex-1">
                  <div class="text-[15px] font-black">{{ module.title }}</div>
                  <div class="mt-0.5 truncate font-mono text-[10px] text-gray-500">{{ module.description }}</div>
                  <div class="mt-2 flex items-center gap-2.5">
                    <div class="h-[11px] flex-1 overflow-hidden border-[2px] border-black bg-[#e8e8e8]">
                      <div class="h-full bg-[#1565FF]" :style="{ width: `${content.progressByModule[module.id]?.percent ?? 0}%` }" />
                    </div>
                    <span class="whitespace-nowrap font-mono text-[10px] font-bold text-gray-700">{{ content.progressByModule[module.id]?.percent ?? 0 }}%</span>
                  </div>
                </div>
                <button class="ml-auto flex-shrink-0 border-[3px] border-black bg-[#1565FF] px-4 py-2.5 text-[12px] font-black text-white transition-all hover:-translate-x-[2px] hover:-translate-y-[2px]" style="box-shadow:3px 3px 0 #000" @click="router.push(`/student/modules/${module.id}`)">RESUME</button>
              </article>
            </div>
          </section>
        </div>

        <aside class="grid gap-5 lg:block lg:space-y-5">
          <section class="border-[3px] border-black bg-white" style="box-shadow:5px 5px 0 #000">
            <div class="flex items-center justify-between border-b-[3px] border-black bg-[#FFE135] px-3 py-2">
              <button class="font-black" type="button" @click="calendarOffset -= 1">&lt;</button>
              <div class="text-center">
                <div class="font-display text-sm font-black">{{ calendarTitle }}</div>
                <div class="font-mono text-[9px] uppercase tracking-widest text-gray-600">{{ calendarYear }}</div>
              </div>
              <button class="font-black" type="button" @click="calendarOffset += 1">&gt;</button>
            </div>
            <div class="grid grid-cols-7 gap-1 p-3 text-center font-mono text-[10px]">
              <div v-for="day in weekDays" :key="day" class="font-black text-gray-500">{{ day }}</div>
              <div v-for="blank in calendarLeadingBlanks" :key="`blank-${blank}`" />
              <div
                v-for="day in calendarDays"
                :key="day"
                :class="['grid h-7 place-items-center border border-transparent font-bold', isToday(day) ? 'border-black bg-[#1565FF] text-white' : 'text-gray-700']"
              >
                {{ day }}
              </div>
            </div>
          </section>

          <section class="min-h-[220px] border-[3px] border-black bg-white" style="box-shadow:5px 5px 0 #000">
            <div class="border-b-[3px] border-black bg-[#1565FF] px-4 py-3">
              <h2 class="font-display text-sm font-black uppercase tracking-widest text-white">Upcoming Deadlines</h2>
            </div>
            <div class="space-y-3 p-4">
              <div v-for="deadline in store.deadlines" :key="`${deadline.title}-${deadline.date}`" class="border-[2px] border-black bg-white p-3">
                <div class="text-xs font-black">{{ deadline.title }}</div>
                <div class="mt-1 font-mono text-[10px] font-bold text-gray-500">{{ deadline.date }}</div>
              </div>
              <div v-if="store.deadlines.length === 0" class="text-xs font-bold text-gray-500">No deadlines yet.</div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useStudentContentStore } from '@/stores/studentContent'

const router = useRouter()
const store = useAppStore()
const auth = useAuthStore()
const profile = useProfileStore()
const content = useStudentContentStore()
const showProfileMenu = ref(false)
const search = ref('')
const calendarOffset = ref(0)

const weekDays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
const viewedDate = computed(() => {
  const date = new Date()
  date.setMonth(date.getMonth() + calendarOffset.value)
  return date
})
const calendarTitle = computed(() => viewedDate.value.toLocaleString('default', { month: 'long' }))
const calendarYear = computed(() => viewedDate.value.getFullYear())
const calendarDays = computed(() => new Date(calendarYear.value, viewedDate.value.getMonth() + 1, 0).getDate())
const calendarLeadingBlanks = computed(() => new Date(calendarYear.value, viewedDate.value.getMonth(), 1).getDay())

const studentEmail = computed(() => auth.accountIdentity.includes('@') ? auth.accountIdentity : 'Not provided')
const studentType = computed(() => {
  const data = profile.profile
  return data && 'student_type' in data ? data.student_type : 'Not provided'
})
const filteredModules = computed(() => content.modules.filter(module =>
  !search.value || module.title.toLowerCase().includes(search.value.toLowerCase())
))

onMounted(() => {
  content.fetchModules()
})

function isToday(day: number) {
  const today = new Date()
  return day === today.getDate()
    && viewedDate.value.getMonth() === today.getMonth()
    && calendarYear.value === today.getFullYear()
}

function logout() {
  auth.logout()
  profile.clear()
  router.push('/')
}
</script>
