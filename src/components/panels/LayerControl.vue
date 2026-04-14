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

/** 处理可见性开关原生事件。 */
function handleLayerToggleEvent(layer: LayerState, event: Event) {
	const target = event.target as HTMLInputElement | null
	handleLayerToggle(layer, target?.checked ?? false)
}

/** 修改图层透明度。 */
function handleOpacityChange(layer: LayerState, opacity: number) {
	emit('opacityChange', layer.key, opacity)
}

/** 处理透明度滑条原生事件。 */
function handleOpacityInput(layer: LayerState, event: Event) {
	const target = event.target as HTMLInputElement | null
	handleOpacityChange(layer, Number(target?.value ?? layer.opacity))
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
				<label class="layer-switch" :aria-label="`${layer.name}显示状态`">
					<input type="checkbox" :checked="layer.visible" @change="handleLayerToggleEvent(layer, $event)">
					<span></span>
				</label>
			</div>
			<div class="layer-row__tools">
				<small>{{ layer.count }} 项</small>
				<button type="button" @click="handleLocateLayer(layer)">定位</button>
			</div>
			<input v-if="layer.key === 'raster' || layer.key.includes('Boundary')" class="layer-opacity" type="range"
				min="0.1" max="1" step="0.02" :value="layer.opacity" @input="handleOpacityInput(layer, $event)">
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

.layer-switch {
	position: relative;
	width: 40px;
	height: 22px;
	display: inline-flex;
	align-items: center;
}

.layer-switch input {
	position: absolute;
	inset: 0;
	opacity: 0;
	margin: 0;
	cursor: pointer;
}

.layer-switch span {
	position: absolute;
	inset: 0;
	border-radius: 999px;
	background: rgba(59, 69, 67, 0.82);
	border: 1px solid rgba(125, 211, 252, 0.34);
	transition: background 0.2s ease;
}

.layer-switch span::after {
	content: '';
	position: absolute;
	top: 2px;
	left: 2px;
	width: 16px;
	height: 16px;
	border-radius: 50%;
	background: #f5fbff;
	transition: transform 0.2s ease;
}

.layer-switch input:checked + span {
	background: rgba(35, 209, 139, 0.82);
}

.layer-switch input:checked + span::after {
	transform: translateX(18px);
}

.layer-opacity {
	width: 100%;
	margin-top: 8px;
	accent-color: #23d18b;
}
</style>
