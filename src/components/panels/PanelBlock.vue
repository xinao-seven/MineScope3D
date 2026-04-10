<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<template>
  <section class="panel-block">
    <header class="panel-block__header">
      <div>
        <p class="panel-block__eyebrow">{{ subtitle || 'MineScope3D' }}</p>
        <h2>{{ title }}</h2>
      </div>
      <span class="panel-block__mark"></span>
    </header>
    <slot />
  </section>
</template>
