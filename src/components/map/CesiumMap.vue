<script setup lang="ts">
import 'cesium/Build/Cesium/Widgets/widgets.css'
import {
    Cartesian2,
    Color,
    Cesium3DTileset,
    Entity,
    ImageryLayer,
    PropertyBag,
    Viewer,
    defined,
} from 'cesium'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { CameraManager } from '../../cesium/core/CameraManager'
import {
    addBoreholeLayerEntities,
    addBoreholePointEntities,
    addBoundaryPolygonFallbackEntities,
    buildBoundaryLookup,
    buildBoreholeRectangle,
    buildBoundaryRectangle,
    buildRasterRectangle,
} from '../../cesium/core/dashboardScene'
import { readEntityProperty } from '../../cesium/core/entityProperty'
import { ViewerManager } from '../../cesium/core/ViewerManager'
import type { BasemapKey } from '../../cesium/constants'
import { GeoJsonLayerLoader, TilesetLoader } from '../../cesium/loaders'
import { EntityManager } from '../../cesium/managers/EntityManager'
import { AnnotationManager } from '../../cesium/managers/AnnotationManager'
import { InteractionManager } from '../../cesium/managers/InteractionManager'
import { LayerManager } from '../../cesium/managers/LayerManager'
import { ImageryLayerLoader } from '../../cesium/loaders/ImageryLayerLoader'
import { MeasureTool } from '../../cesium/tools/MeasureTool'
import { fetchBoundaryGeoJson } from '../../api/dashboard'
import { fetchTilesets, type TilesetEntry } from '../../api/tilesets'
import { useDashboardStore } from '../../store/dashboard'
import type { LayerKey, RasterLayer } from '../../types/dashboard'

const store = useDashboardStore()
const mapContainer = ref<HTMLDivElement | null>(null)
const tooltip = reactive({ visible: false, x: 0, y: 0, text: '' })
const activeBasemapKey = ref<BasemapKey>('geo')
const mapToolState = reactive({
    measuring: false,
    measureResult: '',
    showLayerModel: true,
    tilesetLoading: false,
    tilesetLoaded: false,
    tilesetResult: '',
    annotating: false,
    annotationResult: '',
})
const mapToolResult = computed(() => mapToolState.measureResult || mapToolState.tilesetResult || mapToolState.annotationResult)

const basemapOptions = [
    { key: 'geo' as BasemapKey, name: '地理' },
    { key: 'image' as BasemapKey, name: '影像' },
    { key: 'osm' as BasemapKey, name: '街图' },
]

let viewer: Viewer | null = null
let viewerManager: ViewerManager | null = null
let cameraManager: CameraManager | null = null
let entityManager: EntityManager | null = null
let annotationManager: AnnotationManager | null = null
let interactionManager: InteractionManager | null = null
let layerManager: LayerManager | null = null
let imageryLayerLoader: ImageryLayerLoader | null = null
let geoJsonLayerLoader: GeoJsonLayerLoader | null = null
let tilesetLoader: TilesetLoader | null = null
let measureTool: MeasureTool | null = null
let rasterLayer: ImageryLayer | null = null
const mineTilesetMap = new Map<string, Cesium3DTileset>()
let mineTilesetEntries: TilesetEntry[] = []
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
    annotationManager = new AnnotationManager(viewer, entityManager)
    interactionManager = new InteractionManager(viewer)
    layerManager = new LayerManager(viewer)
    imageryLayerLoader = new ImageryLayerLoader(viewer)
    geoJsonLayerLoader = new GeoJsonLayerLoader(viewer)
    tilesetLoader = new TilesetLoader(viewer)
    measureTool = new MeasureTool(viewer)

    switchBasemap('image')
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

/** 重新绘制全部业务图层。 */
function reloadSceneData() {
    if (!viewer || !viewerManager || !entityManager) {
        return
    }

    viewerManager.clearData()
    boreholeEntities.clear()
    boreholeLayerEntities.clear()
    boundaryEntities.clear()
    removeRasterLayer()

    addBoreholePointEntities(entityManager, store.boreholes, boreholeEntities)
    addBoreholeLayerEntities(entityManager, store.boreholes, boreholeLayerEntities)
    void loadBoundaryGeoJsonLayer()
    addRasterLayer(store.activeRaster)
    syncLayerVisibility()
    annotationManager?.restoreEntities()
    flyToMineOnce()
}

