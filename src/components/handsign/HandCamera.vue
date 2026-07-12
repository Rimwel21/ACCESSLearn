<template>
  <section class="border-[3px] border-black bg-white p-4" style="box-shadow:5px 5px 0 #000">
    <div class="mb-3 flex items-center justify-between gap-3">
      <h2 class="font-display text-sm font-black uppercase tracking-widest">Camera</h2>
      <LoadingIndicator v-if="isDetecting" label="Detecting" />
    </div>

    <div class="relative aspect-[4/3] overflow-hidden border-[3px] border-black bg-gray-100">
      <video ref="videoRef" class="h-full w-full -scale-x-100 object-cover" muted playsinline aria-label="Live hand sign camera feed"></video>
      <canvas ref="canvasRef" hidden></canvas>

      <div v-if="!isRunning" class="absolute inset-0 grid place-items-center bg-white/90 p-6 text-center">
        <button class="border-[3px] border-black bg-[#FFE135] px-5 py-3 text-xs font-black" style="box-shadow:4px 4px 0 #000" type="button" @click="$emit('start')">
          Start Camera
        </button>
      </div>

      <div
        v-if="detection?.box"
        class="absolute border-[4px] border-[#FFE135]"
        :class="{ 'border-[#22C55E]': detection.threshold_met }"
        :style="boxStyle"
        aria-hidden="true"
      ></div>

      <div v-if="detection?.detected" class="absolute left-3 top-3">
        <ConfidenceBadge :prediction="detection.prediction" :confidence="detection.confidence" :threshold-met="detection.threshold_met" />
      </div>
      <div v-else-if="isRunning" class="absolute left-3 top-3 border-[3px] border-black bg-white px-3 py-2 font-mono text-[10px] font-black uppercase">
        No hand detected
      </div>
    </div>

    <p v-if="error" class="mt-3 border-[3px] border-black bg-[#FFC2C2] px-3 py-2 text-xs font-black text-red-700" role="alert">{{ error }}</p>
    <p v-if="retryMessage" class="mt-2 font-mono text-[10px] font-bold uppercase tracking-wide text-gray-600">{{ retryMessage }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ConfidenceBadge from '@/components/handsign/ConfidenceBadge.vue'
import LoadingIndicator from '@/components/handsign/LoadingIndicator.vue'
import type { CameraDetectionResponse } from '@/types/handsign'

const props = defineProps<{
  detection: CameraDetectionResponse | null
  isRunning: boolean
  isDetecting: boolean
  error: string
  retryMessage: string
}>()

defineEmits<{ start: [] }>()

const videoRef = defineModel<HTMLVideoElement | null>('videoRef', { required: true })
const canvasRef = defineModel<HTMLCanvasElement | null>('canvasRef', { required: true })

const boxStyle = computed(() => {
  const box = props.detection?.box
  if (!box || !props.detection) return {}
  const width = props.detection.frame_width
  const height = props.detection.frame_height
  const left = ((width - box.x_max) / width) * 100
  const top = (box.y_min / height) * 100
  const boxWidth = ((box.x_max - box.x_min) / width) * 100
  const boxHeight = ((box.y_max - box.y_min) / height) * 100
  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${boxWidth}%`,
    height: `${boxHeight}%`,
  }
})
</script>
