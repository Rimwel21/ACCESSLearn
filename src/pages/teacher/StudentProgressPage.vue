<template>
  <div class="space-y-5">
    <div class="flex items-end justify-between">
      <div>
        <nav class="flex items-center gap-1.5 text-xs font-mono mb-1">
          <span @click="router.push('/teacher/class')" class="text-ink-soft hover:text-brand-blue cursor-pointer transition-colors">Class Management</span>
          <span class="text-gray-300">›</span>
          <span class="text-ink font-semibold">Student Progress</span>
        </nav>
        <h2 class="font-display text-2xl font-bold">📊 Student Progress</h2>
      </div>
      <button class="btn-primary">📤 Export Report</button>
    </div>

    <div class="gradient-teal rounded-xl px-6 py-3.5">
      <p class="text-white text-sm">Monitor individual and class-wide learning progress</p>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div class="card p-5 flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-cyan-100 flex items-center justify-center text-xl">👥</div>
        <div><div class="font-display text-2xl font-bold">{{ store.students.length }}</div><div class="text-xs text-ink-soft font-medium">Total Students</div></div>
      </div>
      <div class="card p-5 flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-emerald-100 flex items-center justify-center text-xl">🏆</div>
        <div><div class="font-display text-2xl font-bold">{{ store.students.filter(s => s.status === 'Complete').length }}</div><div class="text-xs text-ink-soft font-medium">Passed</div></div>
      </div>
      <div class="card p-5 flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-rose-100 flex items-center justify-center text-xl">⚠️</div>
        <div><div class="font-display text-2xl font-bold">{{ store.atRiskStudents.length }}</div><div class="text-xs text-ink-soft font-medium">Needs Help</div></div>
      </div>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full border-collapse">
        <thead>
          <tr>
            <th class="table-th">Student</th>
            <th class="table-th">Overall Progress</th>
            <th class="table-th">Activity</th>
            <th class="table-th">Last Activity</th>
            <th class="table-th">Actions</th>
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
            <td class="table-td w-44">
              <div class="flex items-center gap-2.5">
                <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div :class="progressGradient(s.status)" class="h-full rounded-full transition-all" :style="{ width: s.overallPercent + '%' }" />
                </div>
                <span class="font-mono text-[11px] text-ink-soft min-w-[36px] text-right">{{ s.overallPercent }}%</span>
              </div>
            </td>
            <td class="table-td font-mono text-xs">{{ s.activitiesCompleted }}/{{ s.activitiesTotal }}</td>
            <td class="table-td font-mono text-xs">{{ s.lastActivity }}</td>
            <td class="table-td">
              <span :class="statusBadge(s.status)">{{ s.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useTeacherStore } from '@/stores/teacher'

const router = useRouter()
const store  = useTeacherStore()

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
