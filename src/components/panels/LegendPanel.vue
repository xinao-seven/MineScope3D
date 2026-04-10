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

<style scoped>
.legend-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.legend-row {
  border: 1px solid rgba(125, 211, 252, 0.18);
  border-radius: 8px;
  background: rgba(5, 18, 42, 0.46);
  min-height: 34px;
  padding: 7px 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.legend-row span {
  color: var(--muted);
  font-size: 12px;
}

.legend-row strong {
  color: #f5fbff;
}

.legend-row__color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  box-shadow: 0 0 16px currentColor;
}

.empty-text {
  margin: 0;
  padding: 12px;
  color: var(--muted);
}
</style>
