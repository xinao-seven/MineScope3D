<script setup lang="ts">
import {
    Cartesian2,
    Color,
    Entity,
    ImageryLayer,
    JulianDate,
    PropertyBag,
    Rectangle,
    Viewer,
    defined,
} from 'cesium'
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { CameraManager } from '../../cesium/core/CameraManager'
import { degreesArrayToCartesianArray } from '../../cesium/core/coordinateTransform'
import { ViewerManager } from '../../cesium/core/ViewerManager'
import type { BasemapKey } from '../../cesium/constants'
import { EntityManager } from '../../cesium/managers/EntityManager'
import { InteractionManager } from '../../cesium/managers/InteractionManager'
import { LayerManager } from '../../cesium/managers/LayerManager'
import { ImageryLayerLoader } from '../../cesium/loaders/ImageryLayerLoader'
import { MeasureTool } from '../../cesium/tools/MeasureTool'
import { useDashboardStore } from '../../store/dashboard'
import type { Borehole, BoundaryRegion, LayerKey, RasterLayer } from '../../types/dashboard'

const store = useDashboardStore()
const mapContainer = ref<HTMLDivElement | null>(null)
const tooltip = reactive({ visible: false, x: 0, y: 0, text: '' })
const activeBasemapKey = ref<BasemapKey>('geo')
const mapToolState = reactive({
    measuring: false,
    measureResult: '',
    showLayerModel: true,
})

const basemapOptions = [
    { key: 'geo' as BasemapKey, name: '地理' },
    { key: 'image' as BasemapKey, name: '影像' },
    { key: 'osm' as BasemapKey, name: '街图' },
]

let viewer: Viewer | null = null
let viewerManager: ViewerManager | null = null
let cameraManager: CameraManager | null = null
let entityManager: EntityManager | null = null
let interactionManager: InteractionManager | null = null
let layerManager: LayerManager | null = null
let imageryLayerLoader: ImageryLayerLoader | null = null
let measureTool: MeasureTool | null = null
let rasterLayer: ImageryLayer | null = null
let hasAutoFlownToMine = false
const boreholeEntities = new Map<string, Entity>()
const boreholeLayerEntities = new Map<string, Entity[]>()
const boundaryEntities = new Map<string, Entity[]>()

/** 挂载 Cesium 场景并加载首屏数据。 */
function mountScene() {
    if (!mapContainer.value || viewer) {
        return
    }

    viewerManager = new ViewerManager(mapContainer.value)
    viewer = viewerManager.viewer
    cameraManager = new CameraManager(viewer)
    entityManager = new EntityManager(viewer)
    interactionManager = new InteractionManager(viewer)
    layerManager = new LayerManager(viewer)
    imageryLayerLoader = new ImageryLayerLoader(viewer)
    measureTool = new MeasureTool(viewer)

    switchBasemap('geo')
    bindMapInteractions()
    reloadSceneData()
}

/** 绑定地图点击和 hover 交互。 */
function bindMapInteractions() {
    if (!interactionManager) {
        return
    }
    interactionManager.onLeftClick(handleMapClick)
    interactionManager.onMouseMove(handleMouseMove)
}

/** 读取图层监听签名。 */
function readLayerSignature() {
    return store.layerSignature
}

/** 读取业务数据监听签名。 */
function readDataSignature() {
    return `${store.boreholes.length}:${store.boundaries.length}:${store.rasters.length}`
}

/** 重新绘制全部业务图层。 */
function reloadSceneData() {
    if (!viewer || !viewerManager) {
        return
    }

    viewerManager.clearData()
    boreholeEntities.clear()
    boreholeLayerEntities.clear()
    boundaryEntities.clear()
    removeRasterLayer()
    addBoreholes(store.boreholes)
    addBoreholeLayerModels(store.boreholes)
    addBoundaries(store.boundaries)
    addRasterLayer(store.activeRaster)
    syncLayerVisibility()
    flyToMineOnce()
}

