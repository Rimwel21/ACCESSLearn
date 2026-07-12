<template>
  <div class="flex min-h-screen bg-white">
    <aside class="flex w-[220px] min-w-[220px] flex-col border-r-[3px] border-black bg-white">
      <RouterLink to="/student/dashboard" class="mx-3 mb-2 mt-3 flex items-center gap-2 border-[3px] border-black px-3 py-2 text-xs font-black text-black no-underline transition-colors hover:bg-[#FFE135]" style="box-shadow:3px 3px 0 #000">
        Go Back
      </RouterLink>

      <div class="px-3.5 py-2">
        <div class="font-mono text-[10px] uppercase tracking-widest text-gray-500">Module {{ moduleId }}</div>
        <div class="mt-0.5 font-display text-[13px] font-black leading-tight">{{ moduleData?.title || 'Learning module' }}</div>
      </div>

      <div class="px-3.5 py-2">
        <div class="h-[8px] overflow-hidden border-[2px] border-black bg-gray-200">
          <div class="h-full bg-green-500 transition-all" :style="{ width: progress.percent + '%' }" />
        </div>
        <div class="mt-1 font-mono text-[10px] text-gray-500">{{ progress.percent }}% Progress</div>
      </div>

      <div class="flex-1 space-y-2 overflow-y-auto px-3 py-2">
        <button
          :class="[
            'flex w-full items-center gap-2.5 border-[2px] border-black px-3 py-2.5 text-left text-[13px] font-bold transition-all',
            isIntroActive ? 'bg-[#1565FF] text-white' : 'bg-white hover:bg-[#D6E4FF]'
          ]"
          style="box-shadow:2px 2px 0 #000"
          @click="selectIntro"
        >
          <span class="grid h-[20px] w-[20px] flex-shrink-0 place-items-center rounded-full border-[2px] border-current bg-white" />
          <span class="truncate">Introduction</span>
        </button>

        <button
          v-for="(topic, index) in topics"
          :key="topic.id"
          :class="[
            'flex w-full items-center gap-2.5 border-[2px] border-black px-3 py-2.5 text-left text-[13px] font-bold transition-all',
            activeTopic?.id === topic.id ? 'bg-[#1565FF] text-white' : 'bg-white hover:bg-[#D6E4FF]'
          ]"
          style="box-shadow:2px 2px 0 #000"
          @click="selectTopic(topic.id)"
        >
          <span :class="['grid h-[20px] w-[20px] flex-shrink-0 place-items-center rounded-full border-[2px] border-black text-[10px] font-black', completedIds.has(topic.id) ? 'bg-green-500 text-white' : 'bg-white text-black']">
            {{ completedIds.has(topic.id) ? 'OK' : '' }}
          </span>
          <span class="truncate">Topic {{ index + 1 }}</span>
        </button>

        <button
          v-for="quiz in quizzes"
          :key="`quiz-${quiz.id}`"
          :disabled="!quizUnlocked"
          :class="[
            'flex w-full items-center gap-2.5 border-[2px] border-black px-3 py-2.5 text-left text-[12px] font-bold uppercase tracking-wide transition-all',
            activeQuiz?.id === quiz.id ? 'bg-[#FFE135] text-black' : 'bg-white hover:bg-[#FFE135]',
            !quizUnlocked ? 'cursor-not-allowed opacity-45' : ''
          ]"
          :style="quizUnlocked ? 'box-shadow:2px 2px 0 #000' : ''"
          @click="selectQuiz(quiz.id)"
        >
          <span :class="['grid h-[20px] w-[20px] flex-shrink-0 place-items-center rounded-full border-[2px] border-black text-[10px] font-black', completedQuizIds.has(quiz.id) ? 'bg-green-500 text-white' : 'bg-white text-black']">
            {{ completedQuizIds.has(quiz.id) ? 'OK' : 'Q' }}
          </span>
          <span class="truncate">{{ quiz.title }}</span>
        </button>
      </div>
    </aside>

    <main class="flex min-w-0 flex-1 flex-col">
      <header class="flex items-center justify-between border-b-[3px] border-black bg-[#7B8FF0] px-8 py-6">
        <div>
          <h1 class="font-display text-[32px] font-black leading-tight text-white">{{ headerTitle }}</h1>
          <p class="mt-1.5 font-display text-[13px] font-bold text-white/85">{{ headerDescription }}</p>
        </div>
        <div class="text-5xl">LMS</div>
      </header>

      <section class="flex-1 overflow-y-auto bg-white p-7">
        <div v-if="content.loading" class="border-[3px] border-black bg-white p-8 text-center font-black" style="box-shadow:4px 4px 0 #000">Loading learning content...</div>
        <div v-else-if="content.error" class="border-[3px] border-black bg-red-50 p-8 text-center font-black text-red-700" style="box-shadow:4px 4px 0 #000">{{ content.error }}</div>
        <div v-else-if="topics.length === 0 && !isIntroActive" class="border-[3px] border-black bg-white p-10 text-center" style="box-shadow:5px 5px 0 #000">
          <h2 class="font-display text-xl font-black">No learning materials are available for this module yet.</h2>
          <p class="mt-2 text-sm text-gray-500">Please check again after your teacher publishes content.</p>
        </div>

        <article v-else-if="isIntroActive" class="space-y-6">
          <div class="rounded-lg border-[2px] border-gray-200 bg-white p-6 text-sm leading-7 text-gray-700">
            {{ moduleData?.description || 'Introduction content will be available here.' }}
          </div>
          <div class="flex justify-end pt-4">
            <button
              class="border-[3px] border-black bg-[#1565FF] px-5 py-2.5 text-sm font-black text-white transition-all hover:-translate-x-[2px] hover:-translate-y-[2px] disabled:opacity-50"
              style="box-shadow:4px 4px 0 #000"
              :disabled="topics.length === 0"
              @click="goNext"
            >
              Start Topic 1
            </button>
          </div>
        </article>

        <article v-else-if="activeQuiz" class="space-y-5">
          <div class="border-[3px] border-black bg-[#FFE135] p-5" style="box-shadow:5px 5px 0 #000">
            <div class="font-mono text-[10px] font-black uppercase tracking-widest">Quiz</div>
            <h2 class="mt-1 font-display text-2xl font-black">{{ activeQuiz.title }}</h2>
            <p class="mt-2 text-sm text-gray-700">{{ activeQuiz.description }}</p>
          </div>

          <div v-if="quizResult" class="border-[3px] border-black bg-green-50 p-4 font-black text-green-800" style="box-shadow:4px 4px 0 #000">
            Score: {{ quizResult.score }} / {{ quizResult.total }}
          </div>

          <div v-for="(question, index) in activeQuiz.questions" :key="index" class="border-[3px] border-black bg-white p-5" style="box-shadow:4px 4px 0 #000">
            <label class="block text-sm font-black">Question {{ index + 1 }}</label>
            <p class="mt-1 text-sm text-gray-700">{{ question.prompt }}</p>
            <input v-model="quizAnswers[String(index)]" class="mt-3 w-full border-[2px] border-black px-3 py-2 text-sm outline-none focus:bg-[#D6E4FF]" placeholder="Your answer" />
          </div>

          <div class="flex justify-end">
            <button class="border-[3px] border-black bg-[#1565FF] px-5 py-2.5 text-sm font-black text-white transition-all hover:-translate-x-[2px] hover:-translate-y-[2px]" style="box-shadow:4px 4px 0 #000" @click="submitActiveQuiz">
              Submit Quiz
            </button>
          </div>
        </article>

        <article v-else-if="activeTopic" class="space-y-6">
          <div v-if="activeTopic.page_image_urls?.length" class="mx-auto grid max-w-4xl gap-6">
            <img
              v-for="(pageUrl, index) in activeTopic.page_image_urls"
              :key="`${activeTopic.id}-${index}`"
              :src="assetUrl(pageUrl)"
              alt=""
              class="w-full rounded border border-gray-200 bg-white shadow-sm"
            />
          </div>
          <div v-else class="prose max-w-none whitespace-pre-line text-[14px] leading-relaxed text-gray-700">{{ activeTopic.content }}</div>

          <div v-if="activeTopic.image_url" class="flex flex-col gap-5 lg:flex-row">
            <img :src="assetUrl(activeTopic.image_url)" alt="" class="h-[280px] w-full border-[3px] border-[#FF9F40] object-cover lg:w-[280px]" />
            <div class="flex-1 rounded-lg border-[2px] border-gray-200 bg-white p-5 text-[14px] leading-relaxed text-gray-700">
              {{ activeTopic.description }}
            </div>
          </div>

          <div class="flex items-center justify-between pt-4">
            <button
              class="border-[3px] border-black bg-white px-5 py-2.5 text-sm font-black transition-all hover:-translate-x-[1px] hover:-translate-y-[1px]"
              style="box-shadow:3px 3px 0 #000"
              @click="goPrevious"
            >
              Previous
            </button>
            <span class="font-mono text-xs text-gray-400">Topic {{ activeIndex + 1 }} of {{ topics.length }}</span>
            <button
              class="border-[3px] border-black bg-[#1565FF] px-5 py-2.5 text-sm font-black text-white transition-all hover:-translate-x-[2px] hover:-translate-y-[2px]"
              style="box-shadow:4px 4px 0 #000"
              @click="goNext"
            >
              {{ activeIndex === topics.length - 1 ? 'Finish Module' : 'Next Topic' }}
            </button>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { API_BASE_URL } from '@/lib/api'
