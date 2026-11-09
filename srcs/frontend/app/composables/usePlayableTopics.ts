import type { PlayableTopic } from '~/types'

export function usePlayableTopics() {
  const { api } = useApi()
  const { locale } = useI18n()

  const topics = ref<PlayableTopic[]>([])
  const loading = ref(false)
  const failed = ref(false)

  async function load() {
    loading.value = true
    failed.value = false
    topics.value = []

    try {
      const data = await api<PlayableTopic[]>('/api/v1/matches/topics', {
        query: { locale: locale.value },
      })
      topics.value = data
    } catch {
      failed.value = true
      topics.value = []
    } finally {
      loading.value = false
    }
  }

  return { topics, loading, failed, load }
}
