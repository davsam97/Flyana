<script setup lang="ts">
/* A launch at dawn from the Guianese coast: rainforest in the foreground,
 * the Atlantic to the east, a launcher climbing from its pad. An
 * illustration with its own colours, the same in both themes. Purely
 * decorative unless given a label */
const { label } = defineProps<{ label?: string }>()

// A few stars, placed by hand so the sky looks the same on every render
const STARS = [
  [80, 40, 1.4],
  [190, 90, 1],
  [300, 30, 1.2],
  [420, 70, 0.9],
  [540, 25, 1.3],
  [980, 35, 1.1],
  [1080, 80, 1.4],
  [1150, 30, 0.9],
  [640, 95, 0.8],
  [880, 60, 1],
] as const
</script>

<template>
  <svg
    viewBox="0 0 1200 420"
    preserveAspectRatio="xMidYMax slice"
    xmlns="http://www.w3.org/2000/svg"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
    class="block h-full w-full"
  >
    <defs>
      <linearGradient id="guiana-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#041010" />
        <stop offset="0.45" stop-color="#16243a" />
        <stop offset="0.75" stop-color="#5c4a7b" />
        <stop offset="1" stop-color="#c16d45" />
      </linearGradient>
      <linearGradient id="guiana-sea" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#1f5a6a" />
        <stop offset="1" stop-color="#003a46" />
      </linearGradient>
      <linearGradient id="guiana-plume" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0" stop-color="#f4fbf9" stop-opacity="0.85" />
        <stop offset="1" stop-color="#f4fbf9" stop-opacity="0" />
      </linearGradient>
      <radialGradient id="guiana-glow" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0" stop-color="#ffd27a" stop-opacity="0.9" />
        <stop offset="1" stop-color="#f68c36" stop-opacity="0" />
      </radialGradient>
    </defs>

    <!-- Sky at dawn -->
    <rect width="1200" height="420" fill="url(#guiana-sky)" />
    <circle
      v-for="([x, y, r], index) in STARS"
      :key="index"
      :cx="x"
      :cy="y"
      :r="r"
      fill="#f4fbf9"
      opacity="0.8"
    />

    <!-- The Atlantic, to the east -->
    <rect x="0" y="318" width="1200" height="102" fill="url(#guiana-sea)" />
    <path d="M0 318H1200" stroke="#f0a070" stroke-opacity="0.5" stroke-width="1.5" />

    <!-- Exhaust plume, curving east over the ocean -->
    <path
      d="M772 296C774 272 788 250 822 234"
      fill="none"
      stroke="url(#guiana-plume)"
      stroke-width="22"
      stroke-linecap="round"
    />

    <!-- The launcher: core stage and two boosters, tilted east -->
    <g transform="translate(846 202) rotate(38)">
      <circle class="guiana-flame" cx="0" cy="40" r="22" fill="url(#guiana-glow)" />
      <path
        fill="#f4fbf9"
        d="M0-34c5 4.5 6.5 9.5 6.5 14.5V26h-13V-19.5C-6.5-24.5-5-29.5 0-34ZM-13.5-14.5c2.8 2.6 4 4.9 4 7.8V26h-8V-6.7c0-2.9 1.2-5.2 4-7.8Zm27 0c2.8 2.6 4 4.9 4 7.8V26h-8V-6.7c0-2.9 1.2-5.2 4-7.8Z"
      />
      <path
        class="guiana-flame"
        fill="#f68c36"
        d="M-5 27h10L0 44ZM-17 27h7l-3.5 10Zm20 0h7l-3.5 10Z"
      />
    </g>

    <!-- The coast the pad stands on -->
    <path fill="#06301f" d="M640 318c20-12 52-18 86-18h112c34 0 58 8 74 18Z" />

    <!-- Launch pad and its lightning masts on the coast -->
    <g fill="#0b2a2a" stroke="#0b2a2a">
      <path d="M736 318V262h6v56M792 318V256h6v56" stroke-width="0" />
      <path d="M739 262l26-18 26 12" fill="none" stroke-width="2" />
      <rect x="752" y="300" width="36" height="18" />
    </g>

    <!-- Rainforest canopy, two layers -->
    <path
      fill="#003821"
      d="M0 300c30-26 62-30 92-12 18-30 58-36 84-10 22-22 60-24 82 2 26-20 64-16 80 10 16-14 44-16 60 0 26-22 70-20 92 4 18-12 40-12 56 2 16 6 30 18 44 36V420H0Z"
    />
    <path
      fill="#002215"
      d="M0 352c26-20 58-22 80-4 20-24 58-26 80-4 24-18 56-18 76 2 22-20 62-22 84 2 20-14 48-14 66 4 24-16 58-14 76 6 20-12 42-10 58 6 10-6 22-8 32-4 14 8 24 20 30 38V420H0Z"
    />
    <path fill="#002215" d="M1200 360c-22-14-48-14-66 2-20-16-52-16-70 2-14-8-30-8-42 0V420h178Z" />

    <!-- Palm trees on the shore -->
    <g fill="#00160d" stroke="#00160d" stroke-linecap="round">
      <path d="M948 362c2-24 6-44 14-60" fill="none" stroke-width="4" />
      <path
        d="M962 302c-14-6-30-4-40 6 12-2 26 0 40-6Zm0 0c14-8 30-8 40 0-12 0-26 2-40 0Zm0 0c-6-12-18-18-30-18 10 6 20 12 30 18Zm0 0c4-12 14-20 28-22-10 6-20 14-28 22Z"
        stroke-width="1"
      />
      <path d="M1082 366c-2-20-6-36-14-50" fill="none" stroke-width="4" />
      <path
        d="M1068 316c-12-6-26-6-36 2 12-2 24 0 36-2Zm0 0c12-8 28-8 38 0-12-2-26 0-38 0Zm0 0c-4-12-14-18-26-20 8 6 18 12 26 20Z"
        stroke-width="1"
      />
    </g>
  </svg>
</template>

<style scoped>
@media (prefers-reduced-motion: no-preference) {
  .guiana-flame {
    animation: guiana-flicker 0.18s ease-in-out infinite alternate;
    transform-box: fill-box;
    transform-origin: 50% 0;
  }
}

@keyframes guiana-flicker {
  from {
    transform: scaleY(0.88);
    opacity: 0.85;
  }
  to {
    transform: scaleY(1.08);
    opacity: 1;
  }
}
</style>
