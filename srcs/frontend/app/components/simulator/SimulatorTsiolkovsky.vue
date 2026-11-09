<script setup lang="ts">
/* Delta-v calculator: pick an engine and the masses, read the delta-v the
 * stage gives against what low orbit needs */
const LEO_DELTA_V = 9_400 // m/s, losses included (see module 3)

const PRESETS = [
  { key: 'solid', isp: 270 },
  { key: 'kerosene', isp: 330 },
  { key: 'hydrogen', isp: 450 },
  { key: 'ion', isp: 3000 },
] as const

const isp = ref(330)
const propellant = ref(300) // t
const dry = ref(40) // t, structure, engines and payload

const initial = computed(() => propellant.value + dry.value)
const ratio = computed(() => initial.value / dry.value)
const deltaV = computed(() => tsiolkovsky(isp.value, initial.value, dry.value))
const share = computed(() => Math.min(100, (deltaV.value / LEO_DELTA_V) * 100))

const { locale } = useI18n()
const format = (value: number, digits = 1) =>
  value.toLocaleString(locale.value, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })

const SLIDER = 'w-full accent-(--accent)'
</script>

<template>
  <UiCard pad class="my-6 flex flex-col gap-4 text-sm">
    <div class="flex items-center gap-2">
      <Icon name="lucide:rocket" mode="svg" aria-hidden="true" class="text-accent" />
      <h3 class="mt-0 font-semibold">{{ $t('simulator.tsiolkovsky.title') }}</h3>
    </div>

    <div class="flex flex-wrap gap-2" role="group" :aria-label="$t('simulator.tsiolkovsky.engine')">
      <UiChip
        v-for="preset in PRESETS"
        :key="preset.key"
        :label="`${$t(`simulator.tsiolkovsky.presets.${preset.key}`)} · ${preset.isp} s`"
        :active="isp === preset.isp"
        @click="isp = preset.isp"
      />
    </div>

    <label class="flex flex-col gap-1">
      <span>{{ $t('simulator.tsiolkovsky.isp', { n: isp }) }}</span>
      <input v-model.number="isp" type="range" min="200" max="3000" step="10" :class="SLIDER" />
    </label>
    <label class="flex flex-col gap-1">
      <span>{{ $t('simulator.tsiolkovsky.propellant', { n: propellant }) }}</span>
      <input v-model.number="propellant" type="range" min="0" max="800" step="5" :class="SLIDER" />
    </label>
    <label class="flex flex-col gap-1">
      <span>{{ $t('simulator.tsiolkovsky.dry', { n: dry }) }}</span>
      <input v-model.number="dry" type="range" min="5" max="200" step="1" :class="SLIDER" />
    </label>

    <div class="flex flex-col gap-2 rounded-md bg-surface-raised p-4" aria-live="polite">
      <p class="font-mono">
        {{ $t('simulator.tsiolkovsky.ratio', { n: format(ratio, 2) }) }} ·
        {{ $t('simulator.tsiolkovsky.result', { v: format(deltaV / 1000, 2) }) }}
      </p>
      <UiProgress :value="share" :tone="share >= 100 ? 'success' : 'accent'" />
      <p class="text-xs text-fg-muted">
        {{
          share >= 100
            ? $t('simulator.tsiolkovsky.enough')
            : $t('simulator.tsiolkovsky.notEnough', { n: Math.round(share) })
        }}
      </p>
    </div>
  </UiCard>
</template>
