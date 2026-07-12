<template>
  <main class="grid min-h-screen place-items-center bg-surface px-4">
    <section class="card max-w-md p-8 text-center">
      <p class="eyebrow">Access Required</p>
      <h1 class="font-display text-3xl font-bold">Please login first</h1>
      <p class="mt-3 text-sm leading-6 text-ink-soft">
        This page needs an authenticated ACCESS Learn account.
      </p>
      <RouterLink to="/login" class="btn-primary mt-6 inline-flex">Go to login</RouterLink>
    </section>
  </main>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