/** 添加基于分层信息的钻孔三维实体。 */
function addBoreholeLayerModels(boreholes: Borehole[]) {
    if (!entityManager) {
        return
    }

    const verticalExaggeration = 4.5
    const minimumVisualLength = 10
    const visualRadius = 5.2

    for (const borehole of boreholes) {
        if (borehole.longitude === 0 && borehole.latitude === 0 || borehole.layers.length === 0) {
            continue
        }

        const layerEntities: Entity[] = []
        const layers = [...borehole.layers].sort((left, right) => left.sort_order - right.sort_order)
        for (const layer of layers) {
            const thickness = Math.max(layer.thickness, 0)
            if (thickness <= 0) {
                continue
            }

            const centerHeight = borehole.elevation - (layer.top_depth + thickness / 2) * verticalExaggeration
            const layerColor = Color.fromCssColorString(layer.color || '#23d18b')
            const entity = entityManager.addCylinder({
                id: `borehole-layer-${borehole.id}-${layer.sort_order}`,
                name: `${borehole.name}-${layer.layer_name}`,
                position: { lon: borehole.longitude, lat: borehole.latitude, height: centerHeight },
                length: Math.max(thickness * verticalExaggeration, minimumVisualLength),
                topRadius: visualRadius,
                bottomRadius: visualRadius,
                color: layerColor.withAlpha(0.8),
                outlineColor: layerColor.withAlpha(0.95),
                tag: 'borehole-layer-model',
            })
            entity.properties = new PropertyBag({
                domainType: 'borehole-layer-model',
                targetId: borehole.id,
                layerName: layer.layer_name,
                tag: 'borehole-layer-model',
            })
            layerEntities.push(entity)
        }

        if (layerEntities.length > 0) {
            boreholeLayerEntities.set(borehole.id, layerEntities)
        }
    }
}

/** 只在数据首次加载完成后自动飞向矿区。 */
function flyToMineOnce() {
    if (hasAutoFlownToMine || store.boundaries.length === 0) {
        return
    }
    hasAutoFlownToMine = true
    window.setTimeout(() => flyToLayer('mineBoundary'), 240)
}

/** 添加钻孔点实体。 */
function addBoreholes(boreholes: Borehole[]) {
    if (!entityManager) {
        return
    }

    for (const borehole of boreholes) {
        if (borehole.longitude === 0 && borehole.latitude === 0) {
            continue
        }
        const entity = entityManager.addPoint({
            id: `borehole-${borehole.id}`,
            name: borehole.name,
            position: { lon: borehole.longitude, lat: borehole.latitude, height: borehole.elevation },
            pixelSize: 13,
            color: Color.fromCssColorString('#f2c94c'),
            outlineColor: Color.fromCssColorString('#04110e'),
            outlineWidth: 3,
            labelText: borehole.borehole_code,
            tag: 'borehole',
        })
        entity.properties = new PropertyBag({
            domainType: 'borehole',
            targetId: borehole.id,
            tag: 'borehole',
        })

        boreholeEntities.set(borehole.id, entity)
    }
}

/** 切换快捷底图，同时保留 Cesium 原生底图选择器。 */
function switchBasemap(key: BasemapKey) {
    if (!viewerManager) {
        return
    }
    viewerManager.switchBasemap(key)
    activeBasemapKey.value = key
}

/** 添加矿区与工作面边界实体。 */
function addBoundaries(boundaries: BoundaryRegion[]) {
    if (!entityManager) {
        return
    }

    for (const boundary of boundaries) {
        const positions = degreesArrayToCartesianArray(
            boundary.coordinates.map((item) => ({ lon: item[0], lat: item[1], height: 0 })),
        )
        const color = boundary.type === 'mine' ? Color.fromCssColorString('#23d18b') : Color.fromCssColorString('#56ccf2')
        const polygon = entityManager.addPolygon({
            id: `boundary-${boundary.id}`,
            name: boundary.name,
            positions,
            color: color.withAlpha(boundary.type === 'mine' ? 0.12 : 0.18),
            outlineColor: color.withAlpha(0.95),
            outlineWidth: boundary.type === 'mine' ? 2 : 1,
            tag: 'boundary',
        })
        const polyline = entityManager.addPolyline({
            id: `boundary-outline-${boundary.id}`,
            name: `${boundary.name}-outline`,
            positions,
            width: boundary.type === 'mine' ? 4 : 3,
            color: color.withAlpha(0.95),
            clampToGround: true,
            tag: 'boundary',
        })

        const boundaryProperties = new PropertyBag({
            domainType: 'boundary',
            targetId: boundary.id,
            boundaryType: boundary.type,
            tag: 'boundary',
        })
        polygon.properties = boundaryProperties
        polyline.properties = boundaryProperties

        boundaryEntities.set(boundary.id, [polygon, polyline])
    }
}

