<script setup lang="ts">
/* Hohmann transfer between two circular orbits, drawn to scale */
const low = ref(400) // km
const high = ref(35_786) // km

const r1 = computed(() => R_EARTH + low.value * 1000)
const r2 = computed(() => R_EARTH + Math.max(high.value, low.value) * 1000)
const transfer = computed(() => hohmann(r1.value, r2.value))

// Drawing: the outer orbit fills the box, the Earth sits at the focus
const SIZE = 300
const scale = computed(() => (SIZE / 2 - 16) / r2.value)
const px = (metres: number) => metres * scale.value
const earth = computed(() => px(R_EARTH))
// Upper half of the transfer ellipse, from perigee (right) to apogee (left)
const arc = computed(() => {
  const a = px(transfer.value.semiMajorAxis)
  const b = px(Math.sqrt(r1.value * r2.value))
  return `M ${px(r1.value)} 0 A ${a} ${b} 0 0 0 ${-px(r2.value)} 0`
})

const { locale } = useI18n()
const format = (value: number, digits = 2) =>
  value.toLocaleString(locale.value, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })

const SLIDER = 'w-full accent-(--accent)'
</script>

<template>
  <UiCard pad class="my-6 flex flex-col gap-4 text-sm">
    <div class="flex items-center gap-2">
      <Icon name="lucide:orbit" mode="svg" aria-hidden="true" class="text-accent" />
      <h3 class="mt-0 font-semibold">{{ $t('simulator.hohmann.title') }}</h3>
    </div>

    <div class="grid items-center gap-5 sm:grid-cols-[minmax(0,300px)_1fr]">
      <svg
        :viewBox="`${-SIZE / 2} ${-SIZE / 2} ${SIZE} ${SIZE}`"
        class="mx-auto w-full max-w-75"
        role="img"
        :aria-label="$t('simulator.hohmann.figure', { low, high: Math.max(high, low) })"
      >
        <circle :r="px(r2)" fill="none" class="stroke-line-strong" stroke-width="1.5" />
        <circle :r="px(r1)" fill="none" class="stroke-accent-2" stroke-width="1.5" />
        <path
          :d="arc"
          fill="none"
          class="stroke-accent-3"
          stroke-width="2"
          stroke-dasharray="6 4"
        />
        <circle :r="Math.max(earth, 3)" class="fill-accent" opacity="0.8" />
        <circle :cx="px(r1)" r="4" class="fill-accent-3" />
        <circle :cx="-px(r2)" r="4" class="fill-accent-3" />
      </svg>

      <div class="flex flex-col gap-4">
        <label class="flex flex-col gap-1">
          <span>{{ $t('simulator.hohmann.low', { n: low.toLocaleString(locale) }) }}</span>
          <input v-model.number="low" type="range" min="200" max="2000" step="50" :class="SLIDER" />
        </label>
        <label class="flex flex-col gap-1">
          <span>{{ $t('simulator.hohmann.high', { n: high.toLocaleString(locale) }) }}</span>
          <input
            v-model.number="high"
            type="range"
            min="2000"
            max="40000"
            step="100"
            :class="SLIDER"
          />
        </label>
        <dl
          class="grid grid-cols-2 gap-x-4 gap-y-1 rounded-md bg-surface-raised p-4 font-mono"
          aria-live="polite"
        >
          <dt class="text-fg-muted">Δv₁</dt>
          <dd>{{ format(transfer.firstBurn / 1000) }} km/s</dd>
          <dt class="text-fg-muted">Δv₂</dt>
          <dd>{{ format(transfer.secondBurn / 1000) }} km/s</dd>
          <dt class="text-fg-muted">{{ $t('simulator.hohmann.total') }}</dt>
          <dd class="font-semibold">{{ format(transfer.total / 1000) }} km/s</dd>
          <dt class="text-fg-muted">{{ $t('simulator.hohmann.duration') }}</dt>
          <dd>{{ format(transfer.duration / 3600, 1) }} h</dd>
        </dl>
      </div>
    </div>
    <p class="text-xs text-fg-subtle">{{ $t('simulator.hohmann.legend') }}</p>
  </UiCard>
</template>
