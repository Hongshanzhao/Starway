<template>
  <div ref="chartEl" class="chart"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, watch, ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

const chartEl = ref(null)
let chart

function render() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const data = props.items.length ? props.items : [{ name: '暂无数据', score: 0 }]
  chart.setOption({
    color: ['#7F8FA3'],
    tooltip: {},
    radar: {
      indicator: data.map((item) => ({ name: item.name, max: 5 })),
      radius: '62%',
      splitArea: { areaStyle: { color: ['rgba(255,255,255,0.3)', 'rgba(165,181,178,0.12)'] } },
      axisName: { color: '#59616b' },
    },
    series: [
      {
        name: props.title,
        type: 'radar',
        areaStyle: { color: 'rgba(127,143,163,0.22)' },
        lineStyle: { width: 2 },
        data: [{ value: data.map((item) => Number(item.score || 0)), name: props.title || '能力' }],
      },
    ],
  })
}

onMounted(() => {
  render()
  window.addEventListener('resize', render)
})
watch(() => props.items, render, { deep: true })
onBeforeUnmount(() => {
  window.removeEventListener('resize', render)
  chart?.dispose()
})
</script>

<style scoped>
.chart {
  width: 100%;
  height: 320px;
}
</style>
