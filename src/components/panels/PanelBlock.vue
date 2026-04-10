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

<style scoped>
.panel-block {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  background: var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
  transition: opacity 0.2s ease, transform 0.24s ease;
}

.panel-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(96, 165, 250, 0.2);
}

.panel-block__header h2 {
  margin: 0;
  color: #f5fbff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0;
}

.panel-block__eyebrow {
  margin: 0 0 3px;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--muted);
}

.panel-block__mark {
  width: 34px;
  height: 2px;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--blue), var(--cyan));
}
</style>
