import type { Difficulty } from '~/types'

type TagType = 'default' | 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'streak'

const MEDIUM_FROM = 1100
const HARD_FROM = 1300

export function difficultyOf(rating: string | number): Difficulty {
  const value = Number(rating)
  if (value >= HARD_FROM) return 'hard'
  if (value >= MEDIUM_FROM) return 'medium'
  return 'easy'
}

export const DIFFICULTY_TAG: Record<Difficulty, TagType> = {
  easy: 'success',
  medium: 'warning',
  hard: 'danger',
}
