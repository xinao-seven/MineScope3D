export type LayerKey = 'boreholes' | 'mineBoundary' | 'workfaceBoundary' | 'raster'

export type BoundaryType = 'mine' | 'workface' | 'region'

export type SelectionType = 'none' | 'borehole' | 'boundary' | 'raster'

export interface BoreholeLayer {
    id: string
    layer_name: string
    top_depth: number
    thickness: number
    bottom_depth: number
    color: string
    sort_order: number
}

export interface Borehole {
    id: string
    borehole_code: string
    name: string
    longitude: number
    latitude: number
    elevation: number
    depth_total: number
    workface_name: string
    remark: string
    layers: BoreholeLayer[]
}

export interface BoundaryRegion {
    id: string
    name: string
    type: BoundaryType
    area: number
    perimeter: number
    borehole_count: number
    properties: Record<string, string | number>
    coordinates: [number, number][]
}

export interface RasterLegendItem {
    label: string
    color: string
    value: string
}

export interface RasterBounds {
    west: number
    south: number
    east: number
    north: number
}

export interface RasterLayer {
    id: string
    name: string
    type: string
    url: string
    preview_url?: string
    bounds: RasterBounds
    opacity: number
    legend_config: RasterLegendItem[]
    description: string
    time_tag: string
}

export interface DashboardOverview {
    boreholeTotal: number
    workfaceTotal: number
    boundaryTotal: number
    rasterTotal: number
}

export interface ChartDatum {
    name: string
    value: number
}

export interface LayerState {
    key: LayerKey
    name: string
    visible: boolean
    opacity: number
    count: number
    description: string
}

export interface SelectionState {
    type: SelectionType
    item: Borehole | BoundaryRegion | RasterLayer | null
}

export interface DashboardPayload {
    overview: DashboardOverview
    boreholes: Borehole[]
    boundaries: BoundaryRegion[]
    rasters: RasterLayer[]
    layerDistribution: ChartDatum[]
    workfaceBoreholes: ChartDatum[]
    depthDistribution: ChartDatum[]
}
