<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { ChartDatum } from '../../types/dashboard'

const props = defineProps<{
  data: ChartDatum[]
}>()

const emit = defineEmits<{
  depthClick: [name: string]
}>()

/** 构建钻孔深度分布图配置。 */
function buildChartOption(): EChartsOption {
  return {
    backgroundColor: 'transparent',
    color: ['#60a5fa'],
    grid: { left: 38, right: 18, top: 22, bottom: 52 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: props.data.map((item) => item.name),
      axisLabel: { color: '#c9e7ff', interval: 'auto', hideOverlap: true },
      axisLine: { lineStyle: { color: '#315f86' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#c9e7ff' },
      splitLine: { lineStyle: { color: 'rgba(96, 165, 250, 0.14)' } },
    },
    series: [
      {
        name: '钻孔数量',
        type: 'bar',
        barMaxWidth: 30,
        data: props.data.map((item) => item.value),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  }
}

/** 将深度区间点击事件透传给父组件。 */
function handleChartClick(name: string) {
  emit('depthClick', name)
}

const option = computed(buildChartOption)
</script>

<template>
  <BaseChart :option="option" @chart-click="handleChartClick" />
</template>
