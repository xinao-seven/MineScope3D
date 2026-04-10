<script setup lang="ts">
import {
    Cartesian2,
    Cartesian3,
    Color,
    ColorMaterialProperty,
    ConstantProperty,
    Entity,
    HeightReference,
    ImageryLayer,
    JulianDate,
    LabelStyle,
    OpenStreetMapImageryProvider,
    PolygonHierarchy,
    Rectangle,
    ScreenSpaceEventHandler,
    ScreenSpaceEventType,
    SingleTileImageryProvider,
    UrlTemplateImageryProvider,
    VerticalOrigin,
    Viewer,
    defined,
} from 'cesium'
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useDashboardStore } from '../../store/dashboard'
import type { Borehole, BoundaryRegion, LayerKey, RasterLayer } from '../../types/dashboard'

const store = useDashboardStore()
const mapContainer = ref<HTMLDivElement | null>(null)
const tooltip = reactive({ visible: false, x: 0, y: 0, text: '' })
const activeBasemapKey = ref('geo')

const basemapOptions = [
    { key: 'geo', name: '地理' },
    { key: 'image', name: '影像' },
    { key: 'osm', name: '街图' },
]

let viewer: Viewer | null = null
let clickHandler: ScreenSpaceEventHandler | null = null
let hoverHandler: ScreenSpaceEventHandler | null = null
let rasterLayer: ImageryLayer | null = null
let hasAutoFlownToMine = false
const boreholeEntities = new Map<string, Entity>()
const boundaryEntities = new Map<string, Entity[]>()

/** 挂载 Cesium 场景并加载首屏数据。 */
function mountScene() {
    if (!mapContainer.value || viewer) {
        return
    }

    viewer = new Viewer(mapContainer.value, {
        animation: false,
        timeline: false,
        geocoder: false,
        homeButton: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        baseLayerPicker: true,
        fullscreenButton: false,
        infoBox: false,
        selectionIndicator: false,
    })

    configureScene()
    switchBasemap('geo')
    bindMapInteractions()
    reloadSceneData()
}

/** 配置深色大屏需要的场景基础效果。 */
function configureScene() {
    if (!viewer) {
        return
    }
    viewer.scene.backgroundColor = Color.fromCssColorString('#020716')
    viewer.scene.globe.baseColor = Color.fromCssColorString('#071933')
    viewer.scene.globe.depthTestAgainstTerrain = false
    viewer.scene.fog.enabled = true
    viewer.scene.fog.density = 0.00045
    viewer.cesiumWidget.creditContainer.setAttribute('style', 'display:none')
}

/** 绑定地图点击和 hover 交互。 */
function bindMapInteractions() {
    if (!viewer) {
        return
    }

    clickHandler = new ScreenSpaceEventHandler(viewer.scene.canvas)
    hoverHandler = new ScreenSpaceEventHandler(viewer.scene.canvas)
    clickHandler.setInputAction(handleMapClick, ScreenSpaceEventType.LEFT_CLICK)
    hoverHandler.setInputAction(handleMouseMove, ScreenSpaceEventType.MOUSE_MOVE)
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
    if (!viewer) {
        return
    }

    viewer.entities.removeAll()
    boreholeEntities.clear()
    boundaryEntities.clear()
    removeRasterLayer()
    addBoreholes(store.boreholes)
    addBoundaries(store.boundaries)
    void addRasterLayer(store.activeRaster)
    syncLayerVisibility()
    flyToMineOnce()
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
    for (const borehole of boreholes) {
        if (borehole.longitude === 0 && borehole.latitude === 0) {
            continue
        }
        const entity = viewer?.entities.add({
            id: `borehole-${borehole.id}`,
            name: borehole.name,
            position: Cartesian3.fromDegrees(borehole.longitude, borehole.latitude, borehole.elevation),
            point: {
                pixelSize: 13,
                color: Color.fromCssColorString('#f2c94c'),
                outlineColor: Color.fromCssColorString('#04110e'),
                outlineWidth: 3,
                heightReference: HeightReference.NONE,
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
            label: {
                text: borehole.borehole_code,
                font: '13px Microsoft YaHei',
                fillColor: Color.fromCssColorString('#eafff7'),
                outlineColor: Color.fromCssColorString('#04110e'),
                outlineWidth: 3,
                style: LabelStyle.FILL_AND_OUTLINE,
                verticalOrigin: VerticalOrigin.BOTTOM,
                pixelOffset: new Cartesian2(0, -18),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
            },
            properties: {
                domainType: 'borehole',
                targetId: borehole.id,
            },
        })

        if (entity) {
            boreholeEntities.set(borehole.id, entity)
        }
    }
}

/** 根据底图键名创建 Cesium 影像 Provider。 */
function createBasemapProvider(key: string) {
    if (key === 'image') {
        return new UrlTemplateImageryProvider({
            url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            credit: 'Esri World Imagery',
        })
    }
    if (key === 'osm') {
        return new OpenStreetMapImageryProvider({
            url: 'https://tile.openstreetmap.org/',
        })
    }
    return new UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        credit: 'Esri World Topographic Map',
    })
}

/** 切换快捷底图，同时保留 Cesium 原生底图选择器。 */
function switchBasemap(key: string) {
    if (!viewer) {
        return
    }
    const firstLayer = viewer.imageryLayers.length > 0 ? viewer.imageryLayers.get(0) : null
    if (firstLayer) {
        viewer.imageryLayers.remove(firstLayer, true)
    }
    activeBasemapKey.value = key
    viewer.imageryLayers.addImageryProvider(createBasemapProvider(key), 0)
}

