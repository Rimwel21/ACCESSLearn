import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { API_BASE_URL, apiFetch } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type ModuleStatus = 'Published' | 'Unpublished'
type ActivityStatus = 'Not Started' | 'In Progress' | 'Overdue' | 'Finished'
type Difficulty = 'Easy' | 'Medium' | 'Hard'

interface Module {
  id: string
  title: string
  description: string
  status: ModuleStatus
  lastUpdated: string
  classId?: number | null
  contentType?: string | null
  week?: string | null
  behaviorRequired?: boolean
  estimatedTime?: string | null
  fileName?: string | null
  fileType?: string | null
  fileSize?: number | null
}

interface Performer {
  name: string
  initials: string
  gradient: string
  assignments: number
  quiz: number
  activities: number
  total: number
  avg: string
}

interface RecentActivity {
  text: string
  time: string
  color: string
}

interface StudentRow {
  studentId: string
  studentName: string
  initials: string
  avatarGradient: string
  overallPercent: number
  activitiesCompleted: number
  activitiesTotal: number
  status: 'Complete' | 'In Progress' | 'Needs Help'
  lastActivity: string
}

interface Quiz {
  id: string
  title: string
  description?: string
  module: string
  moduleId?: number | null
  topicId?: number | null
  type: string
  difficulty: Difficulty
  date: string
  questions?: AssessmentQuestion[]
}

interface Activity {
  id: string
  title: string
  description: string
  module: string
  classId?: number | null
  moduleId?: number | null
  topicId?: number | null
  dueDate: string
  dueTime: string
  status: ActivityStatus
  questions?: AssessmentQuestion[]
}

interface AssessmentQuestion {
  prompt: string
  answer?: string | null
}

interface ClassInfo {
  id: string
  className: string
  subject: string
  gradeLevel: string
  section: string
  schoolYear?: string | null
  studentCount: number
  createdAt: string
}

interface ClassStudent {
  id: number
  accountId: number
  name: string
  username?: string | null
  email?: string | null
  gradeLevel: string
  section: string
  createdAt?: string | null
}

interface TeacherClassResponse {
  id: number
  teacher_id: number
  class_name: string
  subject: string
  grade_level: string
  section: string
  school_year: string | null
  student_count: number
  created_at: string
  updated_at: string
}

interface ClassStudentResponse {
  id: number
  account_id: number
  name: string
  username?: string | null
  email?: string | null
  grade_level: string
  section: string
  created_at?: string | null
}

interface TeacherModuleResponse {
  id: number
  teacher_id: number
  class_id: number | null
  title: string
  description: string
  content_type: string | null
  week: string | null
  status: ModuleStatus
  behavior_required: boolean
  estimated_time: string | null
  file_name: string | null
  file_type: string | null
  file_size: number | null
  created_at: string
  updated_at: string
}

interface TeacherAssessmentResponse {
  id: number
  teacher_id: number
  class_id: number | null
  module_id: number | null
  topic_id: number | null
  assessment_type: 'quiz' | 'activity'
  title: string
  description: string
  category: string | null
  week: string | null
  time_limit: string | null
  attempts_allowed: number
  shuffle_questions: boolean
  show_answers_after_submission: boolean
  questions: AssessmentQuestion[]
  created_at: string
  updated_at: string
}

