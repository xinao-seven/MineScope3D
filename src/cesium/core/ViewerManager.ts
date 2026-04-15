import {
    Color,
    OpenStreetMapImageryProvider,
    UrlTemplateImageryProvider,
    Viewer,
} from 'cesium'
import {
    BASEMAP_CONFIG,
    DEFAULT_FOG_ENABLED,
    DEFAULT_GLOBE_DEPTH_TEST,
    DEFAULT_GLOBE_LIGHTING,
    DEFAULT_SCENE_CONFIG,
    DEFAULT_VIEWER_OPTIONS,
    type BasemapKey,
    type ViewerConstructorOptions,
} from '../constants'

export class ViewerManager {
    readonly viewer: Viewer

    /** 创建 Viewer 并应用项目默认场景配置。 */
    constructor(container: string | HTMLElement, options: Partial<ViewerConstructorOptions> = {}) {
        this.viewer = new Viewer(container, {
            ...DEFAULT_VIEWER_OPTIONS,
            ...options,
        })
        this.applyDefaultSceneConfig()
    }

    /** 应用项目统一场景参数。 */
    applyDefaultSceneConfig(): void {
        this.viewer.scene.backgroundColor = Color.fromCssColorString(DEFAULT_SCENE_CONFIG.backgroundColor)
        this.viewer.scene.globe.baseColor = Color.fromCssColorString(DEFAULT_SCENE_CONFIG.globeBaseColor)
        this.viewer.scene.globe.depthTestAgainstTerrain = DEFAULT_GLOBE_DEPTH_TEST
        this.viewer.scene.globe.enableLighting = DEFAULT_GLOBE_LIGHTING
        this.viewer.scene.fog.enabled = DEFAULT_FOG_ENABLED
        this.viewer.scene.fog.density = DEFAULT_SCENE_CONFIG.fogDensity
        this.viewer.cesiumWidget.creditContainer.setAttribute('style', 'display:none')
    }

    /** 设置场景背景颜色。 */
    setBackgroundColor(cssColor: string): void {
        this.viewer.scene.backgroundColor = Color.fromCssColorString(cssColor)
    }

    /** 控制地形深度测试开关。 */
    setDepthTestAgainstTerrain(enabled: boolean): void {
        this.viewer.scene.globe.depthTestAgainstTerrain = enabled
    }

    /** 控制地球光照开关。 */
    setGlobeLighting(enabled: boolean): void {
        this.viewer.scene.globe.enableLighting = enabled
    }

    /** 控制场景雾效开关。 */
    setFogEnabled(enabled: boolean): void {
        this.viewer.scene.fog.enabled = enabled
    }

    /** 清空场景数据。 */
    clearData(): void {
        this.viewer.dataSources.removeAll()
        this.viewer.entities.removeAll()
    }

    /** 触发 Viewer 尺寸刷新。 */
    resize(): void {
        this.viewer.resize()
    }

    /** 切换快捷底图。 */
    switchBasemap(key: BasemapKey): void {
        const firstLayer = this.viewer.imageryLayers.length > 0 ? this.viewer.imageryLayers.get(0) : null
        if (firstLayer) {
            this.viewer.imageryLayers.remove(firstLayer, true)
        }
        this.viewer.imageryLayers.addImageryProvider(this.createBasemapProvider(key), 0)
    }

    /** 销毁 Cesium Viewer 并释放资源。 */
    destroy(): void {
        if (!this.viewer.isDestroyed()) {
            this.viewer.destroy()
        }
    }

    private createBasemapProvider(key: BasemapKey): OpenStreetMapImageryProvider | UrlTemplateImageryProvider {
        const config = BASEMAP_CONFIG[key]
        if (key === 'osm') {
            return new OpenStreetMapImageryProvider({
                url: config.url,
            })
        }

        return new UrlTemplateImageryProvider({
            url: config.url,
            credit: config.credit,
        })
    }
}