/** 添加 TIFF 元信息对应的影像叠加层。 */
async function addRasterLayer(raster: RasterLayer | null) {
    if (!imageryLayerLoader || !raster) {
        return
    }

    const bounds = {
        west: raster.bounds.west,
        south: raster.bounds.south,
        east: raster.bounds.east,
        north: raster.bounds.north,
    }

    try {
        rasterLayer = await imageryLayerLoader.addGeoTiffSingleTile(raster.url, bounds)
        rasterLayer.alpha = store.getLayerState('raster')?.opacity ?? raster.opacity
        rasterLayer.show = store.getLayerState('raster')?.visible ?? true
    } catch (error) {
        console.error('[MineScope3D] TIFF 栅格加载失败', { rasterId: raster.id, url: raster.url, error })
    }
}

/** 移除当前专题影像图层。 */
function removeRasterLayer() {
    if (imageryLayerLoader && rasterLayer) {
        imageryLayerLoader.remove(rasterLayer, true)
        rasterLayer = null
    }
}

/** 同步图层显隐与透明度。 */
function syncLayerVisibility() {
    syncBoreholeVisibility()
    syncBoundaryVisibility()
    syncRasterVisibility()
}

/** 同步钻孔点图层可见性。 */
function syncBoreholeVisibility() {
    const layer = store.getLayerState('boreholes')
    const modelVisible = (layer?.visible ?? true) && mapToolState.showLayerModel
    if (layerManager) {
        layerManager.setEntityVisible((entity) => readEntityProperty(entity, 'domainType') === 'borehole', layer?.visible ?? true)
        layerManager.setEntityVisible((entity) => readEntityProperty(entity, 'domainType') === 'borehole-layer-model', modelVisible)
        return
    }
    for (const entity of boreholeEntities.values()) {
        entity.show = layer?.visible ?? true
    }
    for (const entities of boreholeLayerEntities.values()) {
        for (const entity of entities) {
            entity.show = modelVisible
        }
    }
}

/** 同步边界图层可见性与透明度。 */
function syncBoundaryVisibility() {
    for (const boundary of store.boundaries) {
        const layerKey = boundary.type === 'mine' ? 'mineBoundary' : 'workfaceBoundary'
        const layer = store.getLayerState(layerKey)
        const color = boundary.type === 'mine' ? Color.fromCssColorString('#23d18b') : Color.fromCssColorString('#56ccf2')
        const entities = boundaryEntities.get(boundary.id) ?? []
        for (const entity of entities) {
            if (layerManager) {
                layerManager.setEntityVisible((target) => target.id === entity.id, layer?.visible ?? true)
            } else {
                entity.show = layer?.visible ?? true
            }
            if (entity.polygon && entity.id === `boundary-${boundary.id}`) {
                ;(entity.polygon as any).material = color.withAlpha((layer?.opacity ?? 0.72) * 0.24)
                ;(entity.polygon as any).outlineColor = color.withAlpha(layer?.opacity ?? 0.72)
            }
            if (entity.polyline && entity.id === `boundary-outline-${boundary.id}`) {
                ;(entity.polyline as any).material = color.withAlpha(layer?.opacity ?? 0.72)
            }
        }
    }
}

