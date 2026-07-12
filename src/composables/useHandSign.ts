import { computed, onBeforeUnmount, ref } from 'vue'
import { detectCameraFrame, handsignErrorMessage, resetCameraSession } from '@/services/handsign'
import type { CameraDetectionResponse } from '@/types/handsign'

const FRAME_INTERVAL_MS = 140

export function useHandSign() {
  const videoRef = ref<HTMLVideoElement | null>(null)
  const canvasRef = ref<HTMLCanvasElement | null>(null)
  const sessionId = crypto.randomUUID()
  const detection = ref<CameraDetectionResponse | null>(null)
  const isRunning = ref(false)
  const isDetecting = ref(false)
  const error = ref('')
  const retryMessage = ref('')
  const answer = computed(() => detection.value?.confirmed_text ?? '')
  let stream: MediaStream | null = null
  let timer: number | null = null
  let inFlight = false
  let failureCount = 0

  async function start() {
    if (isRunning.value) return
    try {
      error.value = ''
      retryMessage.value = ''
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 960 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      })
      if (!videoRef.value) {
        stop()
        error.value = 'Camera view is not ready yet. Please try again.'
        return
      }
      videoRef.value.srcObject = stream
      await videoRef.value.play()
      isRunning.value = true
      timer = window.setInterval(captureAndDetect, FRAME_INTERVAL_MS)
    } catch {
      error.value = 'Camera permission is required to use Sign Language Mode.'
      stop()
    }
  }

  function stop() {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
    stream?.getTracks().forEach((track) => track.stop())
    stream = null
    isRunning.value = false
    isDetecting.value = false
    if (videoRef.value) videoRef.value.srcObject = null
  }

  async function reset() {
    detection.value = null
    failureCount = 0
    retryMessage.value = ''
    await resetCameraSession(sessionId).catch(() => null)
  }

  async function captureAndDetect() {
    if (inFlight || !videoRef.value || !canvasRef.value || videoRef.value.readyState < 2) return
    inFlight = true
    isDetecting.value = true
    try {
      const video = videoRef.value
      const canvas = canvasRef.value
      const maxWidth = 640
      const scale = Math.min(1, maxWidth / video.videoWidth)
      canvas.width = Math.round(video.videoWidth * scale)
      canvas.height = Math.round(video.videoHeight * scale)
      const context = canvas.getContext('2d')
      if (!context) return
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      const image = canvas.toDataURL('image/jpeg', 0.72)
      detection.value = await detectCameraFrame(sessionId, image)
      failureCount = 0
      retryMessage.value = ''
      error.value = ''
    } catch (err) {
      failureCount += 1
      error.value = handsignErrorMessage(err)
      retryMessage.value = failureCount >= 2 ? 'Still trying. You can keep the camera on or switch to text input.' : 'Retrying detection...'
    } finally {
      inFlight = false
      isDetecting.value = false
    }
  }

  onBeforeUnmount(stop)

  return {
    videoRef,
    canvasRef,
    detection,
    answer,
    isRunning,
    isDetecting,
    error,
    retryMessage,
    start,
    stop,
    reset,
  }
}
