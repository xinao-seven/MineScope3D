<script setup lang="ts">
import { computed } from 'vue'
import type { Borehole, BoundaryRegion, RasterLayer, SelectionState } from '../../types/dashboard'

const props = defineProps<{
  selection: SelectionState
}>()

const selectedBorehole = computed(getSelectedBorehole)
const selectedBoundary = computed(getSelectedBoundary)
const selectedRaster = computed(getSelectedRaster)

/** 获取当前选中的钻孔对象。 */
function getSelectedBorehole(): Borehole | null {
  return props.selection.type === 'borehole' ? (props.selection.item as Borehole) : null
}

/** 获取当前选中的边界对象。 */
function getSelectedBoundary(): BoundaryRegion | null {
  return props.selection.type === 'boundary' ? (props.selection.item as BoundaryRegion) : null
}

/** 获取当前选中的专题图对象。 */
function getSelectedRaster(): RasterLayer | null {
  return props.selection.type === 'raster' ? (props.selection.item as RasterLayer) : null
}

/** 计算分层柱状示意图高度占比。 */
function getLayerHeight(layerThickness: number, totalDepth: number): string {
  if (!totalDepth) {
    return '0%'
  }
  return `${(layerThickness / totalDepth) * 100}%`
}

/** 判断分层是否为有效厚度。 */
function isVisibleLayer(layerThickness: number): boolean {
  return layerThickness > 0
}
</script>

<template>
  <div class="detail-panel">
    <template v-if="selectedBorehole">
      <div class="detail-hero">
        <span>当前钻孔</span>
        <h3>{{ selectedBorehole.name }}</h3>
        <p>{{ selectedBorehole.borehole_code }} · {{ selectedBorehole.workface_name }}</p>
      </div>
      <dl class="detail-grid">
        <div><dt>经度</dt><dd>{{ selectedBorehole.longitude.toFixed(5) }}</dd></div>
        <div><dt>纬度</dt><dd>{{ selectedBorehole.latitude.toFixed(5) }}</dd></div>
        <div><dt>高程</dt><dd>{{ selectedBorehole.elevation }}m</dd></div>
        <div><dt>总深度</dt><dd>{{ selectedBorehole.depth_total }}m</dd></div>
      </dl>
      <div class="strata-view">
        <div class="strata-view__bar">
          <span
            v-for="layer in selectedBorehole.layers"
            :key="layer.id"
            :class="{ 'is-zero': !isVisibleLayer(layer.thickness) }"
            :style="{ flexBasis: getLayerHeight(layer.thickness, selectedBorehole.depth_total), background: layer.color }"
            :title="`${layer.layer_name} ${layer.thickness}m`"
          ></span>
        </div>
        <div class="strata-view__table">
          <div v-for="layer in selectedBorehole.layers" :key="layer.id">
            <strong>{{ layer.layer_name }}</strong>
            <span>{{ layer.top_depth }}m - {{ layer.bottom_depth }}m</span>
            <em>{{ layer.thickness }}m</em>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="selectedBoundary">
      <div class="detail-hero">
        <span>当前边界</span>
        <h3>{{ selectedBoundary.name }}</h3>
        <p>{{ selectedBoundary.type }} · SHP 边界对象</p>
      </div>
      <dl class="detail-grid">
        <div><dt>面积</dt><dd>{{ selectedBoundary.area }}km²</dd></div>
        <div><dt>周长</dt><dd>{{ selectedBoundary.perimeter }}km</dd></div>
        <div><dt>钻孔数</dt><dd>{{ selectedBoundary.borehole_count }}</dd></div>
        <div><dt>节点数</dt><dd>{{ selectedBoundary.coordinates.length }}</dd></div>
      </dl>
      <div class="property-list">
        <div v-for="(value, key) in selectedBoundary.properties" :key="key">
          <span>{{ key }}</span>
          <strong>{{ value }}</strong>
        </div>
      </div>
    </template>

    <template v-else-if="selectedRaster">
      <div class="detail-hero">
        <span>当前专题图</span>
        <h3>{{ selectedRaster.name }}</h3>
        <p>{{ selectedRaster.type }} · {{ selectedRaster.time_tag }}</p>
      </div>
      <p class="detail-copy">{{ selectedRaster.description }}</p>
      <dl class="detail-grid">
        <div><dt>默认透明度</dt><dd>{{ Math.round(selectedRaster.opacity * 100) }}%</dd></div>
        <div><dt>图例分级</dt><dd>{{ selectedRaster.legend_config.length }}</dd></div>
      </dl>
    </template>

    <p v-else class="empty-text">点击地图对象后查看属性、分层与图例信息。</p>
  </div>
</template>

<style scoped>
.detail-hero {
  padding: 10px;
  border: 1px solid rgba(125, 211, 252, 0.24);
  border-radius: 8px;
  background: var(--panel-strong);
}

.detail-hero span,
.detail-hero p,
.detail-copy,
.empty-text {
  color: var(--muted);
}

.detail-hero h3 {
  margin: 4px 0;
  color: #f5fbff;
  font-size: 17px;
}

.detail-hero p,
.detail-copy,
.empty-text {
  margin: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin: 8px 0;
}

.detail-grid div {
  padding: 8px;
  border: 1px solid rgba(125, 211, 252, 0.18);
  border-radius: 8px;
  background: rgba(6, 20, 48, 0.5);
}

.detail-grid dt,
.detail-grid dd {
  margin: 0;
}

.detail-grid dt {
  color: var(--muted);
  font-size: 12px;
}

.detail-grid dd {
  margin-top: 4px;
  color: var(--amber);
  font-weight: 700;
}

.strata-view {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 9px;
  min-height: 220px;
}

.strata-view__bar {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  border: 1px solid rgba(96, 165, 250, 0.32);
  border-radius: 8px;
  background: rgba(3, 13, 32, 0.76);
}

.strata-view__bar span {
  display: block;
  flex: 0 0 auto;
  min-height: 1px;
}

.strata-view__bar span.is-zero {
  min-height: 2px;
  opacity: 0.36;
}

.strata-view__table,
.property-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.strata-view__table {
  overflow: auto;
  max-height: 220px;
}

.strata-view__table div,
.property-list div {
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

.strata-view__table div {
  align-items: flex-start;
  padding: 7px 8px;
}

.strata-view__table strong,
.property-list strong {
  color: #f5fbff;
}

.strata-view__table span,
.strata-view__table em,
.property-list span {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
}

.empty-text {
  padding: 12px;
}
</style>
