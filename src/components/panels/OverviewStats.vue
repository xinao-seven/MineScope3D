<script setup lang="ts">
import type { DashboardOverview } from '../../types/dashboard'

defineProps<{
  overview: DashboardOverview
}>()
</script>

<template>
  <div class="stat-grid">
    <article class="stat-tile">
      <span>钻孔总数</span>
      <strong>{{ overview.boreholeTotal }}</strong>
    </article>
    <article class="stat-tile">
      <span>工作面</span>
      <strong>{{ overview.workfaceTotal }}</strong>
    </article>
    <article class="stat-tile">
      <span>边界对象</span>
      <strong>{{ overview.boundaryTotal }}</strong>
    </article>
    <article class="stat-tile">
      <span>专题图层</span>
      <strong>{{ overview.rasterTotal }}</strong>
    </article>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.stat-tile {
  min-height: 58px;
  padding: 9px;
  border: 1px solid rgba(125, 211, 252, 0.2);
  border-radius: 8px;
  background: rgba(6, 20, 48, 0.48);
}

.stat-tile span {
  color: var(--muted);
}

.stat-tile strong {
  display: block;
  margin-top: 3px;
  color: var(--amber);
  font-size: 24px;
  line-height: 1;
}
</style>
