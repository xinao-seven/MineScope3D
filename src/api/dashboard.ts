import { apiClient, isApiError } from './client'
import {
    buildDepthDistribution,
    buildLayerDistribution,
    buildWorkfaceBoreholes,
    mockBoreholes,
    mockBoundaries,
    mockOverview,
    mockRasters,
} from '../mock/dashboard'
import type {
    Borehole,
    BoundaryRegion,
    ChartDatum,
    DashboardOverview,
    DashboardPayload,
    RasterLayer,
} from '../types/dashboard'

export interface BoundaryGeoJsonFeatureCollection {
    type: 'FeatureCollection'
    features: Array<{
        type: 'Feature'
        geometry: {
            type: string
            coordinates: unknown
        } | null
        properties: Record<string, unknown>
    }>
}

function buildBoundaryGeoJsonFallback(): BoundaryGeoJsonFeatureCollection {
    return {
        type: 'FeatureCollection',
        features: mockBoundaries.map((boundary) => ({
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [boundary.coordinates],
            },
            properties: {
                id: boundary.id,
                name: boundary.name,
                type: boundary.type,
                area: boundary.area,
                perimeter: boundary.perimeter,
                borehole_count: boundary.borehole_count,
                properties: boundary.properties,
            },
        })),
    }
}

/** 调用接口失败时返回本地演示数据。 */
async function requestWithFallback<T>(request: Promise<{ data: T }>, fallback: T): Promise<T> {
    try {
        const response = await request
        return response.data
    } catch (error) {
        if (isApiError(error)) {
            console.warn('[MineScope3D] 后端接口暂不可用，已切换到演示数据。')
        }
        return fallback
    }
}

/** 获取钻孔列表与分层信息。 */
export function fetchBoreholes(): Promise<Borehole[]> {
    return requestWithFallback(apiClient.get<Borehole[]>('/boreholes/'), mockBoreholes)
}

/** 获取边界对象列表。 */
export function fetchBoundaries(): Promise<BoundaryRegion[]> {
    return requestWithFallback(apiClient.get<BoundaryRegion[]>('/boundaries/'), mockBoundaries)
}

/** 获取边界 GeoJSON（用于 Cesium 直接叠加）。 */
export function fetchBoundaryGeoJson(): Promise<BoundaryGeoJsonFeatureCollection> {
    return requestWithFallback(apiClient.get<BoundaryGeoJsonFeatureCollection>('/boundaries/geojson/'), buildBoundaryGeoJsonFallback())
}

/** 获取 TIFF 专题图层元信息。 */
export function fetchRasters(): Promise<RasterLayer[]> {
    return requestWithFallback(apiClient.get<RasterLayer[]>('/rasters/'), mockRasters)
}

/** 获取大屏总览统计。 */
export function fetchOverview(): Promise<DashboardOverview> {
    return requestWithFallback(apiClient.get<DashboardOverview>('/dashboard/overview/'), mockOverview)
}

/** 获取钻孔分层类型占比。 */
export function fetchLayerDistribution(): Promise<ChartDatum[]> {
    return requestWithFallback(apiClient.get<ChartDatum[]>('/dashboard/layer-distribution/'), buildLayerDistribution())
}

/** 获取各工作面钻孔数量。 */
export function fetchWorkfaceBoreholes(): Promise<ChartDatum[]> {
    return requestWithFallback(apiClient.get<ChartDatum[]>('/dashboard/workface-boreholes/'), buildWorkfaceBoreholes())
}

/** 获取钻孔深度区间分布。 */
export function fetchDepthDistribution(): Promise<ChartDatum[]> {
    return requestWithFallback(apiClient.get<ChartDatum[]>('/dashboard/borehole-depth-distribution/'), buildDepthDistribution())
}

/** 聚合首页需要的全部首屏数据。 */
export async function fetchDashboardPayload(): Promise<DashboardPayload> {
    const [overview, boreholes, boundaries, rasters, layerDistribution, workfaceBoreholes, depthDistribution] = await Promise.all([
        fetchOverview(),
        fetchBoreholes(),
        fetchBoundaries(),
        fetchRasters(),
        fetchLayerDistribution(),
        fetchWorkfaceBoreholes(),
        fetchDepthDistribution(),
    ])

    return {
        overview,
        boreholes,
        boundaries,
        rasters,
        layerDistribution,
        workfaceBoreholes,
        depthDistribution,
    }
}
