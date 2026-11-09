<script setup lang="ts">
defineOptions({ inheritAttrs: false })

const model = defineModel<string>()

const BASE =
  'h-7 w-full cursor-pointer appearance-none rounded-md border border-line-strong bg-surface-raised pr-8.5 pl-3 font-sans text-sm text-fg-body transition-[border-color,box-shadow] duration-fast focus-visible:border-accent-2 focus-visible:shadow-focus focus-visible:outline-none'
</script>

<template>
  <div class="relative w-full">
    <select v-model="model" :class="BASE" v-bind="$attrs">
      <slot />
    </select>
    <Icon
      name="lucide:chevron-down"
      mode="svg"
      size="1em"
      aria-hidden="true"
      class="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-fg-subtle"
    />
  </div>
</template>