/** 同步专题图图层可见性与透明度。 */
function syncRasterVisibility() {
    const layer = store.getLayerState('raster')
    if (rasterLayer) {
        if (layerManager) {
            layerManager.setImageryLayerVisible(rasterLayer, layer?.visible ?? true)
            layerManager.setImageryLayerOpacity(rasterLayer, layer?.opacity ?? 0.62)
        } else {
            rasterLayer.show = layer?.visible ?? true
            rasterLayer.alpha = layer?.opacity ?? 0.62
        }
    }
}

/** 处理地图点击选中对象。 */
function handleMapClick(event: { position: Cartesian2 }) {
    if (mapToolState.measuring) {
        return
    }

    const entity = pickEntity(event.position)
    if (!entity) {
        return
    }
    const domainType = readEntityProperty(entity, 'domainType')
    const targetId = readEntityProperty(entity, 'targetId')
    if (domainType === 'borehole') {
        store.selectBorehole(targetId)
    }
    if (domainType === 'boundary') {
        store.selectBoundary(targetId)
    }
    if (domainType === 'borehole-layer-model') {
        store.selectBorehole(targetId)
    }
}

/** 处理鼠标移动提示。 */
function handleMouseMove(event: { endPosition: Cartesian2 }) {
    const entity = pickEntity(event.endPosition)
    if (!entity) {
        tooltip.visible = false
        return
    }

    tooltip.visible = true
    tooltip.x = event.endPosition.x + 14
    tooltip.y = event.endPosition.y + 14
    tooltip.text = entity.name || '空间对象'
}

/** 从屏幕坐标拾取业务实体。 */
function pickEntity(position: Cartesian2): Entity | null {
    const picked = interactionManager?.pickObject(position) ?? viewer?.scene.pick(position)
    if (defined(picked) && picked.id instanceof Entity) {
        return picked.id
    }
    return null
}

/** 读取实体上的业务属性。 */
function readEntityProperty(entity: Entity, key: string): string {
    const values = entity.properties?.getValue(JulianDate.now()) as Record<string, unknown> | undefined
    return String(values?.[key] ?? '')
}

/** 飞行定位到钻孔点。 */
function flyToBorehole(id: string) {
    const borehole = store.boreholes.find((item) => item.id === id)
    const entity = boreholeEntities.get(id)
    store.selectBorehole(id)
    if (cameraManager && borehole && entity) {
        cameraManager.flyTo(entity, {
            duration: 1.1,
            offset: {
                heading: 0,
                pitch: -0.85,
                range: 4200,
            },
        })
    }
}

/** 飞行定位到指定边界对象。 */
function flyToBoundary(id: string) {
    const boundary = store.boundaries.find((item) => item.id === id)
    if (cameraManager && boundary) {
        store.selectBoundary(id)
        cameraManager.flyToRectangle(buildBoundaryRectangle(boundary), 1.1)
    }
}

/** 飞行定位到指定图层范围。 */
function flyToLayer(key: LayerKey) {
    if (!cameraManager) {
        return
    }

    if (key === 'boreholes') {
        const destination = buildBoreholeRectangle()
        if (destination) {
            cameraManager.flyToRectangle(destination, 1.1)
        }
        return
    }
    if (key === 'raster' && store.activeRaster) {
        store.selectRaster(store.activeRaster.id)
        cameraManager.flyToRectangle(buildRasterRectangle(store.activeRaster), 1.1)
        return
    }

    const targetBoundary = store.boundaries.find((boundary) => {
        return key === 'mineBoundary' ? boundary.type === 'mine' : boundary.type === 'workface'
    })
    if (targetBoundary) {
        store.selectBoundary(targetBoundary.id)
        cameraManager.flyToRectangle(buildBoundaryRectangle(targetBoundary), 1.1)
    }
}

