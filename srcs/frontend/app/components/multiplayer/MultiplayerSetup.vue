<script setup lang="ts">
const { disabled = false } = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  create: [payload: { size: number; topics: string[]; questionCount: number }]
  join: [code: string]
}>()

const SIZES = [2, 3, 4, 6, 8]
const size = ref(4)
const QUESTION_COUNTS = [3, 5, 7, 10]
const questionCount = ref(10)
const code = ref('')
const selected = ref<string[]>([])

const { topics, loading, failed, load } = usePlayableTopics()

const canJoin = computed(() => !disabled && code.value.trim().length > 0)

const groupedTopics = computed(() => {
  const groups: Array<{ slug: string; name: string; levels: typeof topics.value }> = []
  const byParent = new Map<string | null, typeof topics.value>()

  for (const topic of topics.value) {
    const key = topic.parent_slug
    if (!byParent.has(key)) {
      byParent.set(key, [])
    }
    byParent.get(key)!.push(topic)
  }

  for (const [parentSlug, topicsInGroup] of byParent) {
    if (parentSlug === null) {
      for (const topic of topicsInGroup) {
        groups.push({
          slug: topic.slug,
          name: topic.name,
          levels: [topic],
        })
      }
    } else {
      const parentName = topicsInGroup[0]?.parent_name ?? parentSlug
      groups.push({
        slug: parentSlug,
        name: parentName,
        levels: topicsInGroup,
      })
    }
  }

  return groups
})

const selectedCount = computed(() => {
  if (selected.value.length === 0) {
    return topics.value.reduce((sum, t) => sum + t.question_count, 0)
  }
  return topics.value
    .filter((t) => selected.value.includes(t.slug))
    .reduce((sum, t) => sum + t.question_count, 0)
})

function buildLevelLabel(level: { name: string; question_count: number }) {
  return `${level.name} · ${level.question_count}`
}

function toggleLevel(slug: string) {
  selected.value = selected.value.includes(slug)
    ? selected.value.filter((entry) => entry !== slug)
    : [...selected.value, slug]
}

function handleJoin() {
  if (canJoin.value) emit('join', code.value)
}

onMounted(() => load())
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="grid gap-5 md:grid-cols-2">
      <UiCard pad class="flex flex-col">
        <div class="mb-1 flex items-center gap-2 text-accent">
          <Icon name="lucide:circle-plus" mode="svg" size="1.25em" aria-hidden="true" />
          <h2 class="text-lg font-semibold text-fg-body">{{ $t('multiplayer.create.title') }}</h2>
        </div>
        <p class="mb-5 text-sm text-fg-muted">{{ $t('multiplayer.create.intro') }}</p>

        <fieldset class="mb-5">
          <legend class="mb-1.5 text-sm font-semibold">{{ $t('multiplayer.create.size') }}</legend>
          <div class="flex flex-wrap gap-2">
            <UiChip
              v-for="n in SIZES"
              :key="n"
              :label="$t('multiplayer.create.players', { n })"
              :active="size === n"
              @click="size = n"
            />
          </div>
        </fieldset>

        <fieldset class="mb-5">
          <legend class="mb-1.5 text-sm font-semibold">
            {{ $t('multiplayer.create.questionCount') }}
          </legend>
          <div class="flex flex-wrap gap-2">
            <UiChip
              v-for="n in QUESTION_COUNTS"
              :key="n"
              :label="$t('multiplayer.create.questions', { n })"
              :active="questionCount === n"
              @click="questionCount = n"
            />
          </div>
        </fieldset>

        <fieldset class="mb-5">
          <legend class="mb-1.5 text-sm font-semibold">
            {{ $t('multiplayer.create.levels') }}
          </legend>
          <p class="mb-3 text-sm text-fg-muted">{{ $t('multiplayer.create.levelsHint') }}</p>

          <div v-if="loading" class="text-sm text-fg-muted">
            {{ $t('multiplayer.create.levelsLoading') }}
          </div>

          <UiCallout v-else-if="failed" tone="hint" icon="lucide:triangle-alert">
            {{ $t('multiplayer.create.levelsFailed') }}
          </UiCallout>

          <div v-else class="flex flex-col gap-3">
            <div v-for="group in groupedTopics" :key="group.slug" class="flex flex-col gap-2">
              <h3 class="text-xs font-semibold text-fg-subtle">{{ group.name }}</h3>
              <div class="flex flex-wrap gap-2">
                <UiChip
                  v-for="level in group.levels"
                  :key="level.slug"
                  :label="buildLevelLabel(level)"
                  :active="selected.includes(level.slug)"
                  @click="toggleLevel(level.slug)"
                />
              </div>
            </div>

            <p class="text-sm text-fg-muted">
              {{ $t('multiplayer.create.selectedCount', { n: selectedCount }) }}
            </p>
          </div>
        </fieldset>

        <UiButton
          class="mt-auto self-start"
          :label="$t('multiplayer.create.submit')"
          :disabled="disabled"
          @click="emit('create', { size, topics: [...selected], questionCount })"
        >
          <Icon name="lucide:swords" mode="svg" size="1em" />
        </UiButton>
      </UiCard>

      <slot name="aside" />
    </div>

    <UiCard pad>
      <form class="flex flex-wrap items-center gap-3" @submit.prevent="handleJoin">
        <div class="w-full min-w-0 sm:w-auto sm:flex-1">
          <div class="mb-1 flex items-center gap-2 text-accent">
            <Icon name="lucide:log-in" mode="svg" size="1.25em" aria-hidden="true" />
            <h2 class="text-lg font-semibold text-fg-body">{{ $t('multiplayer.join.title') }}</h2>
          </div>
          <p class="text-sm text-fg-muted">{{ $t('multiplayer.join.intro') }}</p>
        </div>

        <label for="room-code" class="sr-only">{{ $t('multiplayer.join.code') }}</label>
        <div class="min-w-0 flex-1 sm:w-[10rem] sm:flex-none">
          <UiInput
            id="room-code"
            v-model="code"
            icon="lucide:hash"
            autocomplete="off"
            spellcheck="false"
            maxlength="12"
            class="uppercase"
            placeholder="ABC123"
          />
        </div>

        <UiButton
          type="submit"
          variant="secondary"
          :label="$t('multiplayer.join.submit')"
          :disabled="!canJoin"
        />
      </form>
    </UiCard>
  </div>
</template>