/** 添加矿区与工作面边界实体。 */
function addBoundaries(boundaries: BoundaryRegion[]) {
    for (const boundary of boundaries) {
        const positions = Cartesian3.fromDegreesArray(boundary.coordinates.flat())
        const color = boundary.type === 'mine' ? Color.fromCssColorString('#23d18b') : Color.fromCssColorString('#56ccf2')
        const polygon = viewer?.entities.add({
            id: `boundary-${boundary.id}`,
            name: boundary.name,
            polygon: {
                hierarchy: new PolygonHierarchy(positions),
                material: color.withAlpha(boundary.type === 'mine' ? 0.12 : 0.18),
                outline: true,
                outlineColor: color.withAlpha(0.95),
            },
            polyline: {
                positions,
                width: boundary.type === 'mine' ? 4 : 3,
                material: color.withAlpha(0.95),
                clampToGround: true,
            },
            properties: {
                domainType: 'boundary',
                targetId: boundary.id,
                boundaryType: boundary.type,
            },
        })

        if (polygon) {
            boundaryEntities.set(boundary.id, [polygon])
        }
    }
}

/** 添加 TIFF 元信息对应的影像叠加层。 */
async function addRasterLayer(raster: RasterLayer | null) {
    if (!viewer || !raster) {
        return
    }

    const provider = await SingleTileImageryProvider.fromUrl(raster.url || createRasterDataUrl(raster), {
        rectangle: Rectangle.fromDegrees(raster.bounds.west, raster.bounds.south, raster.bounds.east, raster.bounds.north),
    })
    rasterLayer = viewer.imageryLayers.addImageryProvider(provider)
    rasterLayer.alpha = store.getLayerState('raster')?.opacity ?? raster.opacity
    rasterLayer.show = store.getLayerState('raster')?.visible ?? true
}

/** 生成用于演示 TIFF 叠加的栅格图片。 */
function createRasterDataUrl(raster: RasterLayer): string {
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 512
    const context = canvas.getContext('2d')
    if (!context) {
        return ''
    }

    const gradient = context.createLinearGradient(0, 0, 512, 512)
    raster.legend_config.forEach((item, index) => {
        gradient.addColorStop(index / Math.max(raster.legend_config.length - 1, 1), item.color)
    })
    context.globalAlpha = 0.78
    context.fillStyle = gradient
    context.fillRect(0, 0, 512, 512)
    context.globalAlpha = 0.34
    context.strokeStyle = '#06110e'
    context.lineWidth = 5
    for (let index = 0; index < 9; index += 1) {
        context.beginPath()
        context.ellipse(210 + index * 16, 270 - index * 10, 170 - index * 9, 74 - index * 4, -0.35, 0, Math.PI * 2)
        context.stroke()
    }
    return canvas.toDataURL('image/png')
}

/** 移除当前专题影像图层。 */
function removeRasterLayer() {
    if (viewer && rasterLayer) {
        viewer.imageryLayers.remove(rasterLayer, true)
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
    for (const entity of boreholeEntities.values()) {
        entity.show = layer?.visible ?? true
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
            entity.show = layer?.visible ?? true
            if (entity.polygon) {
                entity.polygon.material = new ColorMaterialProperty(color.withAlpha((layer?.opacity ?? 0.72) * 0.24))
                entity.polygon.outlineColor = new ConstantProperty(color.withAlpha(layer?.opacity ?? 0.72))
            }
            if (entity.polyline) {
                entity.polyline.material = new ColorMaterialProperty(color.withAlpha(layer?.opacity ?? 0.72))
            }
        }
    }
}

/** 同步专题图图层可见性与透明度。 */
function syncRasterVisibility() {
    const layer = store.getLayerState('raster')
    if (rasterLayer) {
        rasterLayer.show = layer?.visible ?? true
        rasterLayer.alpha = layer?.opacity ?? 0.62
    }
}

/** 处理地图点击选中对象。 */
function handleMapClick(event: { position: Cartesian2 }) {
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
    const picked = viewer?.scene.pick(position)
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
    if (viewer && borehole && entity) {
        viewer.flyTo(entity, {
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
    if (viewer && boundary) {
        store.selectBoundary(id)
        viewer.camera.flyTo({ destination: buildBoundaryRectangle(boundary), duration: 1.1 })
    }
}

/** 飞行定位到指定图层范围。 */
function flyToLayer(key: LayerKey) {
    if (!viewer) {
        return
    }

    if (key === 'boreholes') {
        const destination = buildBoreholeRectangle()
        if (destination) {
            viewer.camera.flyTo({ destination, duration: 1.1 })
        }
        return
    }
    if (key === 'raster' && store.activeRaster) {
        store.selectRaster(store.activeRaster.id)
        viewer.camera.flyTo({ destination: buildRasterRectangle(store.activeRaster), duration: 1.1 })
        return
    }

    const targetBoundary = store.boundaries.find((boundary) => {
        return key === 'mineBoundary' ? boundary.type === 'mine' : boundary.type === 'workface'
    })
    if (targetBoundary) {
        store.selectBoundary(targetBoundary.id)
        viewer.camera.flyTo({ destination: buildBoundaryRectangle(targetBoundary), duration: 1.1 })
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

/** 销毁 Cesium 场景和事件处理器。 */
function destroyScene() {
    clickHandler?.destroy()
    hoverHandler?.destroy()
    if (viewer && !viewer.isDestroyed()) {
        viewer.destroy()
    }
    viewer = null
    clickHandler = null
    hoverHandler = null
}

watch(readLayerSignature, syncLayerVisibility)
watch(readDataSignature, reloadSceneData)
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