/** 计算钻孔点整体矩形范围。 */
function buildBoreholeRectangle(): Rectangle | null {
    const spatialBoreholes = store.boreholes.filter((item) => item.longitude !== 0 || item.latitude !== 0)
    if (spatialBoreholes.length === 0) {
        return null
    }
    const longitudes = spatialBoreholes.map((item) => item.longitude)
    const latitudes = spatialBoreholes.map((item) => item.latitude)
    return Rectangle.fromDegrees(Math.min(...longitudes) - 0.02, Math.min(...latitudes) - 0.02, Math.max(...longitudes) + 0.02, Math.max(...latitudes) + 0.02)
}

/** 计算边界对象矩形范围。 */
function buildBoundaryRectangle(boundary: BoundaryRegion): Rectangle {
    const longitudes = boundary.coordinates.map((item) => item[0])
    const latitudes = boundary.coordinates.map((item) => item[1])
    return Rectangle.fromDegrees(Math.min(...longitudes) - 0.01, Math.min(...latitudes) - 0.01, Math.max(...longitudes) + 0.01, Math.max(...latitudes) + 0.01)
}

/** 计算专题图图层矩形范围。 */
function buildRasterRectangle(raster: RasterLayer): Rectangle {
    return Rectangle.fromDegrees(raster.bounds.west, raster.bounds.south, raster.bounds.east, raster.bounds.north)
}

/** 切换测距模式。 */
function toggleDistanceMeasure() {
    if (!measureTool) {
        return
    }

    if (mapToolState.measuring) {
        stopDistanceMeasure()
        return
    }

    mapToolState.measuring = true
    mapToolState.measureResult = '测距中：左键选两点，右键取消'
    measureTool.startDistance((result) => {
        mapToolState.measuring = false
        mapToolState.measureResult = `测距结果：${(result.distanceMeters ?? 0).toFixed(2)} m`
    })
}

/** 停止测距模式。 */
function stopDistanceMeasure() {
    measureTool?.stop()
    mapToolState.measuring = false
    if (!mapToolState.measureResult) {
        mapToolState.measureResult = '测距已停止'
    }
}

/** 清理测距结果。 */
function clearMeasureResult() {
    measureTool?.stop()
    measureTool?.clear()
    mapToolState.measuring = false
    mapToolState.measureResult = ''
}

/** 销毁 Cesium 场景和事件处理器。 */
function destroyScene() {
    measureTool?.destroy()
    interactionManager?.destroy()
    viewerManager?.destroy()
    viewer = null
    viewerManager = null
    cameraManager = null
    entityManager = null
    interactionManager = null
    layerManager = null
    imageryLayerLoader = null
    measureTool = null
}

watch(readLayerSignature, syncLayerVisibility)
watch(readDataSignature, reloadSceneData)
watch(() => mapToolState.showLayerModel, syncBoreholeVisibility)
onMounted(mountScene)
onBeforeUnmount(destroyScene)

defineExpose({ flyToBorehole, flyToBoundary, flyToLayer })
</script>

<template>
    <div class="cesium-shell">
        <div ref="mapContainer" class="cesium-map"></div>
        <div class="basemap-switcher" aria-label="快捷底图切换">
            <span>快捷底图</span>
            <button v-for="option in basemapOptions" :key="option.key" type="button"
                :class="{ 'is-active': activeBasemapKey === option.key }" @click="switchBasemap(option.key)">
                {{ option.name }}
            </button>
        </div>
        <div class="map-tools" aria-label="空间分析工具">
            <button type="button" :class="{ 'is-active': mapToolState.measuring }" @click="toggleDistanceMeasure">
                {{ mapToolState.measuring ? '结束测距' : '测距' }}
            </button>
            <button type="button" @click="clearMeasureResult">清除测量</button>
            <label>
                <input v-model="mapToolState.showLayerModel" type="checkbox">
                分层模型
            </label>
            <span v-if="mapToolState.measureResult">{{ mapToolState.measureResult }}</span>
        </div>
        <div class="map-reticle"></div>
        <div class="map-status">
            <span>WGS84</span>
            <strong>锦界矿区三维场景</strong>
            <span>钻孔 / SHP / TIFF</span>
        </div>
        <div v-show="tooltip.visible" class="map-tooltip" :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }">
            {{ tooltip.text }}
        </div>
    </div>
