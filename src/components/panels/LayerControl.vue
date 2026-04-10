<script setup lang="ts">
import type { LayerKey, LayerState } from '../../types/dashboard'

defineProps<{
  layers: LayerState[]
}>()

const emit = defineEmits<{
  toggleLayer: [key: LayerKey, visible: boolean]
  opacityChange: [key: LayerKey, opacity: number]
  locateLayer: [key: LayerKey]
}>()

/** 切换图层显隐状态。 */
function handleLayerToggle(layer: LayerState, visible: string | number | boolean) {
  emit('toggleLayer', layer.key, Boolean(visible))
}

/** 修改图层透明度。 */
function handleOpacityChange(layer: LayerState, opacity: number) {
  emit('opacityChange', layer.key, opacity)
}

/** 通知地图定位到指定图层范围。 */
function handleLocateLayer(layer: LayerState) {
  emit('locateLayer', layer.key)
}
</script>

<template>
  <div class="layer-list">
    <article v-for="layer in layers" :key="layer.key" class="layer-row">
      <div class="layer-row__main">
        <div>
          <strong>{{ layer.name }}</strong>
          <span>{{ layer.description }}</span>
        </div>
        <el-switch
          :model-value="layer.visible"
          active-color="#23d18b"
          inactive-color="#3b4543"
          @change="handleLayerToggle(layer, $event)"
        />
      </div>
      <div class="layer-row__tools">
        <small>{{ layer.count }} 项</small>
        <button type="button" @click="handleLocateLayer(layer)">定位</button>
      </div>
      <el-slider
        v-if="layer.key === 'raster' || layer.key.includes('Boundary')"
        :model-value="layer.opacity"
        :min="0.1"
        :max="1"
        :step="0.02"
        :show-tooltip="false"
        @input="handleOpacityChange(layer, Number($event))"
      />
    </article>
  </div>
</template>
