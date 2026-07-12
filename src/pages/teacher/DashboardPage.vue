<template>
  <div class="space-y-6">
    <!-- Hero -->
    <div class="relative gradient-brand rounded-2xl p-8 flex items-center justify-between overflow-hidden">
      <div class="absolute inset-0 opacity-5" style="background-image:radial-gradient(circle,#fff 1px,transparent 1px);background-size:28px 28px;" />
      <div class="relative z-10">
        <h1 class="font-display text-3xl font-bold text-white leading-tight mb-2">Welcome, {{ store.teacherName }}! 👋</h1>
        <p class="text-white/75 text-sm max-w-sm leading-relaxed">Let's start the day by learning something new. You have {{ store.atRiskStudents.length }} students that may need attention.</p>
        <RouterLink to="/teacher/class" class="mt-4 inline-block px-5 py-2 rounded-full border border-white/40 bg-white/20 backdrop-blur-sm text-white text-sm font-semibold hover:bg-white/30 transition-all">
          View Class Management →
        </RouterLink>
      </div>
      <div class="text-[80px] relative z-10" style="animation: float 4s ease-in-out infinite;">👩‍🏫</div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4">
      <div class="card-hover p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-blue" />
        <div class="w-10 h-10 rounded-xl bg-brand-blue-soft flex items-center justify-center text-lg mb-3">👥</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">48</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Total Students</div>
        <div class="text-[11px] font-mono mt-2 text-brand-green">↑ +3 this week</div>
      </div>
      <div class="card-hover p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-violet" />
        <div class="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center text-lg mb-3">📘</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">{{ store.publishedModules.length }}</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Active Modules</div>
        <div class="text-[11px] font-mono mt-2 text-brand-green">↑ 2 new added</div>
      </div>
      <div class="card-hover p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-teal" />
        <div class="w-10 h-10 rounded-xl bg-cyan-100 flex items-center justify-center text-lg mb-3">📝</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">87%</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Avg. Quiz Score</div>
        <div class="text-[11px] font-mono mt-2 text-brand-green">↑ +4% vs last</div>
      </div>
      <div class="card-hover p-5 relative overflow-hidden">
        <div class="absolute w-20 h-20 rounded-full -top-5 -right-5 opacity-10 bg-brand-rose" />
        <div class="w-10 h-10 rounded-xl bg-rose-100 flex items-center justify-center text-lg mb-3">⏳</div>
        <div class="font-display text-3xl font-bold leading-none mb-1">3</div>
        <div class="text-[12.5px] text-ink-soft font-medium">Pending Reviews</div>
        <div class="text-[11px] font-mono mt-2 text-brand-rose">↓ Due today</div>
      </div>
    </div>

    <!-- Lower grid -->
    <div class="grid grid-cols-[1fr_240px] gap-5">

      <!-- Student Progress -->
      <div class="card">
        <div class="px-5 py-4 border-b border-gray-50 flex items-center justify-between">
          <span class="font-display font-semibold text-base">Student Progress</span>
          <RouterLink to="/teacher/class" class="text-xs font-semibold text-brand-blue bg-brand-blue-soft px-3 py-1.5 rounded-full hover:bg-brand-blue hover:text-white transition-all">See All</RouterLink>
        </div>
        <table class="w-full border-collapse">
          <thead>
            <tr>
              <th class="table-th">Student</th>
              <th class="table-th">Overall Progress</th>
              <th class="table-th">Activity</th>
              <th class="table-th">Last Activity</th>
              <th class="table-th">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in store.students" :key="s.studentId" class="hover:bg-gray-50 transition-colors">
              <td class="table-td">
                <div class="flex items-center gap-2.5">
                  <div :class="`w-8 h-8 rounded-full bg-gradient-to-br ${s.avatarGradient} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`">{{ s.initials }}</div>
                  <span class="text-[13px] font-medium">{{ s.studentName }}</span>
                </div>
              </td>
              <td class="table-td w-40">
                <div class="flex items-center gap-2.5">
                  <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div :class="progressGradient(s.status)" class="h-full rounded-full transition-all" :style="{ width: s.overallPercent + '%' }" />
                  </div>
                  <span class="font-mono text-[11px] text-ink-soft min-w-[34px] text-right">{{ s.overallPercent }}%</span>
                </div>
              </td>
              <td class="table-td font-mono text-xs">{{ s.activitiesCompleted }}/{{ s.activitiesTotal }}</td>
              <td class="table-td font-mono text-xs">{{ s.lastActivity }}</td>
              <td class="table-td"><span :class="statusBadge(s.status)">{{ s.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Right panel -->
      <div class="flex flex-col gap-4">
        <div class="card">
          <div class="px-4 pt-4 pb-3 border-b border-gray-50 font-display font-semibold text-[13px]">📅 September 2025</div>
          <div class="p-3">
            <div class="flex justify-between items-center mb-2.5">
              <span class="font-display text-xs font-semibold">Sep 2025</span>
              <div class="flex gap-1">
                <button class="w-5 h-5 rounded hover:bg-surface-2 text-ink-soft text-xs transition-colors">‹</button>
                <button class="w-5 h-5 rounded hover:bg-surface-2 text-ink-soft text-xs transition-colors">›</button>
              </div>
            </div>
            <div class="grid grid-cols-7 gap-0.5 text-center">
              <div v-for="d in ['M','T','W','T','F','S','S']" :key="d" class="text-[8px] font-semibold text-ink-soft py-1">{{ d }}</div>
              <div v-for="day in 30" :key="day"
                :class="['text-[10px] py-1.5 rounded-md cursor-pointer font-mono transition-colors',
                  day === 10 ? 'bg-brand-blue text-white font-bold' :
                  [11,12,16].includes(day) ? 'relative after:absolute after:bottom-0.5 after:left-1/2 after:-translate-x-1/2 after:w-1 after:h-1 after:rounded-full after:bg-brand-rose hover:bg-surface-2' :
                  'hover:bg-brand-blue-soft text-ink'
                ]"
              >{{ day }}</div>
            </div>
          </div>
        </div>

        <div class="card flex-1">
          <div class="px-4 pt-4 pb-3 border-b border-gray-50 font-display font-semibold text-[13px]">Recent Activity</div>
          <div class="p-4 flex flex-col gap-3">
            <div v-for="act in store.recentActivities" :key="act.text" class="flex items-start gap-2.5">
              <div :class="`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${act.color}`" />
              <div>
                <div class="text-xs leading-relaxed text-ink-soft">{{ act.text }}</div>
                <div class="text-[10px] font-mono text-gray-400 mt-0.5">{{ act.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useTeacherStore } from '@/stores/teacher'
const store = useTeacherStore()

function progressGradient(status: string) {
  if (status === 'Complete')    return 'bg-gradient-to-r from-brand-teal to-brand-green'
  if (status === 'Needs Help')  return 'bg-gradient-to-r from-brand-rose to-orange-400'
  return 'bg-gradient-to-r from-brand-blue to-brand-violet'
}
function statusBadge(status: string) {
  if (status === 'Complete')   return 'badge badge-green'
  if (status === 'Needs Help') return 'badge badge-red'
  return 'badge badge-blue'
}
</script>

<style>
@keyframes float {
  0%,100% { transform: translateY(0) rotate(-3deg); }
  50%      { transform: translateY(-10px) rotate(3deg); }
}
</style>
