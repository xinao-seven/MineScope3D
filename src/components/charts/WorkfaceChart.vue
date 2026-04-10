<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { ChartDatum } from '../../types/dashboard'

const props = defineProps<{
  data: ChartDatum[]
}>()

const emit = defineEmits<{
  workfaceClick: [name: string]
}>()

/** 构建工作面钻孔数量柱状图配置。 */
function buildChartOption(): EChartsOption {
  return {
    backgroundColor: 'transparent',
    color: ['#38bdf8'],
    grid: { left: 38, right: 18, top: 24, bottom: 70 },
    tooltip: { trigger: 'axis' },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, height: 14, bottom: 6, borderColor: 'rgba(56, 189, 248, 0.26)' },
    ],
    xAxis: {
      type: 'category',
      data: props.data.map((item) => item.name),
      axisLabel: { color: '#c9e7ff', interval: 'auto', rotate: 28, hideOverlap: true },
      axisLine: { lineStyle: { color: '#315f86' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#c9e7ff' },
      splitLine: { lineStyle: { color: 'rgba(56, 189, 248, 0.14)' } },
    },
    series: [
      {
        name: '钻孔数量',
        type: 'bar',
        barMaxWidth: 26,
        data: props.data.map((item) => item.value),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  }
}

/** 将工作面点击事件透传给父组件。 */
function handleChartClick(name: string) {
  emit('workfaceClick', name)
}

const option = computed(buildChartOption)
</script>

<template>
  <BaseChart :option="option" @chart-click="handleChartClick" />
</template>