</template>

<style scoped>
.cesium-shell,
.cesium-map {
    position: absolute;
    inset: 0;
}

.cesium-map canvas {
    filter: none;
}

.basemap-switcher {
    position: absolute;
    z-index: 6;
    top: 16px;
    left: 50%;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px;
    border: 1px solid rgba(125, 211, 252, 0.36);
    border-radius: 8px;
    background: rgba(5, 19, 48, 0.58);
    color: var(--muted);
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
    transform: translateX(-50%);
}

.basemap-switcher span {
    padding: 0 4px;
    color: rgba(226, 239, 255, 0.82);
    font-size: 12px;
    white-space: nowrap;
}

.basemap-switcher button {
    min-width: 42px;
    height: 28px;
    border: 1px solid rgba(125, 211, 252, 0.28);
    border-radius: 6px;
    background: rgba(8, 31, 72, 0.62);
    color: rgba(226, 239, 255, 0.82);
    font-size: 12px;
    cursor: pointer;
    transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.basemap-switcher button:hover,
.basemap-switcher button.is-active {
    border-color: rgba(35, 209, 139, 0.78);
    background: rgba(35, 209, 139, 0.18);
    color: #ffffff;
}

.map-tools {
    position: absolute;
    z-index: 6;
    top: 64px;
    left: 50%;
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: min(80%, 980px);
    padding: 6px 10px;
    border: 1px solid rgba(125, 211, 252, 0.34);
    border-radius: 8px;
    background: rgba(5, 19, 48, 0.6);
    color: rgba(226, 239, 255, 0.86);
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
    transform: translateX(-50%);
}

.map-tools button {
    height: 28px;
    padding: 0 10px;
    border: 1px solid rgba(125, 211, 252, 0.28);
    border-radius: 6px;
    background: rgba(8, 31, 72, 0.62);
    color: rgba(226, 239, 255, 0.82);
    font-size: 12px;
    cursor: pointer;
    transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.map-tools button:hover,
.map-tools button.is-active {
    border-color: rgba(35, 209, 139, 0.78);
    background: rgba(35, 209, 139, 0.18);
    color: #ffffff;
}

.map-tools label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--muted);
    font-size: 12px;
    white-space: nowrap;
}

.map-tools input[type="checkbox"] {
    accent-color: #23d18b;
}

.map-tools span {
    color: #fff9da;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.map-reticle {
    position: absolute;
    inset: 18px;
    pointer-events: none;
    border: 1px solid rgba(125, 211, 252, 0.24);
    border-radius: 8px;
}

.map-reticle::before,
.map-reticle::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    background: rgba(125, 211, 252, 0.54);
    transform: translate(-50%, -50%);
}

.map-reticle::before {
    width: 92px;
    height: 1px;
}

.map-reticle::after {
    width: 1px;
    height: 92px;
}

.map-status {
    position: absolute;
    left: 342px;
    right: 372px;
    bottom: 170px;
    display: flex;
    justify-content: space-between;
    padding: 7px 12px;
    border: 1px solid rgba(96, 165, 250, 0.34);
    border-radius: 8px;
    background: rgba(5, 19, 48, 0.54);
    color: var(--muted);
    backdrop-filter: blur(12px);
}

.map-status strong {
    color: var(--green);
}

.map-tooltip {
    position: absolute;
    z-index: 5;
    pointer-events: none;
    padding: 8px 10px;
    border: 1px solid rgba(125, 211, 252, 0.54);
    border-radius: 6px;
    color: #fff9da;
    background: rgba(5, 19, 48, 0.9);
    box-shadow: var(--shadow);
}

:deep(.cesium-viewer-toolbar) {
    top: 16px;
    right: 16px;
}

:deep(.cesium-baseLayerPicker-dropDown) {
    background: rgba(5, 19, 48, 0.92);
    border: 1px solid rgba(125, 211, 252, 0.34);
}

@media (max-width: 1500px) {
    .map-status {
        left: 324px;
        right: 354px;
    }
}
</style>
