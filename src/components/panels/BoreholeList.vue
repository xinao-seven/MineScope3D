<script setup lang="ts">
import type { Borehole } from '../../types/dashboard'

defineProps<{
  boreholes: Borehole[]
  selectedId?: string
}>()

const emit = defineEmits<{
  locateBorehole: [id: string]
}>()

/** 通知地图飞行到钻孔点位。 */
function handleLocate(id: string) {
  emit('locateBorehole', id)
}
</script>

<template>
  <div class="borehole-list">
    <button
      v-for="borehole in boreholes"
      :key="borehole.id"
      type="button"
      class="borehole-list__item"
      :class="{ 'is-active': selectedId === borehole.id }"
      @click="handleLocate(borehole.id)"
    >
      <span>{{ borehole.borehole_code }}</span>
      <strong>{{ borehole.name }}</strong>
      <small>{{ borehole.workface_name }} · {{ borehole.depth_total }}m</small>
    </button>
  </div>
</template>
