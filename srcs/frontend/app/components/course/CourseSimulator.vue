<script setup lang="ts">
/* An interactive piece placed in a lesson by a ```simulator name``` block.
 * An unknown name renders nothing: a typo in a lesson must not break it */
const { name } = defineProps<{ name: string }>()
</script>

<template>
  <SimulatorTsiolkovsky v-if="name === 'tsiolkovsky'" />
  <SimulatorHohmann v-else-if="name === 'hohmann'" />
</template>
