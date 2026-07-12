<template>
  <label class="flex items-center justify-between gap-4 border-[3px] border-black bg-white p-4" style="box-shadow:4px 4px 0 #000">
    <span>
      <span class="block text-sm font-black">Sign Language Mode</span>
      <span class="mt-1 block font-mono text-[10px] font-bold uppercase tracking-wide text-gray-500">{{ modeLabel }}</span>
    </span>
    <input v-model="enabled" type="checkbox" class="sr-only" />
    <span
      :class="[
        'relative h-8 w-16 flex-shrink-0 border-[3px] border-black transition-colors',
        enabled ? 'bg-[#FFE135]' : 'bg-gray-200',
      ]"
      aria-hidden="true"
    >
      <span
        :class="[
          'absolute top-1 h-4 w-4 border-[2px] border-black bg-white transition-transform',
          enabled ? 'translate-x-9' : 'translate-x-1',
        ]"
      />
    </span>
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const enabled = defineModel<boolean>({ required: true })

const modeLabel = computed(() => enabled.value ? 'Camera answers enabled' : 'Text answers only')
</script>
