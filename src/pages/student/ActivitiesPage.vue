<template>
  <div class="min-h-screen bg-white">
    <div class="border-b-[3px] border-black bg-[#1565FF] px-8 py-6">
      <h1 class="font-display text-[28px] font-black text-white">Activity</h1>
    </div>

    <div class="px-7 py-6">
      <div class="grid items-start gap-5 xl:grid-cols-[1fr_240px]">
        <div>
          <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 class="font-display text-sm font-black uppercase tracking-widest">Assigned Activities</h2>
            <button
              class="border-[3px] border-black bg-white px-4 py-2 text-xs font-black transition-all hover:-translate-x-[1px] hover:-translate-y-[1px]"
              style="box-shadow:3px 3px 0 #000"
              @click="content.fetchActivities()"
            >
              Refresh
            </button>
          </div>

          <div v-if="content.loading" class="border-[3px] border-black bg-white p-6 text-sm font-black" style="box-shadow:4px 4px 0 #000">
            Loading activities...
          </div>
          <div v-else-if="content.error" class="border-[3px] border-black bg-red-50 p-6 text-sm font-black text-red-700" style="box-shadow:4px 4px 0 #000">
            {{ content.error }}
          </div>
          <div v-else-if="activities.length === 0" class="border-[3px] border-black bg-white p-8 text-center" style="box-shadow:4px 4px 0 #000">
            <h2 class="font-display text-lg font-black">No activities assigned yet.</h2>
            <p class="mt-2 text-sm text-gray-500">Activities created by your teacher will appear here when they belong to your enrolled class.</p>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="act in activities"
              :key="act.id"
              class="flex cursor-pointer items-center gap-4 border-[3px] border-black bg-white p-4 transition-all hover:-translate-x-[2px] hover:-translate-y-[2px]"
              style="box-shadow:4px 4px 0 #000"
              @click="openActivity(act)"
            >
              <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center border-[3px] border-black bg-[#D6E4FF] text-xs font-black">
                ACT
              </div>

              <div class="min-w-0 flex-1">
                <div class="text-[14px] font-black">{{ act.title }}</div>
                <div class="mt-0.5 truncate font-mono text-[11px] text-gray-500">{{ act.description }}</div>
                <div class="mt-1 font-mono text-[10px] font-bold text-gray-500">{{ act.category || 'Activity' }}</div>
              </div>

              <div class="flex-shrink-0 text-right">
                <div class="font-mono text-[11px] font-bold text-gray-700">{{ act.category || 'Activity' }}</div>
                <div class="font-mono text-[10px] text-gray-500">{{ act.timeLimit || 'No time limit' }}</div>
              </div>

              <span :class="['flex-shrink-0 border-[2px] border-black px-2.5 py-1.5 font-mono text-[10px] font-black', statusStyle(act.status)]">
                {{ act.status }}
              </span>

              <span class="flex-shrink-0 text-lg font-black">&gt;</span>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="border-[3px] border-black bg-white" style="box-shadow:5px 5px 0 #000">
            <div class="border-b-[3px] border-black bg-[#1565FF] px-3.5 py-2.5">
              <span class="font-display text-[12px] font-black uppercase tracking-wide text-white">In Progress</span>
            </div>
            <div class="space-y-2 p-3">
              <div v-if="inProgress.length === 0" class="text-xs font-bold text-gray-500">No activities in progress.</div>
              <button
                v-for="act in inProgress"
                :key="`progress-${act.id}`"
                class="block w-full truncate border-[2px] border-black bg-white px-2 py-1.5 text-left text-[11px] font-black hover:bg-[#D6E4FF]"
                @click="openActivity(act)"
              >
                {{ act.title }}
              </button>
            </div>
          </div>

          <div class="border-[3px] border-black bg-white" style="box-shadow:5px 5px 0 #000">
            <div class="border-b-[3px] border-black bg-[#1565FF] px-3.5 py-2.5">
              <span class="font-display text-[12px] font-black uppercase tracking-wide text-white">Assigned</span>
            </div>
            <div class="p-3 text-xs font-bold text-gray-600">
              {{ activities.length }} activity{{ activities.length === 1 ? '' : 'ies' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentContentStore } from '@/stores/studentContent'

type ActivityStatus = 'In Progress' | 'Not Started' | 'Finished'

interface ActivityRow {
  id: number
  title: string
  description: string
  category?: string | null
  timeLimit?: string | null
  status: ActivityStatus
}

const router = useRouter()
const content = useStudentContentStore()

const activities = computed<ActivityRow[]>(() => content.activities.map(assessment => ({
  id: assessment.id,
  title: assessment.title,
  description: assessment.description,
  category: assessment.category,
  timeLimit: assessment.time_limit,
  status: 'Not Started',
})))

const inProgress = computed(() => activities.value.filter(activity => activity.status === 'In Progress'))

onMounted(() => {
  content.fetchActivities()
})

function openActivity(activity: ActivityRow) {
  router.push({
    name: 'HandSignLanguage',
    query: {
      activityId: String(activity.id),
    },
  })
}

function statusStyle(status: ActivityStatus) {
  switch (status) {
    case 'In Progress': return 'bg-[#FFE135] text-black'
    case 'Finished': return 'bg-green-200 text-green-700'
    case 'Not Started': return 'bg-[#f0f0f0] text-gray-600'
    default: return 'bg-white'
  }
}
</script>
