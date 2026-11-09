"""learning progress: adaptive ratings, check quizzes, module results, lessons read

Revision ID: c4f8b1e6d2a7
Revises: b7d2e5a9c1f3
Create Date: 2026-11-09 08:35:37.248624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4f8b1e6d2a7'
down_revision: Union[str, Sequence[str], None] = 'b7d2e5a9c1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('module_progress',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('best_score', sa.Numeric(precision=4, scale=3), server_default='0', nullable=False),
    sa.Column('quizzes', sa.Integer(), server_default='0', nullable=False),
    sa.Column('passed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_module_progress_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_module_progress_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'topic_id', name=op.f('pk_module_progress'))
    )
    op.create_table('user_topic_ratings',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Numeric(precision=7, scale=2), server_default='1000', nullable=False),
    sa.Column('answers', sa.Integer(), server_default='0', nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_user_topic_ratings_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_topic_ratings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'topic_id', name=op.f('pk_user_topic_ratings'))
    )
    op.create_table('lesson_reads',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('read_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_lesson_reads_lesson_id_lessons'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_lesson_reads_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'lesson_id', name=op.f('pk_lesson_reads'))
    )
    op.create_table('quiz_runs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('question_count', sa.Integer(), nullable=False),
    sa.Column('served_ids', postgresql.ARRAY(sa.Integer()), server_default='{}', nullable=False),
    sa.Column('current_question_id', sa.Integer(), nullable=True),
    sa.Column('answered', sa.Integer(), server_default='0', nullable=False),
    sa.Column('correct', sa.Integer(), server_default='0', nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['current_question_id'], ['questions.id'], name=op.f('fk_quiz_runs_current_question_id_questions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_quiz_runs_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_quiz_runs_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_runs'))
    )
    op.create_index('ix_quiz_runs_user_topic', 'quiz_runs', ['user_id', 'topic_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_quiz_runs_user_topic', table_name='quiz_runs')
    op.drop_table('quiz_runs')
    op.drop_table('lesson_reads')
    op.drop_table('user_topic_ratings')
    op.drop_table('module_progress')
