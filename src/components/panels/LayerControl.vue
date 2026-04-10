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
				<el-switch :model-value="layer.visible" active-color="#23d18b" inactive-color="#3b4543"
					@change="handleLayerToggle(layer, $event)" />
			</div>
			<div class="layer-row__tools">
				<small>{{ layer.count }} 项</small>
				<button type="button" @click="handleLocateLayer(layer)">定位</button>
			</div>
			<el-slider v-if="layer.key === 'raster' || layer.key.includes('Boundary')" :model-value="layer.opacity"
				:min="0.1" :max="1" :step="0.02" :show-tooltip="false"
				@input="handleOpacityChange(layer, Number($event))" />
		</article>
	</div>
</template>

<style scoped>
.layer-list {
	display: flex;
	flex-direction: column;
	gap: 7px;
}

.layer-row {
	border: 1px solid rgba(125, 211, 252, 0.18);
	border-radius: 8px;
	background: rgba(5, 18, 42, 0.46);
	padding: 9px;
}

.layer-row__main,
.layer-row__tools {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
}

.layer-row__main strong {
	display: block;
	color: #f5fbff;
}

.layer-row__main span {
	display: block;
	margin-top: 2px;
	font-size: 12px;
	color: var(--muted);
}

.layer-row__tools {
	margin-top: 7px;
}

.layer-row__tools small {
	color: var(--cyan);
}

.layer-row__tools button {
	height: 28px;
	padding: 0 12px;
	border: 1px solid rgba(56, 189, 248, 0.52);
	border-radius: 6px;
	background: rgba(37, 99, 235, 0.24);
	cursor: pointer;
	color: var(--text);
}

:deep(.el-slider) {
	--el-slider-main-bg-color: var(--green);
	--el-slider-runway-bg-color: rgba(96, 165, 250, 0.2);
	--el-slider-button-size: 14px;
}

:deep(.el-switch) {
	--el-switch-border-color: rgba(125, 211, 252, 0.32);
}
</style>
