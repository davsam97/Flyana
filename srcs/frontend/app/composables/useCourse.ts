import type { LearningPath, Lesson, ModuleDetail, QuizAnswer, QuizRun } from '~/types'

/* The course API: the path, its modules and lessons, and the check quiz.
 * Every read asks for the interface language, the server falls back to
 * English for anything missing */
export function useCourse() {
  const { api } = useApi()
  const { locale } = useI18n()
  const query = () => ({ locale: locale.value })

  return {
    path: () => api<LearningPath>(`/api/v1/paths/${COURSE_PATH}`, { query: query() }),
    module: (slug: string) => api<ModuleDetail>(`/api/v1/modules/${slug}`, { query: query() }),
    lesson: (slug: string) => api<Lesson>(`/api/v1/lessons/${slug}`, { query: query() }),
    markRead: (slug: string) =>
      api<{ achievements: string[] }>(`/api/v1/lessons/${slug}/read`, { method: 'POST' }),
    startQuiz: (slug: string) =>
      api<QuizRun>(`/api/v1/modules/${slug}/quiz`, { method: 'POST', query: query() }),
    run: (id: number) => api<QuizRun>(`/api/v1/quiz-runs/${id}`, { query: query() }),
    answer: (id: number, body: { question_id: number; choice_ids?: number[]; value?: string }) =>
      api<QuizAnswer>(`/api/v1/quiz-runs/${id}/answer`, {
        method: 'POST',
        body,
        query: query(),
      }),
  }
}
