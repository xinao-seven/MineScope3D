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

<style scoped>
.borehole-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  max-height: 178px;
  overflow: auto;
  padding-right: 4px;
}

.borehole-list__item {
  width: 100%;
  border: 1px solid rgba(125, 211, 252, 0.18);
  border-radius: 8px;
  background: rgba(5, 18, 42, 0.46);
  padding: 8px 10px;
  text-align: left;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
  color: var(--text);
}

.borehole-list__item span {
  color: var(--green);
  font-size: 12px;
}

.borehole-list__item strong {
  display: block;
  color: #f5fbff;
}

.borehole-list__item small {
  display: block;
  margin-top: 4px;
  color: var(--muted);
}

.borehole-list__item:hover,
.borehole-list__item.is-active {
  border-color: var(--green);
  background: rgba(37, 99, 235, 0.22);
}
</style>
