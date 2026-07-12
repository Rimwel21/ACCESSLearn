<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="eyebrow">Class Management</p>
        <h1 class="font-display text-2xl font-bold">{{ listTitle }}</h1>
      </div>
      <button class="btn-primary" @click="openForm">Add {{ title }}</button>
    </div>

    <div class="card p-4">
      <div class="flex flex-wrap items-center gap-3">
        <input v-model="search" class="input-field max-w-sm" :placeholder="`Search ${listTitle.toLowerCase()}...`" />
        <span v-if="successMessage" class="status-success">{{ successMessage }}</span>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Loading {{ listTitle.toLowerCase() }}...</div>
    <div v-else-if="filteredItems.length === 0" class="card p-12 text-center">
      <h2 class="font-display text-xl font-bold">No {{ listTitle.toLowerCase() }} have been created yet.</h2>
      <p class="mx-auto mt-2 max-w-md text-sm text-ink-soft">
        Create your first {{ title.toLowerCase() }} for the selected module.
      </p>
      <button class="btn-primary mt-5" @click="openForm">Add {{ title }}</button>
    </div>

    <div v-else class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="item in filteredCards" :key="item.id" class="card p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="font-display text-lg font-bold">{{ item.title }}</h2>
            <p class="mt-1 line-clamp-2 text-sm text-ink-soft">{{ item.description }}</p>
          </div>
          <span class="badge-blue badge">{{ item.badge }}</span>
        </div>
        <dl class="mt-4 grid gap-2 text-xs text-ink-soft">
          <div class="flex justify-between gap-3"><dt class="font-bold">Module</dt><dd>{{ item.module || 'Not set' }}</dd></div>
          <div class="flex justify-between gap-3"><dt class="font-bold">Questions</dt><dd>{{ item.questionCount }}</dd></div>
          <div class="flex justify-between gap-3"><dt class="font-bold">Updated</dt><dd>{{ item.updated }}</dd></div>
        </dl>
      </article>
    </div>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showForm" class="fixed inset-0 z-50 overflow-y-auto bg-ink/40 p-4 backdrop-blur-sm" @click.self="closeForm">
          <div class="mx-auto max-w-5xl rounded-lg bg-[#ededed] p-3 shadow-2xl">
            <div class="mb-2 flex justify-end">
              <button class="figma-button" @click="closeForm">Close</button>
            </div>
            <AssessmentDesigner :kind="kind" :title="title" @saved="handleSaved" />
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AssessmentDesigner from '@/components/teacher/AssessmentDesigner.vue'
import { useTeacherStore } from '@/stores/teacher'

const props = defineProps<{
  kind: 'quiz' | 'activity'
  title: string
}>()

const store = useTeacherStore()
const search = ref('')
const showForm = ref(false)
const loading = ref(false)
const successMessage = ref('')

const listTitle = computed(() => props.kind === 'quiz' ? 'Quizzes' : 'Activities')
const items = computed(() => props.kind === 'quiz' ? store.quizzes : store.activities)
const filteredItems = computed(() => items.value.filter(item =>
  !search.value || item.title.toLowerCase().includes(search.value.toLowerCase())
))
const filteredCards = computed(() => filteredItems.value.map(item => {
  if ('type' in item) {
    return {
      id: item.id,
      title: item.title,
      description: item.description ?? '',
      module: item.module,
      badge: item.type,
      questionCount: item.questions?.length ?? 0,
      updated: item.date,
    }
  }

  return {
    id: item.id,
    title: item.title,
    description: item.description,
    module: item.module,
    badge: item.status,
    questionCount: item.questions?.length ?? 0,
    updated: item.dueDate || 'Not set',
  }
}))

onMounted(async () => {
  loading.value = true
  try {
    await store.fetchAssessments(props.kind)
  } finally {
    loading.value = false
  }
})

function openForm() {
  successMessage.value = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function handleSaved() {
  await store.fetchAssessments(props.kind)
  successMessage.value = `${props.title} created successfully.`
  closeForm()
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
