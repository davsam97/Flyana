"""Models registry

`migrations/env.py` imports this: any model absent from here is invisible to
alembic, which will then suggest dropping its table.
"""

from app.models.attempt import Attempt
from app.models.backup_code import BackupCode
from app.models.base import Base, TimestampMixin
from app.models.content import (
    Choice,
    ChoiceTranslation,
    LearningPath,
    LearningPathTranslation,
    Lesson,
    LessonTranslation,
    PathModule,
    Question,
    QuestionTag,
    QuestionTranslation,
    Tag,
    Topic,
    TopicTranslation,
)
from app.models.friendship import Friendship
from app.models.learning import LessonRead, ModuleProgress, QuizRun, UserTopicRating
from app.models.message import DirectMessage
from app.models.match import Match, MatchAttempt, MatchPlayer, MatchQuestion
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.models.gamification import Achievement, UserAchievement

__all__ = [
	"Achievement",
    "Attempt",
    "BackupCode",
    "Base",
    "Choice",
    "ChoiceTranslation",
    "DirectMessage",
    "Friendship",
    "LearningPath",
    "LearningPathTranslation",
    "Lesson",
    "LessonRead",
    "LessonTranslation",
    "ModuleProgress",
    "Match",
    "MatchAttempt",
    "MatchPlayer",
    "MatchQuestion",
    "PathModule",
    "Question",
    "QuestionTag",
    "QuestionTranslation",
    "QuizRun",
    "RefreshToken",
    "Tag",
    "TimestampMixin",
    "Topic",
    "TopicTranslation",
    "User",
    "UserAchievement",
    "UserTopicRating",
    "OAuthAccount"
]