import { useStudentContentStore } from '@/stores/studentContent'

const route = useRoute()
const content = useStudentContentStore()
const activeTopicId = ref<number | null>(null)
const activeQuizId = ref<number | null>(null)
const quizAnswers = ref<Record<string, string>>({})
const quizResult = ref<{ score: number; total: number } | null>(null)

const moduleId = computed(() => String(route.params.moduleId))
const moduleData = computed(() => content.currentModule)
const topics = computed(() => content.sortedTopics.filter(topic => topic.title.toLowerCase() !== 'introduction'))
const progress = computed(() => content.progress)
const completedIds = computed(() => new Set(progress.value.completed_topic_ids))
const completedQuizIds = computed(() => new Set(progress.value.completed_quiz_ids))
const activeTopic = computed(() => activeTopicId.value ? topics.value.find(topic => topic.id === activeTopicId.value) ?? null : null)
const quizzes = computed(() => (moduleData.value?.assessments ?? []).filter(item => item.assessment_type === 'quiz'))
const activeQuiz = computed(() => quizzes.value.find(quiz => quiz.id === activeQuizId.value) ?? null)
const activeIndex = computed(() => activeTopic.value ? topics.value.findIndex(topic => topic.id === activeTopic.value?.id) : 0)
const quizUnlocked = computed(() => topics.value.length > 0 && progress.value.completed_topics >= topics.value.length)
const isIntroActive = computed(() => !activeTopicId.value && !activeQuizId.value)
const headerTitle = computed(() => activeQuiz.value?.title || activeTopic.value?.title || moduleData.value?.title || 'Learning Content')
const headerDescription = computed(() => activeQuiz.value?.description || activeTopic.value?.description || moduleData.value?.description || 'Module description')

