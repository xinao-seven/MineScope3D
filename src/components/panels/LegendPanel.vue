<script setup lang="ts">
import type { RasterLayer } from '../../types/dashboard'

defineProps<{
  raster: RasterLayer | null
}>()
</script>

<template>
  <div v-if="raster" class="legend-list">
    <div v-for="item in raster.legend_config" :key="item.label" class="legend-row">
      <span class="legend-row__color" :style="{ background: item.color }"></span>
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
    </div>
  </div>
  <p v-else class="empty-text">暂无专题图图例</p>
</template>
