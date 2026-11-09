export interface UserPublic {
  id: number
  email: string
  display_name: string
  avatar_path: string | null
  bio: string | null
  locale: string
  role: string
  totp_enabled: boolean
  created_at: string
  xp: number
  level: number
  xp_max: number
  level_xp: number
  streak: number
  has_password: boolean
}

export interface UserUpdate {
  display_name?: string | null
  bio?: string | null
  locale?: 'en' | 'fr'
}

export interface UserCreate {
  email: string
  password: string
  display_name: string
}

export interface Friend {
  friendship_id: number
  user_id: number
  display_name: string
  avatar_path: string | null
  online: boolean
  last_seen_at: string | null
}

export interface FriendRequest {
  friendship_id: number
  user_id: number
  display_name: string
  avatar_path: string | null
  direction: 'incoming' | 'outgoing'
}

export interface UserSearchResult {
  id: number
  display_name: string
  avatar_path: string | null
}

export interface AchievementOut {
  code: string
  icon: string | null
  earned_at: string | null
}

export interface GamificationRules {
  xp_per_level: number
  xp: {
    correct_llm: number
    correct_self: number
    match_played: number
    match_won: number
    quiz_correct: number
    module_passed: number
  }
}

export interface UserStats {
  solved: number
  to_review: number
}
