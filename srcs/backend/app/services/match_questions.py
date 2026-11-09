"""Load published questions for realtime matches."""

from __future__ import annotations

from collections import defaultdict
from random import shuffle
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import (
    Choice,
    ChoiceTranslation,
    Question,
    QuestionTranslation,
    Topic,
)
from app.models.enums import QuestionKind, QuestionStatus


def playable_questions():
    """The pool the duel draws from, as a reusable filter

    Playable means "has choices", not "is a choice question": the written
    questions of the exam content carry choices for the duel while the model
    keeps grading their written answers. A round scores one choice, so
    questions with several right ones are left out, and numeric ones have
    no choices at all. A retired topic takes its questions out of the pool
    """
    return (
        Question.status == QuestionStatus.published,
        Question.kind.not_in((QuestionKind.multi_choice, QuestionKind.numeric)),
        Question.id.in_(select(Choice.question_id)),
        Question.topic_id.in_(select(Topic.id).where(Topic.archived.is_(False))),
    )


async def load_published_questions(
    db: AsyncSession,
    locale: str,
    limit: int = 10,
    topics: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return playable questions without exposing the correct answer.

    `topics` narrows the draw to those topic slugs; empty draws from everything.
    """
    def question_query_for(translation_locale: str):
        query = (
            select(Question, QuestionTranslation)
            .join(
                QuestionTranslation,
                QuestionTranslation.question_id == Question.id,
            )
            .where(
                *playable_questions(),
                QuestionTranslation.locale == translation_locale,
            )
        )
        if topics:
            query = query.where(
                Question.topic_id.in_(select(Topic.id).where(Topic.slug.in_(topics)))
            )
        return query.order_by(func.random()).limit(limit)

    selected_questions = (await db.execute(question_query_for(locale))).all()
    if not selected_questions and locale != "en":
        selected_questions = (await db.execute(question_query_for("en"))).all()
    if not selected_questions:
        return []

    question_ids = [question.id for question, _ in selected_questions]
    def choice_query_for(translation_locale: str):
        return (
            select(Choice, ChoiceTranslation)
            .join(
                ChoiceTranslation,
                ChoiceTranslation.choice_id == Choice.id,
            )
            .where(
                Choice.question_id.in_(question_ids),
                ChoiceTranslation.locale == translation_locale,
            )
            .order_by(Choice.question_id, Choice.position)
        )

    choice_rows = (await db.execute(choice_query_for(locale))).all()
    if not choice_rows and locale != "en":
        choice_rows = (await db.execute(choice_query_for("en"))).all()

    choices_by_question: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    correct_by_question: dict[int, int] = {}
    for choice, translation in choice_rows:
        choices_by_question[choice.question_id].append(
            {"id": choice.id, "text": translation.text}
        )
        if choice.is_correct:
            correct_by_question[choice.question_id] = choice.id

    questions: list[dict[str, Any]] = []
    for question, translation in selected_questions:
        choices = choices_by_question[question.id]
        correct_choice_id = correct_by_question.get(question.id)
        if len(choices) < 2 or correct_choice_id is None:
            continue

        shuffle(choices)

        questions.append(
            {
                "id": question.id,
                "text": translation.stem,
                "choices": choices,
                "correct_choice_id": correct_choice_id,
            }
        )

    return questions
