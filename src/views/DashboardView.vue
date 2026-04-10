<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import BoreholeChart from '../components/charts/BoreholeChart.vue'
import DepthDistributionChart from '../components/charts/DepthDistributionChart.vue'
import WorkfaceChart from '../components/charts/WorkfaceChart.vue'
import CesiumMap from '../components/map/CesiumMap.vue'
import BoreholeList from '../components/panels/BoreholeList.vue'
import LayerControl from '../components/panels/LayerControl.vue'
import LegendPanel from '../components/panels/LegendPanel.vue'
import ObjectDetailPanel from '../components/panels/ObjectDetailPanel.vue'
import OverviewStats from '../components/panels/OverviewStats.vue'
import PanelBlock from '../components/panels/PanelBlock.vue'
import { useDashboardStore } from '../store/dashboard'
import type { Borehole, LayerKey } from '../types/dashboard'

const store = useDashboardStore()
const mapRef = ref<InstanceType<typeof CesiumMap> | null>(null)
const isLeftPanelCollapsed = ref(false)
const isRightPanelCollapsed = ref(false)
const selectedBoreholeId = computed(getSelectedBoreholeId)

/** 加载大屏初始化数据。 */
async function loadDashboard() {
  await store.loadDashboardData()
}

/** 获取当前选中的钻孔编号。 */
function getSelectedBoreholeId(): string | undefined {
  if (store.selection.type !== 'borehole') {
    return undefined
  }
  return (store.selection.item as Borehole).id
}

/** 切换图层显隐状态。 */
function handleToggleLayer(key: LayerKey, visible: boolean) {
  store.setLayerVisible(key, visible)
}

/** 修改图层透明度。 */
function handleOpacityChange(key: LayerKey, opacity: number) {
  store.setLayerOpacity(key, opacity)
}

/** 定位到指定业务图层范围。 */
function handleLocateLayer(key: LayerKey) {
  mapRef.value?.flyToLayer(key)
}

/** 定位到指定钻孔并联动详情面板。 */
function handleLocateBorehole(id: string) {
  mapRef.value?.flyToBorehole(id)
}

/** 响应工作面图表点击并定位代表钻孔。 */
function handleWorkfaceClick(name: string) {
  const boundary = store.boundaries.find((item) => item.name === name)
  if (boundary) {
    mapRef.value?.flyToBoundary(boundary.id)
    return
  }
  store.selectFirstBoreholeByWorkface(name)
  if (selectedBoreholeId.value) {
    mapRef.value?.flyToBorehole(selectedBoreholeId.value)
  }
}

/** 响应分层图点击并保留后续地图筛选入口。 */
function handleLayerSegmentClick(name: string) {
  console.info(`[MineScope3D] 预留按岩层筛选地图入口：${name}`)
}

/** 响应深度区间点击并保留后续地图筛选入口。 */
function handleDepthClick(name: string) {
  console.info(`[MineScope3D] 预留按深度区间筛选地图入口：${name}`)
}

/** 切换左侧面板伸缩状态。 */
function toggleLeftPanel() {
  isLeftPanelCollapsed.value = !isLeftPanelCollapsed.value
}

/** 切换右侧面板伸缩状态。 */
function toggleRightPanel() {
  isRightPanelCollapsed.value = !isRightPanelCollapsed.value
}

onMounted(loadDashboard)
</script>

<template>
  <main class="dashboard-screen">
    <header class="screen-header">
      <div>
        <p>MineScope3D · WebGIS 可视化</p>
        <h1>矿区三维空间数据驾驶舱</h1>
      </div>
      <div class="screen-header__status">
        <span>API / Mock 自适应</span>
        <strong>{{ store.loading ? '数据同步中' : '运行稳定' }}</strong>
      </div>
    </header>

    <section class="dashboard-grid">
      <aside class="side-panel side-panel--left" :class="{ 'is-collapsed': isLeftPanelCollapsed }">
        <button class="panel-toggle panel-toggle--left" type="button" @click="toggleLeftPanel">
          {{ isLeftPanelCollapsed ? '展开左栏' : '收起左栏' }}
        </button>
        <PanelBlock title="全局统计" subtitle="Overview">
          <OverviewStats :overview="store.overview" />
        </PanelBlock>

        <PanelBlock title="图层控制" subtitle="Layer Control">
          <LayerControl
            :layers="store.layers"
            @toggle-layer="handleToggleLayer"
            @opacity-change="handleOpacityChange"
            @locate-layer="handleLocateLayer"
          />
        </PanelBlock>

        <PanelBlock title="钻孔索引" subtitle="Borehole List">
          <BoreholeList
            :boreholes="store.boreholes"
            :selected-id="selectedBoreholeId"
            @locate-borehole="handleLocateBorehole"
          />
        </PanelBlock>
      </aside>

      <section class="map-stage">
        <CesiumMap ref="mapRef" />
      </section>

      <aside class="side-panel side-panel--right" :class="{ 'is-collapsed': isRightPanelCollapsed }">
        <button class="panel-toggle panel-toggle--right" type="button" @click="toggleRightPanel">
          {{ isRightPanelCollapsed ? '展开右栏' : '收起右栏' }}
        </button>
        <PanelBlock title="对象详情" subtitle="Selection">
          <ObjectDetailPanel :selection="store.selection" />
        </PanelBlock>

        <PanelBlock title="分层类型占比" subtitle="ECharts">
          <div class="chart-box chart-box--pie">
            <BoreholeChart :data="store.layerDistribution" @segment-click="handleLayerSegmentClick" />
          </div>
        </PanelBlock>

        <PanelBlock title="专题图图例" subtitle="Raster Legend">
          <LegendPanel :raster="store.activeRaster" />
        </PanelBlock>
      </aside>
    </section>

    <footer class="bottom-analytics">
      <section>
        <h2>工作面钻孔数量</h2>
        <div class="chart-box">
          <WorkfaceChart :data="store.workfaceBoreholes" @workface-click="handleWorkfaceClick" />
        </div>
      </section>
      <section>
        <h2>钻孔深度分布</h2>
        <div class="chart-box">
          <DepthDistributionChart :data="store.depthDistribution" @depth-click="handleDepthClick" />
        </div>
      </section>
    </footer>
  </main>
</template>
