<script setup lang="ts">
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  option: EChartsOption
}>()

const emit = defineEmits<{
  chartClick: [name: string]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

/** 初始化图表实例并绑定事件。 */
function mountChart() {
  if (!chartRef.value) {
    return
  }
  chart = echarts.init(chartRef.value, 'dark')
  chart.on('click', handleChartClick)
  renderChart()
  window.addEventListener('resize', resizeChart)
}

/** 根据传入配置刷新图表。 */
function renderChart() {
  chart?.setOption(props.option, true)
}

/** 将图表点击事件转换为业务名称。 */
function handleChartClick(params: { name?: string }) {
  if (params.name) {
    emit('chartClick', params.name)
  }
}

/** 根据容器变化重算图表尺寸。 */
function resizeChart() {
  chart?.resize()
}

/** 监听图表配置变化并重绘。 */
function handleOptionChange() {
  renderChart()
}

/** 销毁图表实例并释放监听。 */
function disposeChart() {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
  chart = null
}

watch(() => props.option, handleOptionChange, { deep: true })
onMounted(mountChart)
onBeforeUnmount(disposeChart)
</script>

<template>
  <div ref="chartRef" class="base-chart"></div>
</template>
