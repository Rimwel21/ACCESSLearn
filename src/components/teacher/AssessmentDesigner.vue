<template>
  <div class="figma-page">
    <div class="figma-title mb-2">{{ title }}</div>

    <div class="grid gap-2 lg:grid-cols-[minmax(0,0.95fr)_minmax(320px,1.05fr)]">
      <div class="grid gap-2">
        <section class="figma-panel">
          <h2 class="figma-card-title">{{ title }} Information</h2>
          <div class="grid gap-3">
            <div>
              <label class="figma-label" for="assessment-title">{{ title }} Title</label>
              <input id="assessment-title" v-model.trim="form.title" class="figma-input" />
            </div>
            <div>
              <label class="figma-label" for="assessment-description">Description</label>
              <input id="assessment-description" v-model.trim="form.description" class="figma-input" />
            </div>
            <div>
              <label class="figma-label" for="assessment-type">{{ title }} Type</label>
              <input id="assessment-type" v-model.trim="form.category" class="figma-input" />
            </div>
            <div>
              <label class="figma-label" for="assessment-week">Week</label>
              <input id="assessment-week" v-model.trim="form.week" class="figma-input" />
            </div>
            <div>
              <label class="figma-label" for="assessment-class">Target Class</label>
              <select id="assessment-class" v-model="form.classId" class="figma-input" @change="selectClass">
                <option value="">Select grade and section</option>
                <option v-for="cls in store.classes" :key="cls.id" :value="cls.id">
                  {{ cls.className }} - {{ gradeLabel(cls.gradeLevel) }} Section {{ cls.section }}
                </option>
              </select>
            </div>
            <div v-if="props.kind === 'quiz'">
              <label class="figma-label" for="assessment-module">Learning Material</label>
              <select id="assessment-module" v-model.number="form.moduleId" class="figma-input" :disabled="!form.classId" @change="loadTopics">
                <option :value="null">Select a material</option>
                <option v-for="module in availableModules" :key="module.id" :value="Number(module.id)">
                  {{ module.title }} - {{ classNameFor(module.classId) }}
                </option>
              </select>
            </div>
            <div v-if="props.kind === 'quiz'">
              <label class="figma-label" for="assessment-topic">Topic</label>
              <select id="assessment-topic" v-model.number="form.topicId" class="figma-input" :disabled="topics.length === 0">
                <option :value="null">Whole module</option>
                <option v-for="topic in topics" :key="topic.id" :value="topic.id">
                  {{ topic.title }}
                </option>
              </select>
            </div>
          </div>
        </section>

        <section class="figma-panel">
          <h2 class="figma-card-title">{{ title }} Settings</h2>
          <div class="grid gap-3">
            <div>
              <label class="figma-label" for="time-limit">Time Limit</label>
              <input id="time-limit" v-model.trim="form.timeLimit" class="figma-input" />
            </div>
            <div>
              <label class="figma-label" for="attempts">Attempts Allowed</label>
              <input id="attempts" v-model.number="form.attemptsAllowed" class="figma-input" min="1" type="number" />
            </div>
            <label class="flex items-center gap-2 text-xs font-bold">
              <input v-model="form.shuffleQuestions" type="checkbox" class="accent-green-500" />
              Shuffle Questions
            </label>
            <label class="flex items-center gap-2 text-xs font-bold">
              <input v-model="form.showAnswersAfterSubmission" type="checkbox" class="accent-green-500" />
              Show Answers after Submission
            </label>
          </div>
        </section>
      </div>

      <section class="figma-panel">
        <h2 class="figma-card-title">Questions</h2>
        <div class="rounded bg-gray-200 p-3">
          <p class="mb-3 text-xs text-gray-600">Add clear questions and optional exact answers for automatic scoring.</p>
          <div class="grid gap-2">
            <div v-for="(question, index) in form.questions" :key="index" class="grid gap-1">
              <input v-model.trim="question.prompt" class="figma-input bg-white" :placeholder="`Question ${index + 1}`" />
              <input v-model.trim="question.answer" class="figma-input bg-white" placeholder="Correct answer (optional)" />
            </div>
          </div>
        </div>
        <div class="mt-3 flex justify-center">
          <button class="figma-button" type="button" @click="addQuestion">Add Question</button>
        </div>
      </section>
    </div>

    <div class="mt-3 flex items-center justify-end gap-3">
      <p v-if="error" class="status-error mr-auto" role="alert">{{ error }}</p>
      <p v-if="success" class="status-success mr-auto" role="status">{{ success }}</p>
      <button class="figma-primary" :disabled="saving" @click="saveAssessment">
        {{ saving ? 'Saving...' : `Save ${title}` }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiFetch } from '@/lib/api'
