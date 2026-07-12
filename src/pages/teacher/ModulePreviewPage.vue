<template>
  <div class="min-h-screen bg-white">
    <div class="border-b-[3px] border-black bg-[#7B8FF0] px-8 py-6">
      <button class="mb-4 border-[3px] border-black bg-white px-4 py-2 text-xs font-black" style="box-shadow:3px 3px 0 #000" @click="router.push('/teacher/modules')">Back</button>
      <h1 class="font-display text-[32px] font-black text-white">{{ headerTitle }}</h1>
      <p class="mt-1 text-sm font-bold text-white/85">{{ headerDescription }}</p>
    </div>

    <div class="grid min-h-[calc(100vh-150px)] grid-cols-1 lg:grid-cols-[220px_1fr]">
      <aside class="border-b-[3px] border-black bg-white p-3 lg:border-b-0 lg:border-r-[3px]">
        <div class="mb-3 font-mono text-[10px] uppercase tracking-widest text-gray-500">Student Preview</div>
        <button
          :class="['mb-2 flex w-full items-center gap-2 border-[2px] border-black px-3 py-2.5 text-left text-xs font-black', isIntroActive ? 'bg-[#1565FF] text-white' : 'bg-white']"
          style="box-shadow:2px 2px 0 #000"
          @click="activeTopicId = null"
        >
          <span class="h-4 w-4 rounded-full border-[2px] border-current bg-white" />
          Introduction
        </button>
        <button
          v-for="(topic, index) in topics"
          :key="topic.id"
          :class="['mb-2 flex w-full items-center gap-2 border-[2px] border-black px-3 py-2.5 text-left text-xs font-black', activeTopic?.id === topic.id ? 'bg-[#1565FF] text-white' : 'bg-white']"
          style="box-shadow:2px 2px 0 #000"
          @click="activeTopicId = topic.id"
        >
          <span class="h-4 w-4 rounded-full border-[2px] border-current bg-white" />
          Topic {{ index + 1 }}
        </button>
        <div
          v-for="quiz in quizzes"
          :key="`quiz-${quiz.id}`"
          class="mb-2 flex w-full items-center gap-2 border-[2px] border-black bg-gray-50 px-3 py-2.5 text-left text-xs font-black uppercase tracking-wide opacity-70"
        >
          <span class="grid h-4 w-4 place-items-center rounded-full border-[2px] border-black text-[9px]">Q</span>
          {{ quiz.title }}
        </div>
      </aside>

      <main class="overflow-y-auto p-7">
        <div v-if="loading" class="border-[3px] border-black p-8 text-center font-black" style="box-shadow:4px 4px 0 #000">Loading preview...</div>
        <div v-else-if="error" class="border-[3px] border-black bg-red-50 p-8 text-center font-black text-red-700" style="box-shadow:4px 4px 0 #000">{{ error }}</div>
        <article v-else-if="isIntroActive" class="rounded-lg border-[2px] border-gray-200 bg-white p-6 text-sm leading-7 text-gray-700">
          {{ moduleData?.description || 'Introduction content will be available here.' }}
        </article>
        <div v-else-if="!activeTopic" class="border-[3px] border-black p-8 text-center" style="box-shadow:4px 4px 0 #000">
          <h2 class="font-display text-xl font-black">No generated topics yet.</h2>
          <p class="mt-2 text-sm text-gray-500">Upload or replace the learning material file to generate student content.</p>
        </div>
        <article v-else class="space-y-5">
          <div>
            <h2 class="font-display text-2xl font-black">{{ activeTopic.title }}</h2>
            <p class="mt-1 text-sm text-gray-500">{{ activeTopic.description }}</p>
          </div>
          <div v-if="activeTopic.page_image_urls?.length" class="mx-auto grid max-w-4xl gap-6">
            <img
              v-for="(pageUrl, index) in activeTopic.page_image_urls"
              :key="`${activeTopic.id}-${index}`"
              :src="assetUrl(pageUrl)"
              alt=""
              class="w-full rounded border border-gray-200 bg-white shadow-sm"
            />
          </div>
          <div v-else class="whitespace-pre-line rounded-lg border-[2px] border-gray-200 bg-white p-5 text-sm leading-7 text-gray-700">{{ activeTopic.content }}</div>
        </article>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE_URL, apiFetch } from '@/lib/api'

interface Topic {
  id: number
  title: string
  description?: string | null
  content: string
  page_image_urls: string[]
  sort_order: number
}

interface ModuleDetail {
  id: number
  title: string
  description: string
  topics: Topic[]
  assessments: Array<{ id: number; assessment_type: string; title: string; description: string }>
}

const route = useRoute()
const router = useRouter()
const moduleData = ref<ModuleDetail | null>(null)
const activeTopicId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')

const topics = computed(() => [...(moduleData.value?.topics ?? [])].filter(topic => topic.title.toLowerCase() !== 'introduction').sort((a, b) => a.sort_order - b.sort_order))
const quizzes = computed(() => (moduleData.value?.assessments ?? []).filter(item => item.assessment_type === 'quiz'))
const activeTopic = computed(() => activeTopicId.value ? topics.value.find(topic => topic.id === activeTopicId.value) ?? null : null)
const isIntroActive = computed(() => !activeTopicId.value)
const headerTitle = computed(() => activeTopic.value?.title || moduleData.value?.title || 'Module Preview')
const headerDescription = computed(() => activeTopic.value?.description || moduleData.value?.description || '')

onMounted(async () => {
  loading.value = true
  try {
    moduleData.value = await apiFetch<ModuleDetail>(`/teacher/modules/${route.params.moduleId}`)
    activeTopicId.value = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load preview.'
  } finally {
    loading.value = false
  }
})

function assetUrl(url?: string | null) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_BASE_URL}${url}`
}
</script>
