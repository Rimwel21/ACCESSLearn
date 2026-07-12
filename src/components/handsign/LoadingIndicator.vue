<template>
  <div class="inline-flex items-center gap-2 font-mono text-[10px] font-black uppercase tracking-wide text-gray-600">
    <span class="h-2.5 w-2.5 animate-pulse border-[2px] border-black bg-[#1565FF]" aria-hidden="true"></span>
    {{ label }}
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ label?: string }>(), {
  label: 'Processing',
})
</script>
