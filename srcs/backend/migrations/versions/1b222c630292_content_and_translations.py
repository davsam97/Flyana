"""content and translations

Revision ID: 1b222c630292
Revises: d53216e55eef
Create Date: 2026-08-13 07:40:41.626644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '1b222c630292'
down_revision: Union[str, Sequence[str], None] = 'eee92670a8c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tags')),
    sa.UniqueConstraint('slug', name=op.f('uq_tags_slug'))
    )
    op.create_table('topics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('icon', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['topics.id'], name=op.f('fk_topics_parent_id_topics'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_topics')),
    sa.UniqueConstraint('slug', name=op.f('uq_topics_slug'))
    )
    op.create_table('learning_paths',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('level', sa.Enum('beginner', 'intermediate', 'advanced', name='path_level', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', 'rejected', name='path_status', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_learning_paths_author_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_paths')),
    sa.UniqueConstraint('slug', name=op.f('uq_learning_paths_slug'))
    )
    op.create_table('questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.Enum('single_choice', 'multi_choice', 'free_text', name='question_kind', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('difficulty_rating', sa.Numeric(precision=7, scale=2), server_default='1200', nullable=False),
    sa.Column('status', sa.Enum('draft', 'in_review', 'published', 'archived', 'rejected', name='question_status', native_enum=False, create_constraint=True, length=32), server_default='draft', nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('times_asked', sa.Integer(), server_default='0', nullable=False),
    sa.Column('times_correct', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_questions_author_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_questions_reviewed_by_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_questions_topic_id_topics'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_questions'))
    )
    op.create_index('ix_questions_status_topic_difficulty', 'questions', ['status', 'topic_id', 'difficulty_rating'], unique=False)
    op.create_table('topic_translations',
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_topic_translations_topic_id_topics'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('topic_id', 'locale', name=op.f('pk_topic_translations'))
    )
    op.create_table('choices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_choices_question_id_questions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_choices'))
    )
    op.create_table('learning_path_translations',
    sa.Column('path_id', sa.Integer(), nullable=False),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['path_id'], ['learning_paths.id'], name=op.f('fk_learning_path_translations_path_id_learning_paths'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('path_id', 'locale', name=op.f('pk_learning_path_translations'))
    )
    op.create_table('path_modules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('path_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('min_questions', sa.Integer(), server_default='5', nullable=False),
    sa.ForeignKeyConstraint(['path_id'], ['learning_paths.id'], name=op.f('fk_path_modules_path_id_learning_paths'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_path_modules_topic_id_topics'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_path_modules'))
    )
    op.create_table('question_tags',
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_question_tags_question_id_questions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_question_tags_tag_id_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('question_id', 'tag_id', name=op.f('pk_question_tags'))
    )
    op.create_table('question_translations',
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('stem', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('search_vector', postgresql.TSVECTOR(), sa.Computed("to_tsvector('simple', coalesce(stem, ''))", persisted=True), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_question_translations_question_id_questions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('question_id', 'locale', name=op.f('pk_question_translations'))
    )
    op.create_index('ix_qt_search', 'question_translations', ['search_vector'], unique=False, postgresql_using='gin')
    op.create_index('ix_qt_stem_trgm', 'question_translations', ['stem'], unique=False, postgresql_using='gin', postgresql_ops={'stem': 'gin_trgm_ops'})
    op.create_table('choice_translations',
    sa.Column('choice_id', sa.Integer(), nullable=False),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['choice_id'], ['choices.id'], name=op.f('fk_choice_translations_choice_id_choices'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('choice_id', 'locale', name=op.f('pk_choice_translations'))
    )


def downgrade() -> None:
    op.drop_table('choice_translations')
    op.drop_index('ix_qt_stem_trgm', table_name='question_translations', postgresql_using='gin', postgresql_ops={'stem': 'gin_trgm_ops'})
    op.drop_index('ix_qt_search', table_name='question_translations', postgresql_using='gin')
    op.drop_table('question_translations')
    op.drop_table('question_tags')
    op.drop_table('path_modules')
    op.drop_table('learning_path_translations')
    op.drop_table('choices')
    op.drop_table('topic_translations')
    op.drop_index('ix_questions_status_topic_difficulty', table_name='questions')
    op.drop_table('questions')
    op.drop_table('learning_paths')
    op.drop_table('topics')
    op.drop_table('tags')