export const useTeacherStore = defineStore('teacher', () => {
  const teacherName = ref('Ms. Rymuel')
  const modules = ref<Module[]>([])
  const quizzes = ref<Quiz[]>([])
  const activities = ref<Activity[]>([])

  const modulesLoading = ref(false)
  const moduleSaving = ref(false)
  const moduleError = ref('')
  const quizSaving = ref(false)
  const quizError = ref('')
  const activitySaving = ref(false)
  const activityError = ref('')
  const classesLoading = ref(false)
  const classSaving = ref(false)
  const classError = ref('')
  const classStudents = ref<ClassStudent[]>([])
  const classStudentsLoading = ref(false)

  const performers = ref<Performer[]>([
    { name: 'Penagrin, Aguiluz Emmanuelle O.', initials: 'FE', gradient: 'from-brand-blue to-brand-violet', assignments: 80, quiz: 183, activities: 80, total: 343, avg: '95%' },
    { name: 'Nugajin, Rymuel', initials: 'NR', gradient: 'from-cyan-500 to-cyan-700', assignments: 80, quiz: 180, activities: 80, total: 340, avg: '92%' },
    { name: 'Dimaculangan, Dominhar', initials: 'DD', gradient: 'from-amber-400 to-rose-500', assignments: 80, quiz: 153, activities: 80, total: 313, avg: '84%' },
    { name: 'Santos, Carla M.', initials: 'SC', gradient: 'from-emerald-400 to-teal-500', assignments: 78, quiz: 170, activities: 75, total: 323, avg: '88%' },
  ])

  const recentActivities = ref<RecentActivity[]>([
    { text: 'Module created', time: '2 min ago', color: 'bg-brand-green' },
    { text: 'Class management updated', time: '1 hr ago', color: 'bg-brand-blue' },
  ])

  const students = ref<StudentRow[]>([
    { studentId: 's1', studentName: 'Penagrin, Aguiluz Emmanuelle O.', initials: 'FE', avatarGradient: 'from-brand-blue to-brand-violet', overallPercent: 95, activitiesCompleted: 12, activitiesTotal: 12, status: 'Complete', lastActivity: '03-24-26' },
    { studentId: 's2', studentName: 'Nugajin, Rymuel', initials: 'NR', avatarGradient: 'from-cyan-500 to-cyan-700', overallPercent: 88, activitiesCompleted: 10, activitiesTotal: 12, status: 'In Progress', lastActivity: '03-22-26' },
  ])

  const classes = ref<ClassInfo[]>([])
  const selectedClassId = ref<string | null>(null)

  const selectedClass = computed(() => classes.value.find(c => c.id === selectedClassId.value) ?? null)
  const hasClasses = computed(() => classes.value.length > 0)
  const publishedModules = computed(() => modules.value.filter(m => m.status === 'Published'))
  const unpublishedModules = computed(() => modules.value.filter(m => m.status === 'Unpublished'))
  const atRiskStudents = computed(() => students.value.filter(s => s.status === 'Needs Help'))

  async function fetchClasses() {
    const auth = useAuthStore()
    if (!auth.token) return
    classesLoading.value = true
    classError.value = ''

    try {
      const data = await apiFetch<TeacherClassResponse[]>('/teacher/classes/', { token: auth.token })
      classes.value = data.map(mapClassResponse)
      if (!selectedClassId.value && classes.value.length) {
        selectedClassId.value = classes.value[0].id
        await fetchClassStudents(selectedClassId.value)
      } else if (selectedClassId.value && !classes.value.some(c => c.id === selectedClassId.value)) {
        selectedClassId.value = classes.value[0]?.id ?? null
        classStudents.value = []
      }
    } catch (err) {
      classError.value = err instanceof Error ? err.message : 'Unable to load classes'
    } finally {
      classesLoading.value = false
    }
  }

  async function addClass(payload: {
    className: string
    subject: string
    gradeLevel: string
    section: string
    schoolYear?: string | null
  }) {
    const auth = useAuthStore()
    if (!auth.token) throw new Error('Please login first')
    classSaving.value = true
    classError.value = ''

    try {
      const saved = await apiFetch<TeacherClassResponse>('/teacher/classes/', {
        method: 'POST',
        token: auth.token,
        body: JSON.stringify({
          class_name: payload.className,
          subject: payload.subject,
          grade_level: payload.gradeLevel,
          section: payload.section,
          school_year: payload.schoolYear || null,
        }),
      })
      const mapped = mapClassResponse(saved)
      classes.value.unshift(mapped)
      selectedClassId.value = mapped.id
      await fetchClassStudents(mapped.id)
      return mapped
    } catch (err) {
      classError.value = err instanceof Error ? err.message : 'Unable to create class'
      throw err
    } finally {
      classSaving.value = false
    }
  }

  async function selectClass(id: string) {
    selectedClassId.value = id
    await fetchClassStudents(id)
  }

  async function deleteClass(id: string) {
    const auth = useAuthStore()
    const original = classes.value
    classes.value = classes.value.filter(c => c.id !== id)
    if (selectedClassId.value === id) {
      selectedClassId.value = classes.value[0]?.id ?? null
      classStudents.value = []
    }
    if (!auth.token) return

    try {
      await apiFetch(`/teacher/classes/${id}`, { method: 'DELETE', token: auth.token })
      if (selectedClassId.value) await fetchClassStudents(selectedClassId.value)
    } catch (err) {
      classes.value = original
      classError.value = err instanceof Error ? err.message : 'Unable to delete class'
    }
  }

  async function fetchClassStudents(id: string) {
    const auth = useAuthStore()
    if (!auth.token) return
    classStudentsLoading.value = true
    classError.value = ''

    try {
      const data = await apiFetch<ClassStudentResponse[]>(`/teacher/classes/${id}/students`, { token: auth.token })
      classStudents.value = data.map(mapClassStudentResponse)
      const target = classes.value.find(cls => cls.id === id)
      if (target) target.studentCount = classStudents.value.length
    } catch (err) {
      classError.value = err instanceof Error ? err.message : 'Unable to load students'
    } finally {
      classStudentsLoading.value = false
    }
  }

  async function fetchModules() {
    const auth = useAuthStore()
    if (!auth.token) return
    modulesLoading.value = true
    moduleError.value = ''

    try {
      const data = await apiFetch<TeacherModuleResponse[]>('/teacher/modules/', { token: auth.token })
      modules.value = data.map(mapModuleResponse)
    } catch (err) {
      moduleError.value = err instanceof Error ? err.message : 'Unable to load materials'
    } finally {
      modulesLoading.value = false
    }
  }

  async function addModule(module: Omit<Module, 'id' | 'lastUpdated'> & { file?: File | null }) {
    const auth = useAuthStore()
    moduleSaving.value = true
    moduleError.value = ''

    try {
      if (!auth.token) throw new Error('Please login first')

      const saved = module.file
        ? await uploadModule(module, auth.token)
        : await apiFetch<TeacherModuleResponse>('/teacher/modules/', {
            method: 'POST',
            token: auth.token,
            body: JSON.stringify({
              title: module.title,
              description: module.description,
              content_type: module.contentType,
              week: module.week,
              status: module.status,
              behavior_required: module.behaviorRequired ?? true,
              estimated_time: module.estimatedTime,
              class_id: module.classId ?? null,
            }),
          })
      modules.value.unshift(mapModuleResponse(saved))
      return saved
    } catch (err) {
      moduleError.value = err instanceof Error ? err.message : 'Unable to create material'
      throw err
    } finally {
      moduleSaving.value = false
    }
  }

  async function deleteModule(id: string) {
    const auth = useAuthStore()
    const original = modules.value
    modules.value = modules.value.filter(m => m.id !== id)
    if (!auth.token) return

    try {
      await apiFetch(`/teacher/modules/${id}`, { method: 'DELETE', token: auth.token })
    } catch (err) {
      modules.value = original
      moduleError.value = err instanceof Error ? err.message : 'Unable to delete material'
    }
  }

  async function updateModule(id: string, updates: Partial<Module>) {
    const auth = useAuthStore()
    if (!auth.token) throw new Error('Please login first')
    const saved = await apiFetch<TeacherModuleResponse>(`/teacher/modules/${id}`, {
      method: 'PATCH',
      token: auth.token,
      body: JSON.stringify({
        title: updates.title,
        description: updates.description,
        content_type: updates.contentType,
        week: updates.week,
        status: updates.status,
        behavior_required: updates.behaviorRequired,
        estimated_time: updates.estimatedTime,
        class_id: updates.classId ?? null,
      }),
    })
    const mapped = mapModuleResponse(saved)
    modules.value = modules.value.map(module => module.id === id ? mapped : module)
    return saved
  }

  async function replaceModuleFile(id: string, file: File) {
    const auth = useAuthStore()
    if (!auth.token) throw new Error('Please login first')
    const formData = new FormData()
    formData.append('material_file', file)
    const saved = await apiFetch<TeacherModuleResponse>(`/teacher/modules/${id}/replace-file`, {
      method: 'PUT',
      token: auth.token,
      body: formData,
    })
    const mapped = mapModuleResponse(saved)
    modules.value = modules.value.map(module => module.id === id ? mapped : module)
    return saved
  }

  async function downloadModuleFile(id: string, fileName?: string | null) {
    const auth = useAuthStore()
    if (!auth.token) throw new Error('Please login first')
    const response = await fetch(`${API_BASE_URL}/teacher/modules/${id}/download`, {
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    if (!response.ok) throw new Error('Unable to download file')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName || 'learning-material'
    link.click()
    URL.revokeObjectURL(url)
  }

  async function fetchAssessments(type: 'quiz' | 'activity') {
    const auth = useAuthStore()
    if (!auth.token) return

    const data = await apiFetch<TeacherAssessmentResponse[]>(`/teacher/assessments/${type}`, { token: auth.token })
    if (type === 'quiz') quizzes.value = data.map(mapQuizResponse)
    else activities.value = data.map(mapActivityResponse)
  }

  async function addQuiz(payload: {
    moduleId?: number | null
    topicId?: number | null
    title: string
    description: string
    quizType: string
    week: string
    timeLimit: string
    attemptsAllowed: number
    shuffleQuestions: boolean
    showAnswersAfterSubmission: boolean
    questions: AssessmentQuestion[]
  }) {
    const auth = useAuthStore()
    quizSaving.value = true
    quizError.value = ''

    try {
      if (!auth.token) throw new Error('Please login first')
      const saved = await apiFetch<TeacherAssessmentResponse>('/teacher/assessments/', {
        method: 'POST',
        token: auth.token,
        body: JSON.stringify({
          assessment_type: 'quiz',
          module_id: payload.moduleId ?? null,
          topic_id: payload.topicId ?? null,
          title: payload.title,
          description: payload.description,
          category: payload.quizType,
          week: payload.week,
          time_limit: payload.timeLimit,
          attempts_allowed: payload.attemptsAllowed,
          shuffle_questions: payload.shuffleQuestions,
          show_answers_after_submission: payload.showAnswersAfterSubmission,
          questions: payload.questions,
        }),
      })
      quizzes.value.unshift(mapQuizResponse(saved))
    } catch (err) {
      quizError.value = err instanceof Error ? err.message : 'Unable to create quiz'
      throw err
    } finally {
      quizSaving.value = false
    }
  }

  async function addActivity(payload: {
    classId?: number | null
    moduleId?: number | null
    topicId?: number | null
    title: string
    description: string
    activityType: string
    week: string
    timeLimit: string
    attemptsAllowed: number
    shuffleQuestions: boolean
    showAnswersAfterSubmission: boolean
    questions: AssessmentQuestion[]
  } | Omit<Activity, 'id'>) {
    const auth = useAuthStore()
    activitySaving.value = true
    activityError.value = ''

    try {
      if (!auth.token) {
        const localPayload = payload as Omit<Activity, 'id'>
        activities.value.unshift({ ...localPayload, id: `a${Date.now()}` })
        return
      }

      const formPayload = payload as {
        classId?: number | null
        moduleId?: number | null
        topicId?: number | null
        title: string
        description: string
        activityType?: string
        week?: string
        timeLimit?: string
        attemptsAllowed?: number
        shuffleQuestions?: boolean
        showAnswersAfterSubmission?: boolean
        questions?: AssessmentQuestion[]
      }

      const saved = await apiFetch<TeacherAssessmentResponse>('/teacher/assessments/', {
        method: 'POST',
        token: auth.token,
        body: JSON.stringify({
          assessment_type: 'activity',
          class_id: formPayload.classId ?? null,
          module_id: null,
          topic_id: null,
          title: formPayload.title,
          description: formPayload.description,
          category: formPayload.activityType ?? 'Activity',
          week: formPayload.week ?? '',
          time_limit: formPayload.timeLimit ?? '',
          attempts_allowed: formPayload.attemptsAllowed ?? 1,
          shuffle_questions: formPayload.shuffleQuestions ?? true,
          show_answers_after_submission: formPayload.showAnswersAfterSubmission ?? true,
          questions: formPayload.questions ?? [],
        }),
      })
      activities.value.unshift(mapActivityResponse(saved))
    } catch (err) {
      activityError.value = err instanceof Error ? err.message : 'Unable to create activity'
      throw err
    } finally {
      activitySaving.value = false
    }
  }

  function updateActivity(id: string, updates: Partial<Activity>) {
    const idx = activities.value.findIndex(a => a.id === id)
    if (idx !== -1) activities.value[idx] = { ...activities.value[idx], ...updates }
  }

  function deleteActivity(id: string) {
    activities.value = activities.value.filter(a => a.id !== id)
  }

  return {
    teacherName, modules, performers, recentActivities, students, quizzes, activities,
    classes, selectedClassId, selectedClass, hasClasses,
    modulesLoading, moduleSaving, moduleError, quizSaving, quizError, activitySaving, activityError,
    classesLoading, classSaving, classError, classStudents, classStudentsLoading,
    publishedModules, unpublishedModules, atRiskStudents,
    fetchModules, addModule, updateModule, replaceModuleFile, downloadModuleFile, deleteModule, fetchAssessments, addQuiz, addActivity, updateActivity, deleteActivity,
    fetchClasses, addClass, selectClass, deleteClass, fetchClassStudents,
  }
})

function mapClassResponse(cls: TeacherClassResponse): ClassInfo {
  return {
    id: String(cls.id),
    className: cls.class_name,
    subject: cls.subject,
    gradeLevel: cls.grade_level,
    section: cls.section,
    schoolYear: cls.school_year,
    studentCount: cls.student_count,
    createdAt: new Date(cls.created_at).toLocaleDateString(),
  }
}

function mapClassStudentResponse(student: ClassStudentResponse): ClassStudent {
  return {
    id: student.id,
    accountId: student.account_id,
    name: student.name,
    username: student.username,
    email: student.email,
    gradeLevel: student.grade_level,
    section: student.section,
    createdAt: student.created_at ? new Date(student.created_at).toLocaleDateString() : null,
  }
}

function mapModuleResponse(module: TeacherModuleResponse): Module {
  return {
    id: String(module.id),
    title: module.title,
    description: module.description,
    status: module.status,
    lastUpdated: new Date(module.updated_at).toLocaleDateString(),
    classId: module.class_id,
    contentType: module.content_type,
    week: module.week,
    behaviorRequired: module.behavior_required,
    estimatedTime: module.estimated_time,
    fileName: module.file_name,
    fileType: module.file_type,
    fileSize: module.file_size,
  }
}

function uploadModule(module: Omit<Module, 'id' | 'lastUpdated'> & { file?: File | null }, token: string) {
  const formData = new FormData()
  formData.append('title', module.title)
  formData.append('description', module.description)
  formData.append('content_type', module.contentType ?? '')
  formData.append('week', module.week ?? '')
  formData.append('status_value', module.status)
  formData.append('behavior_required', String(module.behaviorRequired ?? true))
  formData.append('estimated_time', module.estimatedTime ?? '')
  if (module.classId) formData.append('class_id', String(module.classId))
  if (module.file) formData.append('material_file', module.file)

  return apiFetch<TeacherModuleResponse>('/teacher/modules/upload', {
    method: 'POST',
    token,
    body: formData,
  })
}

function mapQuizResponse(assessment: TeacherAssessmentResponse): Quiz {
  return {
    id: String(assessment.id),
    title: assessment.title,
    description: assessment.description,
      module: assessment.week ?? 'No week',
    moduleId: assessment.module_id,
    topicId: assessment.topic_id,
    type: assessment.category ?? 'Quiz',
    difficulty: 'Medium',
    date: new Date(assessment.updated_at).toLocaleDateString(),
    questions: assessment.questions,
  }
}

function mapActivityResponse(assessment: TeacherAssessmentResponse): Activity {
  return {
    id: String(assessment.id),
    title: assessment.title,
    description: assessment.description,
    module: assessment.category ?? 'Activity',
    classId: assessment.class_id,
    moduleId: assessment.module_id,
    topicId: assessment.topic_id,
    dueDate: assessment.week ?? '',
    dueTime: assessment.time_limit ?? '',
    status: 'Not Started',
    questions: assessment.questions,
  }
}
