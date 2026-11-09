export type Difficulty = 'easy' | 'medium' | 'hard'

export type QuestionKind = 'single_choice' | 'multi_choice' | 'free_text' | 'numeric'

export interface PlayableTopic {
  slug: string
  name: string
  description: string | null
  parent_slug: string | null
  parent_name: string | null
  question_count: number
}

export interface UserSummary {
  id: number
  display_name: string
  avatar_path: string | null
}

export type FriendshipView = 'none' | 'pending_in' | 'pending_out' | 'friends' | 'blocked'

export interface Profile extends UserSummary {
  bio: string | null
  role: string
  created_at: string
  online: boolean
  friendship: FriendshipView
  friendship_id: number | null
}

export interface Friend {
  friendship_id: number
  user: UserSummary
  online: boolean
  last_seen_at: string | null
}

export interface PendingRequest {
  friendship_id: number
  user: UserSummary
  created_at: string
}

export interface DirectMessage {
  id: number
  sender_id: number
  recipient_id: number
  body: string
  created_at: string
  read_at: string | null
}

export interface Conversation {
  user: UserSummary
  last_message: DirectMessage
  unread: number
}

export interface MatchSummaryChoice {
  id: number
  text: string
  correct: boolean
}

export interface MatchSummaryAttempt {
  user_id: number
  choice_id: number | null
  is_correct: boolean
  response_ms: number | null
  score: number
}

export interface MatchSummaryQuestion {
  position: number
  question_id: number
  slug: string
  stem: string
  is_fallback: boolean
  choices: MatchSummaryChoice[]
  attempts: MatchSummaryAttempt[]
}

export interface MatchSummaryPlayer {
  user_id: number
  display_name: string
  avatar_path: string | null
  score: number
  final_rank: number | null
}

export interface MatchSummary {
  public_id: string
  mode: string
  question_count: number
  started_at: string | null
  finished_at: string | null
  players: MatchSummaryPlayer[]
  questions: MatchSummaryQuestion[]
}

export interface LeaderboardEntry extends UserSummary {
  rank: number
  xp: number
  level: number
}

export interface Leaderboard {
  entries: LeaderboardEntry[]
  me: LeaderboardEntry | null
}

/* The course: path, modules, lessons and the adaptive check quiz. Decimals
 * arrive as strings, as FastAPI serialises them */

export interface ModuleSummary {
  slug: string
  name: string
  description: string | null
  position: number
  lessons_total: number
  lessons_read: number
  quiz_questions: number
  best_score: string | null
  quizzes: number
  passed: boolean
  rating: string | null
}

export interface LearningPath {
  slug: string
  title: string
  description: string | null
  pass_ratio: string
  modules: ModuleSummary[]
}

export interface LessonSummary {
  slug: string
  title: string
  position: number
  read: boolean
}

export interface ModuleDetail extends ModuleSummary {
  lessons: LessonSummary[]
  open_run_id: number | null
}

export interface Lesson {
  slug: string
  title: string
  body: string
  module_slug: string
  module_name: string
  position: number
  previous_slug: string | null
  next_slug: string | null
  read: boolean
}

export interface QuizChoice {
  id: number
  text: string
}

export interface QuizQuestion {
  id: number
  kind: QuestionKind
  title: string | null
  stem: string | null
  unit: string | null
  difficulty_rating: string
  choices: QuizChoice[]
}

export interface Correction {
  correct_choice_ids: number[]
  expected_value: string | null
  tolerance_rel: string | null
  unit: string | null
  explanation: string | null
  source: { label: string; url: string | null } | null
}

export interface RunResult {
  correct: number
  total: number
  passed: boolean
  pass_ratio: string
}

export interface QuizRun {
  id: number
  module_slug: string
  total: number
  answered: number
  correct: number
  question: QuizQuestion | null
  result: RunResult | null
}

export interface QuizAnswer {
  correct: boolean
  correction: Correction
  xp: number
  achievements: string[]
  rating: string
  answered: number
  total: number
  next_question: QuizQuestion | null
  result: RunResult | null
}
