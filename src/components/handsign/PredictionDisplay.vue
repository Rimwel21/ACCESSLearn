<template>
  <section class="border-[3px] border-black bg-white p-4" style="box-shadow:4px 4px 0 #000">
    <div class="flex items-center justify-between gap-3 border-b-[3px] border-black pb-3">
      <h2 class="font-display text-sm font-black uppercase tracking-widest">Answer</h2>
      <ConfidenceBadge
        v-if="detection?.detected"
        :prediction="detection.prediction"
        :confidence="detection.confidence"
        :threshold-met="detection.threshold_met"
      />
    </div>

    <textarea
      v-if="!signMode"
      v-model="textAnswer"
      rows="5"
      class="mt-4 w-full resize-none border-[3px] border-black bg-white p-3 text-sm font-bold outline-none focus:bg-[#F7FAFF]"
      placeholder="Type your answer"
    />
    <div v-else class="mt-4 min-h-[132px] border-[3px] border-black bg-[#F7FAFF] p-4">
      <div class="break-words font-display text-3xl font-black leading-tight">{{ answer || '...' }}</div>
      <div class="mt-3 font-mono text-[10px] font-bold uppercase tracking-wide text-gray-500">
        {{ detection?.detected ? 'Detected hand sign input' : 'Waiting for a hand sign' }}
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import ConfidenceBadge from '@/components/handsign/ConfidenceBadge.vue'
import type { CameraDetectionResponse } from '@/types/handsign'

defineProps<{
  signMode: boolean
  answer: string
  detection: CameraDetectionResponse | null
}>()

const textAnswer = defineModel<string>('textAnswer', { required: true })
</script>
