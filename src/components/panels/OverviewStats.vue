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
