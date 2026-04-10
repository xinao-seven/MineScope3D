import type {
  Borehole,
  BoundaryRegion,
  ChartDatum,
  DashboardOverview,
  RasterLayer,
} from '../types/dashboard'

export const mockBoreholes: Borehole[] = [
  {
    id: '1',
    borehole_code: 'JJ-101',
    name: '锦界一号钻孔',
    longitude: 110.2145,
    latitude: 39.2892,
    elevation: 1184,
    depth_total: 236.8,
    workface_name: '一盘区 1201 工作面',
    remark: '主采煤层控制孔',
    layers: [
      { id: '1-1', layer_name: '第四系覆盖层', top_depth: 0, thickness: 18.5, bottom_depth: 18.5, color: '#6fcf97', sort_order: 1 },
      { id: '1-2', layer_name: '细砂岩', top_depth: 18.5, thickness: 62.3, bottom_depth: 80.8, color: '#56ccf2', sort_order: 2 },
      { id: '1-3', layer_name: '泥岩', top_depth: 80.8, thickness: 74.2, bottom_depth: 155, color: '#bb6bd9', sort_order: 3 },
      { id: '1-4', layer_name: '煤层', top_depth: 155, thickness: 8.4, bottom_depth: 163.4, color: '#f2c94c', sort_order: 4 },
      { id: '1-5', layer_name: '粉砂岩', top_depth: 163.4, thickness: 73.4, bottom_depth: 236.8, color: '#f2994a', sort_order: 5 },
    ],
  },
  {
    id: '2',
    borehole_code: 'JJ-118',
    name: '锦界二号钻孔',
    longitude: 110.2452,
    latitude: 39.3015,
    elevation: 1191,
    depth_total: 288.4,
    workface_name: '一盘区 1201 工作面',
    remark: '沉降专题图校核点',
    layers: [
      { id: '2-1', layer_name: '黄土层', top_depth: 0, thickness: 25.6, bottom_depth: 25.6, color: '#f2c94c', sort_order: 1 },
      { id: '2-2', layer_name: '砂质泥岩', top_depth: 25.6, thickness: 94.1, bottom_depth: 119.7, color: '#eb5757', sort_order: 2 },
      { id: '2-3', layer_name: '细砂岩', top_depth: 119.7, thickness: 72.8, bottom_depth: 192.5, color: '#56ccf2', sort_order: 3 },
      { id: '2-4', layer_name: '煤层', top_depth: 192.5, thickness: 9.2, bottom_depth: 201.7, color: '#f2c94c', sort_order: 4 },
      { id: '2-5', layer_name: '泥岩', top_depth: 201.7, thickness: 86.7, bottom_depth: 288.4, color: '#bb6bd9', sort_order: 5 },
    ],
  },
  {
    id: '3',
    borehole_code: 'JJ-203',
    name: '锦界三号钻孔',
    longitude: 110.2688,
    latitude: 39.2744,
    elevation: 1169,
    depth_total: 214.3,
    workface_name: '二盘区 2203 工作面',
    remark: '边界控制孔',
    layers: [
      { id: '3-1', layer_name: '第四系覆盖层', top_depth: 0, thickness: 15.4, bottom_depth: 15.4, color: '#6fcf97', sort_order: 1 },
      { id: '3-2', layer_name: '粉砂岩', top_depth: 15.4, thickness: 80.2, bottom_depth: 95.6, color: '#f2994a', sort_order: 2 },
      { id: '3-3', layer_name: '泥岩', top_depth: 95.6, thickness: 61.9, bottom_depth: 157.5, color: '#bb6bd9', sort_order: 3 },
      { id: '3-4', layer_name: '煤层', top_depth: 157.5, thickness: 7.8, bottom_depth: 165.3, color: '#f2c94c', sort_order: 4 },
      { id: '3-5', layer_name: '细砂岩', top_depth: 165.3, thickness: 49, bottom_depth: 214.3, color: '#56ccf2', sort_order: 5 },
    ],
  },
  {
    id: '4',
    borehole_code: 'JJ-306',
    name: '锦界四号钻孔',
    longitude: 110.2327,
    latitude: 39.2558,
    elevation: 1176,
    depth_total: 342.6,
    workface_name: '二盘区 2205 工作面',
    remark: '深部结构验证孔',
    layers: [
      { id: '4-1', layer_name: '黄土层', top_depth: 0, thickness: 32.1, bottom_depth: 32.1, color: '#f2c94c', sort_order: 1 },
      { id: '4-2', layer_name: '砂质泥岩', top_depth: 32.1, thickness: 108.5, bottom_depth: 140.6, color: '#eb5757', sort_order: 2 },
      { id: '4-3', layer_name: '粉砂岩', top_depth: 140.6, thickness: 90.6, bottom_depth: 231.2, color: '#f2994a', sort_order: 3 },
      { id: '4-4', layer_name: '煤层', top_depth: 231.2, thickness: 10.1, bottom_depth: 241.3, color: '#f2c94c', sort_order: 4 },
      { id: '4-5', layer_name: '泥岩', top_depth: 241.3, thickness: 101.3, bottom_depth: 342.6, color: '#bb6bd9', sort_order: 5 },
    ],
  },
  {
    id: '5',
    borehole_code: 'JJ-412',
    name: '锦界五号钻孔',
    longitude: 110.2876,
    latitude: 39.3184,
    elevation: 1203,
    depth_total: 261.9,
    workface_name: '北翼 3102 工作面',
    remark: '北翼专题图约束点',
    layers: [
      { id: '5-1', layer_name: '第四系覆盖层', top_depth: 0, thickness: 20.2, bottom_depth: 20.2, color: '#6fcf97', sort_order: 1 },
      { id: '5-2', layer_name: '细砂岩', top_depth: 20.2, thickness: 79.5, bottom_depth: 99.7, color: '#56ccf2', sort_order: 2 },
      { id: '5-3', layer_name: '砂质泥岩', top_depth: 99.7, thickness: 81.4, bottom_depth: 181.1, color: '#eb5757', sort_order: 3 },
      { id: '5-4', layer_name: '煤层', top_depth: 181.1, thickness: 8.8, bottom_depth: 189.9, color: '#f2c94c', sort_order: 4 },
      { id: '5-5', layer_name: '泥岩', top_depth: 189.9, thickness: 72, bottom_depth: 261.9, color: '#bb6bd9', sort_order: 5 },
    ],
  },
]

