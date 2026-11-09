import type { MatchSummary } from '~/types'

export function useMatchSummary() {
  const { api } = useApi()
  const { locale } = useI18n()

  const summary = ref<MatchSummary | null>(null)
  const loading = ref(false)
  const failed = ref(false)

  async function load(publicId: string) {
    loading.value = true
    failed.value = false
    summary.value = null

    try {
      const data = await api<MatchSummary>(`/api/v1/matches/${publicId}`, {
        query: { locale: locale.value },
      })
      summary.value = data
    } catch {
      failed.value = true
      summary.value = null
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, failed, load }
}
