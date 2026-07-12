<template>
  <div class="space-y-6">
    <div class="gradient-brand rounded-2xl px-7 py-5 flex items-center justify-between gap-4">
      <div>
        <h2 class="font-display text-2xl font-bold text-white">Class Management</h2>
        <p class="text-white/75 text-sm mt-1">
          {{ store.selectedClass ? `${store.selectedClass.className} - ${store.selectedClass.subject}` : 'Create a class to get started' }}
        </p>
      </div>
      <button @click="showAddClass = true" class="px-5 py-2.5 rounded-full border border-white/40 bg-white/20 backdrop-blur-sm text-white text-sm font-semibold hover:bg-white/30 transition-all">
        New Class
      </button>
    </div>

    <div v-if="store.classesLoading" class="empty-state">Loading classes...</div>

    <div v-else-if="!store.hasClasses" class="card p-14 flex flex-col items-center text-center">
      <h3 class="font-display text-xl font-bold mb-2">No classes yet</h3>
      <p class="text-sm text-ink-soft max-w-sm mb-6">Create your first class to start adding modules, activities, and quizzes for your students.</p>
      <button @click="showAddClass = true" class="btn-primary">Create Your First Class</button>
      <p v-if="store.classError" class="status-error mt-4">{{ store.classError }}</p>
    </div>

    <template v-else>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="font-display text-base font-semibold text-ink-soft">Your Classes</h3>
          <p v-if="store.classError" class="status-error">{{ store.classError }}</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="cls in store.classes"
            :key="cls.id"
            @click="store.selectClass(cls.id)"
            :class="['card-hover p-4 cursor-pointer relative border-2 transition-all', store.selectedClassId === cls.id ? 'border-brand-blue' : 'border-transparent']"
          >
            <button @click.stop="confirmDeleteClass(cls.id)" class="absolute top-2 right-2 w-6 h-6 rounded-full hover:bg-rose-50 text-gray-300 hover:text-brand-rose flex items-center justify-center text-xs transition-all">x</button>
            <div class="font-display font-bold text-sm pr-6">{{ cls.className }}</div>
            <div class="text-xs text-ink-soft mt-1">{{ cls.subject }}</div>
            <div class="text-xs text-ink-soft mt-1">{{ gradeLabel(cls.gradeLevel) }} - Section {{ cls.section }}</div>
            <div class="text-[11px] font-mono text-gray-400 mt-2">{{ cls.studentCount }} students</div>
            <div v-if="store.selectedClassId === cls.id" class="absolute -top-2 -left-2 bg-brand-blue text-white text-[10px] font-bold px-2 py-0.5 rounded-full">Active</div>
          </div>

          <button
            @click="showAddClass = true"
            class="border-2 border-dashed border-gray-200 rounded-xl flex flex-col items-center justify-center gap-1.5 text-ink-soft hover:border-brand-blue hover:text-brand-blue hover:bg-brand-blue-soft/30 transition-all min-h-[120px]"
          >
            <span class="text-xl font-bold">+</span>
            <span class="text-xs font-semibold">Add Class</span>
          </button>
        </div>
      </div>

      <template v-if="store.selectedClass">
        <div class="grid gap-4 md:grid-cols-3">
          <div class="card p-5">
            <div class="font-display text-2xl font-bold">{{ store.selectedClass.studentCount }}</div>
            <div class="text-xs text-ink-soft font-medium">Total Students</div>
          </div>
          <div class="card p-5">
            <div class="font-display text-2xl font-bold">{{ classModules.length }}</div>
            <div class="text-xs text-ink-soft font-medium">Class Materials</div>
          </div>
          <div class="card p-5">
            <div class="font-display text-2xl font-bold">{{ store.selectedClass.schoolYear || 'Not set' }}</div>
            <div class="text-xs text-ink-soft font-medium">School Year</div>
          </div>
        </div>

        <div class="grid gap-5 xl:grid-cols-[1fr_230px]">
          <div class="space-y-4">
            <div class="card p-5">
              <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 class="font-display text-base font-semibold">Students</h3>
                  <p class="text-xs text-ink-soft">Automatically enrolled from matching grade level and section.</p>
                </div>
                <button class="figma-button" @click="store.fetchClassStudents(store.selectedClass!.id)">Refresh</button>
              </div>

              <div v-if="store.classStudentsLoading" class="text-sm text-ink-soft">Loading students...</div>
              <div v-else-if="store.classStudents.length === 0" class="text-sm text-ink-soft">No matching students found yet.</div>
              <div v-else class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                  <thead class="border-b border-gray-100 text-ink-soft">
                    <tr>
                      <th class="py-2 font-semibold">Name</th>
                      <th class="py-2 font-semibold">Student ID</th>
                      <th class="py-2 font-semibold">Email</th>
                      <th class="py-2 font-semibold">Grade</th>
                      <th class="py-2 font-semibold">Section</th>
                      <th class="py-2 font-semibold">Registered</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="student in store.classStudents" :key="student.id" class="border-b border-gray-50 last:border-0">
                      <td class="py-2 font-semibold text-ink">{{ student.name }}</td>
                      <td class="py-2 text-ink-soft">{{ student.username || student.accountId }}</td>
                      <td class="py-2 text-ink-soft">{{ student.email || 'No email' }}</td>
                      <td class="py-2 text-ink-soft">{{ gradeLabel(student.gradeLevel) }}</td>
                      <td class="py-2 text-ink-soft">{{ student.section }}</td>
                      <td class="py-2 text-ink-soft">{{ student.createdAt || 'Not available' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-for="section in sections" :key="section.title" class="card-hover cursor-pointer" @click="router.push(section.to)">
              <div class="flex">
                <div :class="`w-1.5 flex-shrink-0 rounded-l-xl ${section.accent}`" />
                <div class="flex-1 p-5">
                  <h3 class="font-display text-base font-semibold mb-2">{{ section.title }}</h3>
                  <p class="text-sm text-ink-soft leading-relaxed">{{ section.description }}</p>
                  <div class="flex items-center justify-between mt-4 gap-3">
                    <div class="flex flex-wrap gap-4">
                      <span v-for="meta in section.meta" :key="meta" class="text-[11.5px] text-ink-soft">{{ meta }}</span>
                    </div>
                    <button :class="`text-white text-xs font-bold px-4 py-2 rounded-full ${section.btnClass}`">{{ section.btnLabel }}</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="card p-4">
              <div class="font-display text-[13px] font-semibold mb-3">Quick Actions</div>
              <div class="space-y-2">
                <button @click="router.push('/teacher/modules')" class="flex items-center gap-2.5 w-full px-4 py-2.5 rounded-xl bg-brand-blue text-white text-[13px] font-semibold hover:-translate-y-0.5 hover:shadow-lg transition-all">Add Module</button>
                <button @click="router.push('/teacher/quizzes')" class="flex items-center gap-2.5 w-full px-4 py-2.5 rounded-xl gradient-violet text-white text-[13px] font-semibold hover:-translate-y-0.5 hover:shadow-lg transition-all">Create Quiz</button>
                <button @click="router.push('/teacher/activities')" class="flex items-center gap-2.5 w-full px-4 py-2.5 rounded-xl gradient-teal text-white text-[13px] font-semibold hover:-translate-y-0.5 hover:shadow-lg transition-all">Create Activity</button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddClass" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="closeClassModal">
          <div class="absolute inset-0 bg-ink/40 backdrop-blur-sm" @click="closeClassModal" />
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div class="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="font-display font-bold text-lg">Create New Class</h3>
              <button @click="closeClassModal" class="w-8 h-8 rounded-full hover:bg-surface flex items-center justify-center text-ink-soft hover:text-ink transition-all text-lg">x</button>
            </div>
            <div class="px-6 py-5 space-y-4">
              <div>
                <label class="block text-xs font-semibold text-ink-soft mb-1.5">Class Name</label>
                <input v-model.trim="newClass.className" class="input-field" placeholder="e.g. Grade 6 Mathematics" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-ink-soft mb-1.5">Subject</label>
                <input v-model.trim="newClass.subject" class="input-field" placeholder="e.g. Mathematics" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-ink-soft mb-1.5">Grade Level</label>
                <select v-model="newClass.gradeLevel" class="input-field">
                  <option value="">Select grade level...</option>
                  <option v-for="g in gradeOptions" :key="g.value" :value="g.value">{{ g.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-ink-soft mb-1.5">Section</label>
                <input v-model.trim="newClass.section" class="input-field" placeholder="e.g. A, Diamond, Sampaguita" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-ink-soft mb-1.5">School Year</label>
                <input v-model.trim="newClass.schoolYear" class="input-field" placeholder="e.g. 2026-2027" />
              </div>
              <p v-if="store.classError" class="status-error">{{ store.classError }}</p>
            </div>
            <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button @click="closeClassModal" class="btn-secondary">Cancel</button>
              <button @click="createClass" class="btn-primary" :disabled="store.classSaving">
                {{ store.classSaving ? 'Creating...' : 'Create Class' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="deleteTargetId" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="deleteTargetId = null">
          <div class="absolute inset-0 bg-ink/40 backdrop-blur-sm" @click="deleteTargetId = null" />
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden p-6 text-center">
            <h3 class="font-display font-bold text-base mb-2">Delete this class?</h3>
            <p class="text-sm text-ink-soft mb-5">This removes the class container. Content linked to it may no longer be available to students.</p>
            <div class="flex justify-center gap-3">
              <button @click="deleteTargetId = null" class="btn-secondary">Cancel</button>
              <button @click="performDelete" class="px-5 py-2.5 rounded-full bg-brand-rose text-white font-semibold text-sm hover:bg-red-600 transition-all">Delete</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTeacherStore } from '@/stores/teacher'

const router = useRouter()
const store = useTeacherStore()

const gradeOptions = [
  { value: 'grade_1', label: 'Grade 1' },
  { value: 'grade_2', label: 'Grade 2' },
  { value: 'grade_3', label: 'Grade 3' },
  { value: 'grade_4', label: 'Grade 4' },
  { value: 'grade_5', label: 'Grade 5' },
  { value: 'grade_6', label: 'Grade 6' },
]

const showAddClass = ref(false)
const newClass = ref(defaultClassForm())
const deleteTargetId = ref<string | null>(null)

const classModules = computed(() => store.modules.filter(module => module.classId === Number(store.selectedClassId)))

const sections = computed(() => [
  {
    title: 'Modules / Learning Materials',
    description: 'Manage class learning materials, upload resources, and track published content.',
    accent: 'bg-gradient-to-b from-brand-blue to-brand-violet',
    btnClass: 'bg-gradient-to-r from-brand-blue to-brand-violet',
    btnLabel: 'Manage',
    to: '/teacher/modules',
    meta: [`${classModules.value.length} materials`, `${classModules.value.filter(module => module.status === 'Published').length} published`],
  },
  {
    title: 'Activities',
    description: 'Create and manage student activities for the selected class content.',
    accent: 'bg-gradient-to-b from-brand-teal to-brand-green',
    btnClass: 'bg-gradient-to-r from-brand-teal to-brand-green',
    btnLabel: 'Manage',
    to: '/teacher/activities',
    meta: [`${store.activities.length} activities`, `${store.atRiskStudents.length} students need help`],
  },
  {
    title: 'Quizzes',
    description: 'Create, schedule, and review quizzes linked to class learning materials.',
    accent: 'bg-gradient-to-b from-brand-amber to-brand-rose',
    btnClass: 'bg-gradient-to-r from-brand-amber to-brand-rose',
    btnLabel: 'Review',
    to: '/teacher/quizzes',
    meta: [`${store.quizzes.length} quizzes`, 'Class scoped by material'],
  },
])

onMounted(() => {
  store.fetchClasses()
  store.fetchModules()
})

function defaultClassForm() {
  return {
    className: '',
    subject: '',
    gradeLevel: '',
    section: '',
    schoolYear: '',
  }
}

async function createClass() {
  if (!newClass.value.className || !newClass.value.subject || !newClass.value.gradeLevel || !newClass.value.section) {
    alert('Please complete the class details.')
    return
  }

  await store.addClass({
    className: newClass.value.className,
    subject: newClass.value.subject,
    gradeLevel: newClass.value.gradeLevel,
    section: newClass.value.section,
    schoolYear: newClass.value.schoolYear || null,
  })
  closeClassModal()
}

function closeClassModal() {
  showAddClass.value = false
  newClass.value = defaultClassForm()
}

function confirmDeleteClass(id: string) {
  deleteTargetId.value = id
}

async function performDelete() {
  if (deleteTargetId.value) await store.deleteClass(deleteTargetId.value)
  deleteTargetId.value = null
}

function gradeLabel(value: string) {
  return gradeOptions.find(option => option.value === value)?.label ?? value
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-active .relative, .modal-leave-active .relative { transition: transform .2s, opacity .2s; }
.modal-enter-from { opacity: 0; }
.modal-enter-from .relative { transform: scale(.95); opacity: 0; }
.modal-leave-to { opacity: 0; }
</style>