onMounted(async () => {
  await content.fetchModule(moduleId.value)
  activeTopicId.value = null
})

watch(topics, value => {
  if (!isIntroActive.value && !activeTopicId.value && value.length) activeTopicId.value = value[0].id
})

async function selectTopic(topicId: number) {
  activeQuizId.value = null
  quizResult.value = null
  activeTopicId.value = topicId
  await content.markTopic(moduleId.value, topicId, 'in_progress')
}

function selectIntro() {
  activeTopicId.value = null
  activeQuizId.value = null
  quizResult.value = null
}

function selectQuiz(quizId: number) {
  if (!quizUnlocked.value) return
  activeQuizId.value = quizId
  activeTopicId.value = null
  quizAnswers.value = {}
  quizResult.value = null
}

async function goPrevious() {
  if (activeIndex.value <= 0) {
    selectIntro()
    return
  }
  const previous = topics.value[activeIndex.value - 1]
  await selectTopic(previous.id)
}

async function goNext() {
  if (isIntroActive.value) {
    const first = topics.value[0]
    if (first) await selectTopic(first.id)
    return
  }
  if (!activeTopic.value) return
  await content.markTopic(moduleId.value, activeTopic.value.id, 'completed')
  if (activeIndex.value >= topics.value.length - 1) {
    if (quizzes.value.length) selectQuiz(quizzes.value[0].id)
    return
  }
  const next = topics.value[activeIndex.value + 1]
  await selectTopic(next.id)
}

async function submitActiveQuiz() {
  if (!activeQuiz.value) return
  const result = await content.submitQuiz(moduleId.value, activeQuiz.value.id, quizAnswers.value)
  if (result) quizResult.value = { score: result.score, total: result.total }
}

function assetUrl(url?: string | null) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_BASE_URL}${url}`
}
</script>
