<template>
  <div v-if="prediction" :class="['border-[3px] border-black px-3 py-2 text-xs font-black', thresholdMet ? 'bg-[#FFE135]' : 'bg-white']">
    {{ prediction }} {{ confidencePercent }}%
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  prediction: string | null
  confidence: number
  thresholdMet: boolean
}>()

const confidencePercent = computed(() => Math.round(props.confidence * 100))
</script>
