import { defineStore } from 'pinia'
import {
    fetchBoreholes,
    fetchBoundaries,
    fetchDepthDistribution,
    fetchLayerDistribution,
    fetchOverview,
    fetchRasters,
    fetchWorkfaceBoreholes,
} from '../api/dashboard'
import type {
    Borehole,
    BoundaryRegion,
    ChartDatum,
    DashboardOverview,
    LayerKey,
    LayerState,
    RasterLayer,
    SelectionState,
} from '../types/dashboard'

interface DashboardStoreState {
    loading: boolean
    overview: DashboardOverview
    boreholes: Borehole[]
    boundaries: BoundaryRegion[]
    rasters: RasterLayer[]
    layerDistribution: ChartDatum[]
    workfaceBoreholes: ChartDatum[]
    depthDistribution: ChartDatum[]
    layers: LayerState[]
    selection: SelectionState
}

/** 生成默认图层控制状态。 */
function createDefaultLayers(): LayerState[] {
    return [
        { key: 'boreholes', name: '钻孔点图层', visible: true, opacity: 1, count: 0, description: '点位、编号、分层详情' },
        { key: 'mineBoundary', name: '矿区边界', visible: true, opacity: 0.72, count: 0, description: 'SHP 面边界入库后返回' },
        { key: 'workfaceBoundary', name: '工作面边界', visible: true, opacity: 0.62, count: 0, description: '工作面边界分区' },
        { key: 'raster', name: 'TIFF 专题图', visible: true, opacity: 0.62, count: 0, description: '沉降、热力、风险专题图' },
    ]
}

/** 创建大屏初始状态。 */
function createInitialState(): DashboardStoreState {
    return {
        loading: false,
        overview: { boreholeTotal: 0, workfaceTotal: 0, boundaryTotal: 0, rasterTotal: 0 },
        boreholes: [],
        boundaries: [],
        rasters: [],
        layerDistribution: [],
        workfaceBoreholes: [],
        depthDistribution: [],
        layers: createDefaultLayers(),
        selection: { type: 'none', item: null },
    }
}

export const useDashboardStore = defineStore('dashboard', {
    state: createInitialState,
    getters: {
        /** 获取当前激活的 TIFF 图层。 */
        activeRaster(state): RasterLayer | null {
            return state.rasters[0] ?? null
        },
        /** 生成图层变化签名，供 Cesium 组件监听。 */
        layerSignature(state): string {
            return state.layers.map((layer) => `${layer.key}:${layer.visible}:${layer.opacity}`).join('|')
        },
    },
    actions: {
        /** 加载大屏首屏所需数据。 */
        async loadDashboardData() {
            this.loading = true
            try {
                const [overview, boreholes, boundaries, rasters] = await Promise.all([
                    fetchOverview(),
                    fetchBoreholes(),
                    fetchBoundaries(),
                    fetchRasters(),
                ])

                this.overview = overview
                this.boreholes = boreholes
                this.boundaries = boundaries
                this.rasters = rasters
                this.refreshLayerCounts()
                this.selectBorehole(this.boreholes[0]?.id)
                void this.loadChartData()
            } finally {
                this.loading = false
            }
        },
        /** 异步补齐图表数据，避免阻塞首屏。 */
        async loadChartData() {
            try {
                const [layerDistribution, workfaceBoreholes, depthDistribution] = await Promise.all([
                    fetchLayerDistribution(),
                    fetchWorkfaceBoreholes(),
                    fetchDepthDistribution(),
                ])
                this.layerDistribution = layerDistribution
                this.workfaceBoreholes = workfaceBoreholes
                this.depthDistribution = depthDistribution
            } catch (error) {
                console.warn('[MineScope3D] 图表数据加载失败', error)
            }
        },
        /** 刷新图层面板中的数量统计。 */
        refreshLayerCounts() {
            for (const layer of this.layers) {
                if (layer.key === 'boreholes') {
                    layer.count = this.boreholes.length
                }
                if (layer.key === 'mineBoundary') {
                    layer.count = this.boundaries.filter((boundary) => boundary.type === 'mine').length
                }
                if (layer.key === 'workfaceBoundary') {
                    layer.count = this.boundaries.filter((boundary) => boundary.type === 'workface').length
                }
                if (layer.key === 'raster') {
                    layer.count = this.rasters.length
                }
            }
        },
        /** 切换指定图层显隐。 */
        setLayerVisible(key: LayerKey, visible: boolean) {
            const layer = this.layers.find((item) => item.key === key)
            if (layer) {
                layer.visible = visible
            }
        },
        /** 设置指定图层透明度。 */
        setLayerOpacity(key: LayerKey, opacity: number) {
            const layer = this.layers.find((item) => item.key === key)
            if (layer) {
                layer.opacity = opacity
            }
        },
        /** 读取指定图层配置。 */
        getLayerState(key: LayerKey): LayerState | undefined {
            return this.layers.find((layer) => layer.key === key)
        },
        /** 选中钻孔并同步右侧详情。 */
        selectBorehole(id?: string) {
            const borehole = this.boreholes.find((item) => item.id === id)
            this.selection = borehole ? { type: 'borehole', item: borehole } : { type: 'none', item: null }
        },
        /** 选中边界并同步右侧详情。 */
        selectBoundary(id?: string) {
            const boundary = this.boundaries.find((item) => item.id === id)
            this.selection = boundary ? { type: 'boundary', item: boundary } : { type: 'none', item: null }
        },
        /** 选中专题图并同步右侧详情。 */
        selectRaster(id?: string) {
            const raster = this.rasters.find((item) => item.id === id)
            this.selection = raster ? { type: 'raster', item: raster } : { type: 'none', item: null }
        },
        /** 按工作面定位一个代表钻孔。 */
        selectFirstBoreholeByWorkface(workface: string) {
            const borehole = this.boreholes.find((item) => item.workface_name === workface)
            this.selectBorehole(borehole?.id)
        },
    },
})
