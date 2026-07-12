<template>
  <main class="auth-page">
    <section class="auth-card max-w-3xl">
      <p class="eyebrow">{{ auth.role }}</p>
      <h1 class="auth-title">{{ roleLabel }} Profile Setup</h1>

      <div v-if="profile.loading" class="empty-state">Loading your existing profile...</div>

      <form v-else class="form-stack" @submit.prevent="submitProfile">
        <div class="grid gap-4 md:grid-cols-2">
          <template v-if="auth.role === 'student'">
            <div>
              <label class="field-label" for="name">Name</label>
              <input id="name" v-model.trim="studentForm.name" class="input-field" minlength="5" maxlength="100" required />
            </div>
            <div>
              <label class="field-label" for="age">Age</label>
              <input id="age" v-model.number="studentForm.age" class="input-field" type="number" min="1" max="120" required />
            </div>
            <div>
              <label class="field-label" for="sex">Sex</label>
              <select id="sex" v-model="studentForm.sex" class="input-field" required>
                <option value="">Select sex</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>
            <div>
              <label class="field-label" for="grade-level">Grade Level</label>
              <select id="grade-level" v-model="studentForm.grade_level" class="input-field" required>
                <option value="">Select grade</option>
                <option v-for="grade in gradeOptions" :key="grade.value" :value="grade.value">{{ grade.label }}</option>
              </select>
            </div>
            <div>
              <label class="field-label" for="section">Section</label>
              <input id="section" v-model.trim="studentForm.section" class="input-field" maxlength="250" required />
            </div>
            <div>
              <label class="field-label" for="student-type">Student Type</label>
              <select id="student-type" v-model="studentForm.student_type" class="input-field" required>
                <option value="">Select type</option>
                <option value="regular">Regular</option>
                <option value="hearing impaired">Hearing Impaired</option>
              </select>
            </div>
            <div>
              <label class="field-label" for="guardian">Guardian Name</label>
              <input id="guardian" v-model.trim="studentForm.guardians_name" class="input-field" />
            </div>
            <div>
              <label class="field-label" for="guardian-contact">Guardian Contact</label>
              <input id="guardian-contact" v-model.trim="studentForm.guardians_contact_no" class="input-field" />
            </div>
            <div class="md:col-span-2">
              <label class="field-label" for="student-address">Address</label>
              <textarea id="student-address" v-model.trim="studentForm.address" class="input-field min-h-24 resize-y" />
            </div>
          </template>

          <template v-else>
            <div>
              <label class="field-label" for="teacher-name">Name</label>
              <input id="teacher-name" v-model.trim="teacherForm.name" class="input-field" minlength="5" maxlength="50" required />
            </div>
            <div>
              <label class="field-label" for="teacher-age">Age</label>
              <input id="teacher-age" v-model.number="teacherForm.age" class="input-field" type="number" min="18" max="100" required />
            </div>
            <div>
              <label class="field-label" for="teacher-sex">Sex</label>
              <select id="teacher-sex" v-model="teacherForm.sex" class="input-field" required>
                <option value="">Select sex</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>
            <div>
              <label class="field-label" for="teacher-contact">Contact Number</label>
              <input id="teacher-contact" v-model.trim="teacherForm.contact_no" class="input-field" minlength="11" maxlength="11" required />
            </div>
            <fieldset class="md:col-span-2 rounded-lg border border-gray-200 bg-white p-3">
              <legend class="field-label px-1">Grade Levels Handled</legend>
              <div class="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                <label v-for="grade in gradeOptions" :key="grade.value" class="flex items-center gap-2 text-sm font-semibold text-ink">
                  <input v-model="teacherForm.grade_level_handles" type="checkbox" :value="grade.value" />
                  {{ grade.label }}
                </label>
              </div>
            </fieldset>
            <div class="md:col-span-2">
              <label class="field-label" for="teacher-address">Address</label>
              <textarea id="teacher-address" v-model.trim="teacherForm.address" class="input-field min-h-24 resize-y" minlength="5" maxlength="150" required />
            </div>
          </template>
        </div>

        <div>
          <label class="field-label" for="profile-image">Profile Image</label>
          <input id="profile-image" class="input-field" type="file" accept="image/png,image/jpeg,image/webp" @change="previewImage" />
        </div>

        <div class="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-3">
          <img v-if="previewUrl" :src="previewUrl" alt="Profile preview" class="h-16 w-16 rounded-full object-cover" />
          <div v-else class="grid h-16 w-16 place-items-center rounded-full bg-brand-blue text-xl font-bold text-white">
            {{ profile.initial }}
          </div>
          <p class="text-sm text-ink-soft">Image upload runs after the profile is saved.</p>
        </div>

        <p v-if="profile.error" class="status-error" role="alert">{{ profile.error }}</p>
        <p v-if="message" class="status-success" role="status">{{ message }}</p>

        <button type="submit" class="btn-primary w-full justify-center rounded-lg" :disabled="profile.saving">
          {{ profile.saving ? 'Saving...' : profile.profile ? 'Update profile' : 'Save profile' }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()

const imageFile = ref<File | null>(null)
const previewUrl = ref('')
const message = ref('')

const gradeOptions = [
  { value: 'grade_1', label: 'Grade 1' },
  { value: 'grade_2', label: 'Grade 2' },
  { value: 'grade_3', label: 'Grade 3' },
  { value: 'grade_4', label: 'Grade 4' },
  { value: 'grade_5', label: 'Grade 5' },
  { value: 'grade_6', label: 'Grade 6' },
] as const

const studentForm = ref({
  name: '',
  age: null as number | null,
  sex: '',
  grade_level: '',
  section: '',
  student_type: '',
  guardians_name: '',
  guardians_contact_no: '',
  address: '',
})

const teacherForm = ref({
  name: '',
  age: null as number | null,
  sex: '',
  contact_no: '',
  grade_level_handles: [] as string[],
  address: '',
})

const roleLabel = computed(() => auth.role === 'student' ? 'Student' : 'Teacher')

onMounted(async () => {
  const existing = await profile.fetchProfile()
  if (!existing) return

  if (auth.role === 'student' && 'student_type' in existing) {
    studentForm.value = {
      name: existing.name ?? '',
      age: existing.age ?? null,
      sex: existing.sex ?? '',
      grade_level: existing.grade_level ?? '',
      section: existing.section ?? '',
      student_type: existing.student_type ?? '',
      guardians_name: existing.guardians_name ?? '',
      guardians_contact_no: existing.guardians_contact_no ?? '',
      address: existing.address ?? '',
    }
  }

  if (auth.role === 'teacher' && 'contact_no' in existing) {
    teacherForm.value = {
      name: existing.name ?? '',
      age: existing.age ?? null,
      sex: existing.sex ?? '',
      contact_no: existing.contact_no ?? '',
      grade_level_handles: existing.handle_grade_levels?.map(grade => grade.grade_level_handles) ?? [],
      address: existing.address ?? '',
    }
  }

  previewUrl.value = profile.image?.file_url ?? ''
})

function previewImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  imageFile.value = file

  if (previewUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }

  previewUrl.value = file ? URL.createObjectURL(file) : profile.image?.file_url ?? ''
}

async function submitProfile() {
  if (auth.role === 'teacher' && teacherForm.value.grade_level_handles.length === 0) {
    profile.error = 'Select at least one grade level handled.'
    return
  }

  const payload = auth.role === 'student'
    ? normalizeStudentPayload()
    : teacherForm.value

  await profile.saveProfile(payload, imageFile.value)
  message.value = 'Profile saved. Opening dashboard...'

  setTimeout(() => {
    router.push(auth.role === 'student' ? '/student/dashboard' : '/teacher/class')
  }, 500)
}

function normalizeStudentPayload() {
  return {
    ...studentForm.value,
    guardians_name: studentForm.value.guardians_name || null,
    guardians_contact_no: studentForm.value.guardians_contact_no || null,
    address: studentForm.value.address || null,
  }
}
</script>
