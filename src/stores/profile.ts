import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { ApiError, apiFetch } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type Role = 'student' | 'teacher'
type StudentType = 'regular' | 'hearing impaired'
type UserSex = 'Male' | 'Female'
type GradeLevel = 'grade_1' | 'grade_2' | 'grade_3' | 'grade_4' | 'grade_5' | 'grade_6'

export interface StudentProfile {
  id: number
  name: string
  age: number | null
  sex: UserSex | null
  grade_level: GradeLevel | null
  section: string | null
  student_type: StudentType
  account_id: number
  profile_image_id: number | null
  guardians_name: string | null
  guardians_contact_no: string | null
  address: string | null
  created_at: string
  updated_at: string
}

export interface TeacherProfile {
  id: number
  account_id: number
  profile_image_id: number | null
  name: string
  age: number | null
  sex: UserSex | null
  handle_grade_levels: Array<{ grade_level_handles: GradeLevel }>
  contact_no: string
  email_address: string
  address: string
  created_at: string
  updated_at: string
}

export interface FileProfile {
  id: number | null
  filename: string
  file_type: string
  file_url: string
  file_category: string
  is_default?: boolean
  created_at: string | null
  updated_at: string | null
}

type Profile = StudentProfile | TeacherProfile

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<Profile | null>(loadJson<Profile>('profile_data'))
  const image = ref<FileProfile | null>(loadJson<FileProfile>('profile_image'))
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')

  const displayName = computed(() => profile.value?.name ?? 'ACCESS Learn user')
  const initial = computed(() => displayName.value.charAt(0).toUpperCase())

  async function fetchProfile() {
    const auth = useAuthStore()

    if (!auth.token || !auth.role) return null

    loading.value = true
    error.value = ''

    try {
      profile.value = await apiFetch<Profile>(`/profile/${auth.role}/get_profile`, {
        token: auth.token,
      })
      localStorage.setItem('profile_data', JSON.stringify(profile.value))
      auth.setProfileCompleted(true)

      await fetchImage({ ignoreMissing: true })

      return profile.value
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        profile.value = null
        image.value = null
        localStorage.removeItem('profile_data')
        localStorage.removeItem('profile_image')
        auth.setProfileCompleted(false)
        return null
      }

      error.value = err instanceof Error ? err.message : 'Unable to load profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchImage(options: { ignoreMissing?: boolean } = {}) {
    const auth = useAuthStore()

    if (!auth.token) return null

    try {
      image.value = await apiFetch<FileProfile>('/profile/image/get_image', {
        token: auth.token,
      })
      localStorage.setItem('profile_image', JSON.stringify(image.value))
      return image.value
    } catch (err) {
      if (options.ignoreMissing && err instanceof ApiError && err.status === 404) {
        image.value = null
        localStorage.removeItem('profile_image')
        return null
      }

      throw err
    }
  }

  async function saveProfile(payload: Record<string, unknown>, imageFile: File | null) {
    const auth = useAuthStore()

    if (!auth.token || !auth.role) {
      throw new Error('Please login first')
    }

    saving.value = true
    error.value = ''

    const exists = Boolean(profile.value)
    const method = exists ? 'PATCH' : 'POST'
    const action = exists ? 'update' : 'create'

    try {
      profile.value = await apiFetch<Profile>(`/profile/${auth.role}/${action}`, {
        method,
        token: auth.token,
        body: JSON.stringify(payload),
      })

      localStorage.setItem('profile_data', JSON.stringify(profile.value))
      auth.setProfileCompleted(true)

      if (imageFile) {
        await uploadImage(imageFile)
      }

      return profile.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unable to save profile'
      throw err
    } finally {
      saving.value = false
    }
  }

  async function uploadImage(file: File) {
    const auth = useAuthStore()
    const formData = new FormData()
    formData.append('image', file)

    image.value = await apiFetch<FileProfile>('/profile/image/upload', {
      method: 'PUT',
      token: auth.token,
      body: formData,
    })
    localStorage.setItem('profile_image', JSON.stringify(image.value))

    return image.value
  }

  async function deleteImage() {
    const auth = useAuthStore()

    await apiFetch<{ detail: string }>('/profile/image/delete', {
      method: 'DELETE',
      token: auth.token,
    })

    image.value = null
    localStorage.removeItem('profile_image')
  }

  function clear() {
    profile.value = null
    image.value = null
    error.value = ''
  }

  return {
    profile,
    image,
    loading,
    saving,
    error,
    displayName,
    initial,
    fetchProfile,
    fetchImage,
    saveProfile,
    uploadImage,
    deleteImage,
    clear,
  }
})

function loadJson<T>(key: string) {
  const raw = localStorage.getItem(key)
  if (!raw) return null

  try {
    return JSON.parse(raw) as T
  } catch {
    localStorage.removeItem(key)
    return null
  }
}