export const mockBoundaries: BoundaryRegion[] = [
  {
    id: 'mine-1',
    name: '锦界矿区边界',
    type: 'mine',
    area: 15.8,
    perimeter: 18.7,
    borehole_count: 5,
    properties: { 数据源: 'SHP 入库', 坐标系: 'EPSG:4326' },
    coordinates: [
      [110.178, 39.237],
      [110.318, 39.238],
      [110.323, 39.334],
      [110.174, 39.332],
      [110.178, 39.237],
    ],
  },
  {
    id: 'workface-1201',
    name: '1201 工作面边界',
    type: 'workface',
    area: 2.1,
    perimeter: 6.4,
    borehole_count: 2,
    properties: { 盘区: '一盘区', 状态: '重点监测' },
    coordinates: [
      [110.202, 39.281],
      [110.256, 39.284],
      [110.254, 39.311],
      [110.199, 39.307],
      [110.202, 39.281],
    ],
  },
  {
    id: 'workface-2205',
    name: '2205 工作面边界',
    type: 'workface',
    area: 2.8,
    perimeter: 7.2,
    borehole_count: 2,
    properties: { 盘区: '二盘区', 状态: '采前分析' },
    coordinates: [
      [110.219, 39.247],
      [110.284, 39.25],
      [110.281, 39.284],
      [110.215, 39.28],
      [110.219, 39.247],
    ],
  },
]

export const mockRasters: RasterLayer[] = [
  {
    id: 'raster-subsidence',
    name: 'InSAR 沉降专题图',
    type: 'subsidence',
    url: '',
    bounds: { west: 110.188, south: 39.244, east: 110.311, north: 39.326 },
    opacity: 0.62,
    legend_config: [
      { label: '稳定区', value: '0 - 12 mm', color: '#23d18b' },
      { label: '轻微沉降', value: '12 - 28 mm', color: '#f2c94c' },
      { label: '显著沉降', value: '28 - 45 mm', color: '#f2994a' },
      { label: '重点预警', value: '> 45 mm', color: '#eb5757' },
    ],
    description: '基于静态资源或切片服务叠加的 TIFF 元信息示例。',
    time_tag: '2026-Q1',
  },
]

export const mockOverview: DashboardOverview = {
  boreholeTotal: mockBoreholes.length,
  workfaceTotal: new Set(mockBoreholes.map(getBoreholeWorkfaceName)).size,
  boundaryTotal: mockBoundaries.length,
  rasterTotal: mockRasters.length,
}

/** 获取钻孔所属工作面名称。 */
export function getBoreholeWorkfaceName(borehole: Borehole): string {
  return borehole.workface_name
}

/** 统计分层类型占比。 */
export function buildLayerDistribution(): ChartDatum[] {
  const layerCounter = new Map<string, number>()
  for (const borehole of mockBoreholes) {
    for (const layer of borehole.layers) {
      layerCounter.set(layer.layer_name, (layerCounter.get(layer.layer_name) ?? 0) + 1)
    }
  }
  return Array.from(layerCounter, ([name, value]) => ({ name, value }))
}

/** 统计各工作面的钻孔数量。 */
export function buildWorkfaceBoreholes(): ChartDatum[] {
  const workfaceCounter = new Map<string, number>()
  for (const borehole of mockBoreholes) {
    workfaceCounter.set(borehole.workface_name, (workfaceCounter.get(borehole.workface_name) ?? 0) + 1)
  }
  return Array.from(workfaceCounter, ([name, value]) => ({ name, value }))
}

/** 按总深度区间统计钻孔数量。 */
export function buildDepthDistribution(): ChartDatum[] {
  const ranges = [
    { name: '< 240m', min: 0, max: 240 },
    { name: '240 - 280m', min: 240, max: 280 },
    { name: '280 - 320m', min: 280, max: 320 },
    { name: '> 320m', min: 320, max: Number.POSITIVE_INFINITY },
  ]

  return ranges.map((range) => ({
    name: range.name,
    value: mockBoreholes.filter((borehole) => borehole.depth_total >= range.min && borehole.depth_total < range.max).length,
  }))
}
