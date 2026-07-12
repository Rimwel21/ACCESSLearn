import axios from 'axios'
import { API_BASE_URL } from '@/lib/api'
import type { CameraDetectionResponse, PredictionResponse } from '@/types/handsign'

const handsignApi = axios.create({
  baseURL: `${API_BASE_URL}/api/handsign`,
  timeout: 10000,
})

handsignApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function checkHandsignHealth() {
  const response = await handsignApi.get<{ status: string; classes: string[] }>('/health')
  return response.data
}

export async function predictHandsignImage(image: string): Promise<PredictionResponse> {
  const response = await handsignApi.post<PredictionResponse>('/predict', { image })
  return response.data
}

export async function detectCameraFrame(sessionId: string, image: string): Promise<CameraDetectionResponse> {
  const response = await handsignApi.post<CameraDetectionResponse>('/detect', {
    session_id: sessionId,
    image,
  })
  return response.data
}

export async function resetCameraSession(sessionId: string): Promise<void> {
  await handsignApi.post('/reset', { session_id: sessionId })
}

export function handsignErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') return 'Detection timed out. Please try again.'
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return 'Detection service is unavailable.'
  }
  return error instanceof Error ? error.message : 'Detection failed.'
}
