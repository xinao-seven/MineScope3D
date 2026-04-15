<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import BoreholeList from '../components/panels/BoreholeList.vue'
import LayerControl from '../components/panels/LayerControl.vue'
import LegendPanel from '../components/panels/LegendPanel.vue'
import ObjectDetailPanel from '../components/panels/ObjectDetailPanel.vue'
import OverviewStats from '../components/panels/OverviewStats.vue'
import PanelBlock from '../components/panels/PanelBlock.vue'
import { useDashboardStore } from '../store/dashboard'
import type { Borehole, LayerKey } from '../types/dashboard'

const CesiumMap = defineAsyncComponent(() => import('../components/map/CesiumMap.vue'))
const BoreholeChart = defineAsyncComponent(() => import('../components/charts/BoreholeChart.vue'))

interface MapExpose {
    flyToLayer: (key: LayerKey) => void
    flyToBorehole: (id: string) => void
}

const store = useDashboardStore()
const mapRef = ref<MapExpose | null>(null)
const isLeftPanelCollapsed = ref(false)
const isRightPanelCollapsed = ref(false)
const shouldMountMap = ref(false)
const shouldMountCharts = ref(false)
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

/** 响应分层图点击并保留后续地图筛选入口。 */
function handleLayerSegmentClick(name: string) {
    console.info(`[MineScope3D] 预留按岩层筛选地图入口：${name}`)
}

/** 切换左侧面板伸缩状态。 */
function toggleLeftPanel() {
    isLeftPanelCollapsed.value = !isLeftPanelCollapsed.value
}

/** 切换右侧面板伸缩状态。 */
function toggleRightPanel() {
    isRightPanelCollapsed.value = !isRightPanelCollapsed.value
}

/** 延后挂载地图，降低首帧阻塞。 */
function scheduleMapMount() {
    const mount = () => {
        shouldMountMap.value = true
    }

    if (typeof window.requestIdleCallback === 'function') {
        window.requestIdleCallback(mount, { timeout: 700 })
        return
    }

    window.setTimeout(mount, 120)
}

/** 延后挂载图表，避开首屏关键链路。 */
function scheduleChartsMount() {
    const mount = () => {
        shouldMountCharts.value = true
    }

    if (typeof window.requestIdleCallback === 'function') {
        window.requestIdleCallback(mount, { timeout: 1200 })
        return
    }

    window.setTimeout(mount, 360)
}

onMounted(() => {
    void loadDashboard()
    scheduleMapMount()
    scheduleChartsMount()
})
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
                    <LayerControl :layers="store.layers" @toggle-layer="handleToggleLayer"
                        @opacity-change="handleOpacityChange" @locate-layer="handleLocateLayer" />
                </PanelBlock>

                <PanelBlock title="钻孔索引" subtitle="Borehole List">
                    <BoreholeList :boreholes="store.boreholes" :selected-id="selectedBoreholeId"
                        @locate-borehole="handleLocateBorehole" />
                </PanelBlock>
            </aside>

            <section class="map-stage">
                <CesiumMap v-if="shouldMountMap" ref="mapRef" />
                <div v-else class="map-stage__placeholder">地图引擎加载中...</div>
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
                        <BoreholeChart v-if="shouldMountCharts" :data="store.layerDistribution"
                            @segment-click="handleLayerSegmentClick" />
                        <div v-else class="chart-placeholder">图表加载中...</div>
                    </div>
                </PanelBlock>

                <PanelBlock title="专题图图例" subtitle="Raster Legend">
                    <LegendPanel :raster="store.activeRaster" />
                </PanelBlock>
            </aside>
        </section>

    </main>
</template>

<style scoped>
.dashboard-screen {
    position: relative;
    width: min(1920px, 100vw);
    height: 100vh;
    margin: 0 auto;
    padding: 10px;
    overflow: hidden;
}

.screen-header {
    position: absolute;
    z-index: 6;
    top: 10px;
    left: 10px;
    right: 10px;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 18px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: linear-gradient(90deg, rgba(8, 31, 72, 0.82), rgba(3, 12, 32, 0.58));
    box-shadow: var(--shadow);
}

.screen-header p,
.screen-header h1 {
    margin: 0;
}

.screen-header p,
.screen-header__status span {
    color: var(--muted);
}

.screen-header h1 {
    margin-top: 2px;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0;
    color: #f5fbff;
}

.screen-header__status {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
}

.screen-header__status strong {
    color: var(--green);
}

.dashboard-grid {
    position: absolute;
    inset: 74px 10px 10px;
    min-height: 0;
}

.side-panel {
    position: absolute;
    z-index: 4;
    top: 10px;
    bottom: 10px;
    width: 318px;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(96, 165, 250, 0.46) transparent;
    transition: transform 0.26s ease, opacity 0.26s ease;
}

.side-panel--left {
    left: 10px;
}

.side-panel--right {
    right: 10px;
    width: 348px;
}

.side-panel.is-collapsed.side-panel--left {
    transform: none;
}

.side-panel.is-collapsed.side-panel--right {
    transform: none;
}

.side-panel.is-collapsed {
    pointer-events: none;
}

.panel-toggle {
    position: sticky;
    top: 0;
    z-index: 10;
    height: 32px;
    cursor: pointer;
    border: 1px solid rgba(125, 211, 252, 0.52);
    border-radius: 8px;
    color: #eaf6ff;
    background: rgba(5, 19, 48, 0.82);
    box-shadow: 0 12px 34px rgba(0, 0, 0, 0.26);
    backdrop-filter: blur(12px);
}

.side-panel.is-collapsed .panel-toggle {
    position: fixed;
    top: 88px;
    width: 86px;
    pointer-events: auto;
}

.side-panel.is-collapsed .panel-block {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease, transform 0.24s ease;
}

.side-panel.is-collapsed.side-panel--left .panel-block {
    transform: translateX(calc(-100% - 22px));
}

.side-panel.is-collapsed.side-panel--right .panel-block {
    transform: translateX(calc(100% + 22px));
}

.side-panel.is-collapsed.side-panel--left .panel-toggle {
    left: 18px;
    transform: translateX(calc(100% + 8px));
}

.side-panel.is-collapsed.side-panel--right .panel-toggle {
    right: 18px;
    transform: translateX(calc(-100% - 8px));
}

.map-stage {
    position: absolute;
    inset: 0;
    border: 1px solid var(--line-strong);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    background: #020716;
}

.map-stage__placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    letter-spacing: 0.5px;
    background:
        radial-gradient(circle at 68% 12%, rgba(56, 189, 248, 0.12), transparent 30%),
        radial-gradient(circle at 24% 76%, rgba(35, 209, 139, 0.12), transparent 35%),
        #020716;
}

.chart-box {
    height: 100px;
    min-height: 0;
}

.chart-box--pie {
    height: 188px;
}

.chart-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    border: 1px dashed rgba(125, 211, 252, 0.24);
    border-radius: 8px;
    background: rgba(5, 19, 48, 0.32);
}

@media (max-width: 1500px) {
    .dashboard-screen {
        width: 1500px;
    }

    .dashboard-grid {
        min-height: 0;
    }

    .side-panel {
        width: 300px;
    }

    .side-panel--right {
        width: 330px;
    }
}
</style>
