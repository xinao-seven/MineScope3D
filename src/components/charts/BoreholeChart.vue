<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { ChartDatum } from '../../types/dashboard'

const props = defineProps<{
  data: ChartDatum[]
}>()

const emit = defineEmits<{
  segmentClick: [name: string]
}>()

/** 构建钻孔分层类型占比图配置。 */
function buildChartOption(): EChartsOption {
  return {
    backgroundColor: 'transparent',
    color: ['#23d18b', '#56ccf2', '#f2c94c', '#f2994a', '#eb5757', '#bb6bd9'],
    tooltip: { trigger: 'item' },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      top: 'middle',
      right: 0,
      height: 132,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#c9e7ff', fontSize: 11 },
    },
    series: [
      {
        name: '分层类型',
        type: 'pie',
        radius: ['38%', '64%'],
        center: ['34%', '50%'],
        avoidLabelOverlap: true,
        label: { show: false },
        emphasis: {
          label: { show: true, color: '#f5fbff', formatter: '{b}' },
        },
        data: props.data,
      },
    ],
  }
}

/** 将图表点击事件透传给父组件。 */
function handleChartClick(name: string) {
  emit('segmentClick', name)
}

const option = computed(buildChartOption)
</script>

<template>
  <BaseChart :option="option" @chart-click="handleChartClick" />
</template>