import { useTeacherStore } from '@/stores/teacher'

const props = defineProps<{
  kind: 'quiz' | 'activity'
  title: string
}>()
const emit = defineEmits<{
  saved: []
}>()

const store = useTeacherStore()
const error = ref('')
const success = ref('')
const form = ref({
  classId: '',
  moduleId: null as number | null,
  topicId: null as number | null,
  title: '',
  description: '',
  category: '',
  week: '',
  timeLimit: '',
  attemptsAllowed: 1,
  shuffleQuestions: true,
  showAnswersAfterSubmission: true,
  questions: [
    { prompt: '', answer: '' },
  ],
})
const topics = ref<Array<{ id: number; title: string }>>([])

const saving = computed(() => props.kind === 'quiz' ? store.quizSaving : store.activitySaving)

onMounted(() => {
  store.fetchClasses()
  store.fetchModules()
})

const availableModules = computed(() => store.modules.filter(module => form.value.classId && module.classId === Number(form.value.classId)))

function addQuestion() {
  form.value.questions.push({ prompt: '', answer: '' })
}

async function loadTopics() {
  topics.value = []
  form.value.topicId = null
  if (!form.value.moduleId) return
  const detail = await apiFetch<{ topics: Array<{ id: number; title: string }> }>(`/teacher/modules/${form.value.moduleId}`)
  topics.value = detail.topics
}

function selectClass() {
  store.selectedClassId = form.value.classId || null
  form.value.moduleId = null
  form.value.topicId = null
  topics.value = []
}

async function saveAssessment() {
  error.value = ''
  success.value = ''

  if (!form.value.title || !form.value.description || !form.value.category || !form.value.week || !form.value.classId || (props.kind === 'quiz' && !form.value.moduleId)) {
    error.value = `Please complete the ${props.title.toLowerCase()} information.`
    return
  }

  const questions = form.value.questions.filter(question => question.prompt.trim())

  if (questions.length === 0) {
    error.value = 'Add at least one question.'
    return
  }

  if (props.kind === 'quiz') {
    await store.addQuiz({
      title: form.value.title,
      moduleId: form.value.moduleId,
      topicId: form.value.topicId,
      description: form.value.description,
      quizType: form.value.category,
      week: form.value.week,
      timeLimit: form.value.timeLimit,
      attemptsAllowed: form.value.attemptsAllowed,
      shuffleQuestions: form.value.shuffleQuestions,
      showAnswersAfterSubmission: form.value.showAnswersAfterSubmission,
      questions,
    })
  } else {
    await store.addActivity({
      title: form.value.title,
      classId: Number(form.value.classId),
      moduleId: null,
      topicId: null,
      description: form.value.description,
      activityType: form.value.category,
      week: form.value.week,
      timeLimit: form.value.timeLimit,
      attemptsAllowed: form.value.attemptsAllowed,
      shuffleQuestions: form.value.shuffleQuestions,
      showAnswersAfterSubmission: form.value.showAnswersAfterSubmission,
      questions,
    })
  }

  success.value = `${props.title} saved successfully.`
  emit('saved')
}

function classNameFor(classId?: number | null) {
  if (!classId) return 'No class'
  const cls = store.classes.find(item => item.id === String(classId))
  return cls ? cls.className : `Class #${classId}`
}

function gradeLabel(value: string) {
  const grades: Record<string, string> = {
    grade_1: 'Grade 1',
    grade_2: 'Grade 2',
    grade_3: 'Grade 3',
    grade_4: 'Grade 4',
    grade_5: 'Grade 5',
    grade_6: 'Grade 6',
  }
  return grades[value] ?? value
}
</script>