/** 通过 GeoJSON 数据源直接叠加边界并写入选中映射。 */
async function loadBoundaryGeoJsonLayer() {
    if (!geoJsonLayerLoader || !entityManager) {
        return
    }

    try {
        const geojson = await fetchBoundaryGeoJson()
        const dataSource = await geoJsonLayerLoader.load(geojson, 'boundaries-geojson')
        boundaryEntities.clear()
        const boundaryLookup = buildBoundaryLookup(store.boundaries)
        const polygonBoundaryIds = new Set<string>()

        for (const entity of dataSource.entities.values) {
            const boundaryId = readEntityProperty(entity, 'id')
            const boundaryType = readEntityProperty(entity, 'type')
            if (!boundaryId) {
                continue
            }

            const boundary = boundaryLookup.get(boundaryId)
            const resolvedType = boundaryType || boundary?.type || 'workface'
            const resolvedName = boundary?.name || readEntityProperty(entity, 'name') || entity.name || `边界-${boundaryId}`

            const color = resolvedType === 'mine'
                ? Color.fromCssColorString('#23d18b')
                : Color.fromCssColorString('#56ccf2')

            if (entity.polygon) {
                polygonBoundaryIds.add(boundaryId)
                const polygon = entity.polygon as any
                polygon.material = color.withAlpha(resolvedType === 'mine' ? 0.12 : 0.18)
                polygon.outline = true
                polygon.outlineColor = color.withAlpha(0.95)
            }
            if (entity.polyline) {
                const polyline = entity.polyline as any
                polyline.material = color.withAlpha(0.95)
                polyline.width = resolvedType === 'mine' ? 4 : 3
                polyline.clampToGround = true
            }

            entity.name = String(resolvedName)

            entity.properties = new PropertyBag({
                id: boundaryId,
                type: resolvedType,
                domainType: 'boundary',
                targetId: boundaryId,
                boundaryType: resolvedType,
                tag: 'boundary',
            })

            const targetList = boundaryEntities.get(boundaryId)
            if (targetList) {
                targetList.push(entity)
            } else {
                boundaryEntities.set(boundaryId, [entity])
            }
        }

        // GeoJSON 只含线时，按元数据坐标补面，保证“面+线”同时可交互。
        addBoundaryPolygonFallbackEntities(entityManager, store.boundaries, boundaryEntities, polygonBoundaryIds)

        syncBoundaryVisibility()
    } catch (error) {
        console.error('[MineScope3D] 边界 GeoJSON 加载失败', { error })
    }
}

/** 切换点击标注模式。 */
function toggleAnnotationMode() {
    mapToolState.annotating = !mapToolState.annotating
    if (mapToolState.annotating) {
        stopDistanceMeasure()
        mapToolState.annotationResult = '标注中：左键点击地图添加标注，名称由弹窗输入'
        return
    }
    if (!mapToolState.annotationResult) {
        mapToolState.annotationResult = '标注已停止'
    }
}

/** 清空全部点击标注。 */
function clearAnnotations() {
    annotationManager?.clearAll()
    mapToolState.annotationResult = '已清空标注'
}

/** 删除选中的标注。 */
function deleteSelectedAnnotation() {
    const selected = annotationManager?.getSelected() ?? null
    if (!selected) {
        mapToolState.annotationResult = '请先点击一个标注后再删除'
        return
    }

    const confirmed = window.confirm(`确认删除标注“${selected.name}”吗？`)
    if (!confirmed) {
        return
    }

    const deleted = annotationManager?.deleteSelected() ?? null
    if (!deleted) {
        mapToolState.annotationResult = '删除失败：未找到选中标注'
        return
    }
    mapToolState.annotationResult = `已删除 ${deleted.name}`
}

