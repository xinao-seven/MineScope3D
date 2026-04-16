import { HeadingPitchRange, Math as CesiumMath } from 'cesium'
import type { Viewer } from 'cesium'

export type BasemapKey = 'geo' | 'image' | 'osm'

export type ViewerConstructorOptions = NonNullable<ConstructorParameters<typeof Viewer>[1]>

export const DEFAULT_VIEWER_OPTIONS: ViewerConstructorOptions = {
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
    shouldAnimate: true,
}

export const DEFAULT_SCENE_CONFIG = {
    backgroundColor: '#020716',
    globeBaseColor: '#071933',
    depthTestAgainstTerrain: false,
    globeLighting: false,
    fogEnabled: true,
    fogDensity: 0.00045,
}

export const DEFAULT_GLOBE_DEPTH_TEST = DEFAULT_SCENE_CONFIG.depthTestAgainstTerrain
export const DEFAULT_GLOBE_LIGHTING = DEFAULT_SCENE_CONFIG.globeLighting
export const DEFAULT_FOG_ENABLED = DEFAULT_SCENE_CONFIG.fogEnabled

export const DEFAULT_CAMERA_FLY_DURATION = 1.2
export const DEFAULT_CAMERA_HEADING = CesiumMath.toRadians(0)
export const DEFAULT_CAMERA_PITCH = CesiumMath.toRadians(-35)
export const DEFAULT_CAMERA_ROLL = 0

export const DEFAULT_CAMERA_OFFSET = new HeadingPitchRange(
    DEFAULT_CAMERA_HEADING,
    DEFAULT_CAMERA_PITCH,
    2500,
)

export const DEFAULT_POINT_PIXEL_SIZE = 8
export const DEFAULT_LABEL_FONT = '12px Microsoft YaHei'
export const DEFAULT_MEASURE_LABEL_FONT = '14px Microsoft YaHei'
export const DEFAULT_PICK_DISTANCE = Number.POSITIVE_INFINITY

export interface BasemapConfigItem {
    url: string
    credit?: string
    subdomains?: string[]
}

export const BASEMAP_CONFIG: Record<BasemapKey, BasemapConfigItem> = {
    geo: {
        // 国内网络下 ArcGIS 矢量底图容易连接失败，这里改为高德矢量瓦片。
        url: 'https://webrd0{s}.is.autonavi.com/appmaptile?style=7&x={x}&y={y}&z={z}',
        subdomains: ['1', '2', '3', '4'],
        credit: 'Amap Vector',
    },
    image: {
        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        credit: 'Esri World Imagery',
    },
    osm: {
        url: 'https://tile.openstreetmap.org/',
    },
}