/** 重命名选中的标注。 */
function renameSelectedAnnotation() {
    const selected = annotationManager?.getSelected() ?? null
    if (!selected) {
        mapToolState.annotationResult = '请先点击一个标注后再重命名'
        return
    }

    const input = window.prompt('请输入新的标注名称', selected.name)
    if (input === null) {
        return
    }
    const name = input.trim()
    if (!name) {
        mapToolState.annotationResult = '标注名称不能为空'
        return
    }

    const renamed = annotationManager?.renameSelected(name) ?? null
    if (!renamed) {
        mapToolState.annotationResult = '重命名失败：未找到选中标注'
        return
    }
    mapToolState.annotationResult = `已重命名为 ${renamed.name}`
}

/** 只在数据首次加载完成后自动飞向矿区。 */
function flyToMineOnce() {
    if (hasAutoFlownToMine || store.boundaries.length === 0) {
        return
    }
    hasAutoFlownToMine = true
    window.setTimeout(() => flyToLayer('mineBoundary'), 240)
}

/** 切换快捷底图，同时保留 Cesium 原生底图选择器。 */
function switchBasemap(key: BasemapKey) {
    if (!viewerManager) {
        return
    }
    viewerManager.switchBasemap(key)
    activeBasemapKey.value = key
}

function applyRasterLayerState(targetLayer: ImageryLayer, fallbackOpacity: number) {
    targetLayer.alpha = store.getLayerState('raster')?.opacity ?? fallbackOpacity
    targetLayer.show = store.getLayerState('raster')?.visible ?? true
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

    const previewUrl = raster.preview_url?.trim()

    try {
        rasterLayer = previewUrl
            ? await imageryLayerLoader.addSingleTile(previewUrl, bounds)
            : await imageryLayerLoader.addGeoTiffSingleTile(raster.url, bounds)
        applyRasterLayerState(rasterLayer, raster.opacity)
    } catch (error) {
        if (previewUrl) {
            try {
                rasterLayer = await imageryLayerLoader.addGeoTiffSingleTile(raster.url, bounds)
                applyRasterLayerState(rasterLayer, raster.opacity)
                return
            } catch (fallbackError) {
                console.error('[MineScope3D] 栅格预览与 TIFF 回退加载均失败', {
                    rasterId: raster.id,
                    previewUrl,
                    rasterUrl: raster.url,
                    fallbackError,
                })
                return
            }
        }
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
            if (entity.polygon) {
                ;(entity.polygon as any).material = color.withAlpha((layer?.opacity ?? 0.72) * 0.24)
                ;(entity.polygon as any).outlineColor = color.withAlpha(layer?.opacity ?? 0.72)
            }
            if (entity.polyline) {
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

    if (mapToolState.annotating) {
        const cartesian = interactionManager?.pickCartesian(event.position) ?? null
        if (!cartesian) {
            mapToolState.annotationResult = '当前视角下无法拾取地表位置'
            return
        }

        const defaultName = annotationManager?.createDefaultName() ?? '标注'
        const input = window.prompt('请输入标注名称', defaultName)
        if (input === null) {
            mapToolState.annotationResult = '已取消添加标注'
            return
        }
        const name = input.trim() || defaultName
        const result = annotationManager?.addAt(cartesian, name)
        if (!result) {
            mapToolState.annotationResult = '添加标注失败'
            return
        }
        mapToolState.annotationResult = `已添加 ${result.annotation.name} (${result.longitude.toFixed(6)}, ${result.latitude.toFixed(6)})`
        return
    }

    if (!entity) {
        annotationManager?.clearSelection()
        return
    }
    const domainType = readEntityProperty(entity, 'domainType')
    const targetId = readEntityProperty(entity, 'targetId')
    if (domainType === 'annotation') {
        const selected = annotationManager?.selectByEntity(entity) ?? null
        mapToolState.annotationResult = selected
            ? `已选中 ${selected.name}，可使用“重命名标注/删除标注”`
            : '标注选择失败'
        return
    }

    annotationManager?.clearSelection()
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
        const destination = buildBoreholeRectangle(store.boreholes)
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
    mapToolState.annotating = false
    annotationManager?.clearSelection()
    if (mapToolState.annotationResult.startsWith('已选中')) {
        mapToolState.annotationResult = ''
    }
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

/** 加载矿区 3D Tiles 模型，并自动飞行定位。 */
async function loadMineTilesetAndLocate() {
    if (!tilesetLoader || mapToolState.tilesetLoading) {
        return
    }

    mapToolState.tilesetLoading = true
    mapToolState.tilesetResult = '3D 模型加载中...'
    try {
        if (mineTilesetEntries.length === 0) {
            mineTilesetEntries = await fetchTilesets()
            if (mineTilesetEntries.length === 0) {
                mapToolState.tilesetResult = '未找到可用 3D 模型'
                return
            }
        }

        let failedCount = 0
        let newlyLoadedCount = 0

        for (const entry of mineTilesetEntries) {
            const tilesetKey = entry.id || entry.url
            const currentTileset = mineTilesetMap.get(tilesetKey)
            if (currentTileset && !currentTileset.isDestroyed()) {
                continue
            }

            try {
                const tileset = await tilesetLoader.loadFromUrl(entry.url)
                mineTilesetMap.set(tilesetKey, tileset)
                newlyLoadedCount += 1
            } catch (error) {
                failedCount += 1
                console.error('[MineScope3D] 3D Tiles 模型加载失败', { id: entry.id, url: entry.url, error })
            }
        }

        const activeTilesets = Array.from(mineTilesetMap.values()).filter((item) => !item.isDestroyed())
        if (activeTilesets.length === 0) {
            mapToolState.tilesetLoaded = false
            mapToolState.tilesetResult = '3D 模型加载失败，请检查 tileset 路径'
            return
        }

        mapToolState.tilesetLoaded = true
        await tilesetLoader.flyTo(activeTilesets[0], 1.2)

        if (failedCount > 0) {
            mapToolState.tilesetResult = `已加载 ${activeTilesets.length} 个模型，${failedCount} 个失败`
            return
        }
        if (newlyLoadedCount > 0) {
            mapToolState.tilesetResult = `已加载 ${activeTilesets.length} 个 3D 模型并定位`
            return
        }
        mapToolState.tilesetResult = `已定位 ${activeTilesets.length} 个 3D 模型`
    } catch (error) {
        console.error('[MineScope3D] 3D Tiles 模型加载失败', { error })
        mapToolState.tilesetResult = '3D 模型加载失败，请检查 tileset 路径'
    } finally {
        mapToolState.tilesetLoading = false
    }
}

/** 销毁 Cesium 场景和事件处理器。 */
function destroyScene() {
    if (tilesetLoader) {
        for (const tileset of mineTilesetMap.values()) {
            if (!tileset.isDestroyed()) {
                tilesetLoader.remove(tileset)
            }
        }
    }
    mineTilesetMap.clear()
    mineTilesetEntries = []
    annotationManager?.clearAll()
    measureTool?.destroy()
    interactionManager?.destroy()
    viewerManager?.destroy()
    viewer = null
    viewerManager = null
    cameraManager = null
    entityManager = null
    annotationManager = null
    interactionManager = null
    layerManager = null
    imageryLayerLoader = null
    geoJsonLayerLoader = null
    tilesetLoader = null
    measureTool = null
}

watch(() => store.layerSignature, syncLayerVisibility)
watch(() => `${store.boreholes.length}:${store.boundaries.length}:${store.rasters.length}`, reloadSceneData)
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
            <button type="button" :class="{ 'is-active': mapToolState.annotating }" @click="toggleAnnotationMode">
                {{ mapToolState.annotating ? '结束标注' : '点击标注' }}
            </button>
            <button type="button" @click="renameSelectedAnnotation">重命名标注</button>
            <button type="button" @click="deleteSelectedAnnotation">删除标注</button>
            <button type="button" @click="clearAnnotations">清空标注</button>
            <button type="button" :disabled="mapToolState.tilesetLoading" @click="loadMineTilesetAndLocate">
                {{ mapToolState.tilesetLoading ? '模型加载中...' : (mapToolState.tilesetLoaded ? '定位全部模型' : '加载全部模型') }}
            </button>
            <label>
                <input v-model="mapToolState.showLayerModel" type="checkbox">
                分层模型
            </label>
            <span v-if="mapToolResult">{{ mapToolResult }}</span>
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

.map-tools button:disabled {
    cursor: not-allowed;
    opacity: 0.7;
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
