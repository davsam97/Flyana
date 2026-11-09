"""Rules Pydantic cannot express:
constrain relations between rows,not the shape of a single field
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException


from app.models.content import (
    Question, ChoiceTranslation, Choice, QuestionTranslation,
    QuestionKind
)


async def assert_publishable(db: AsyncSession, question: Question) -> None:
    """Raises unless this question is complete enough to publish"""
    choices = list(await db.scalars(
        select(Choice).where(Choice.question_id == question.id)
    ))
    # Choices are required of a choice question and optional on a written one,
    # but once they are there the same counts apply: the duel has to have one
    # answer to score, and a single proposal is not a question. A numeric
    # question is answered with a number, never with choices
    if question.kind == QuestionKind.numeric:
        if choices:
            raise HTTPException(422, detail="a numeric question has no choices")
        if question.numeric_answer is None or question.tolerance_rel is None:
            raise HTTPException(422, detail="a numeric question needs an answer and a tolerance")
    elif choices or question.kind != QuestionKind.free_text:
        if len(choices) < 2:
            raise HTTPException(422, detail="at least 2 choices required")

        correct = sum(1 for c in choices if c.is_correct)
        if question.kind == QuestionKind.multi_choice:
            if correct < 1:
                raise HTTPException(422, detail="at least 1 correct answer expected")
        elif correct != 1:
            raise HTTPException(422, detail="exactly 1 correct answer expected")

    # `en` is the fallback: without it the question is invisible in any untranslated language
    en = await db.scalar(
        select(QuestionTranslation).where(
            QuestionTranslation.question_id == question.id,
            QuestionTranslation.locale == "en",
        )
    )
    if en is None or not en.stem.strip():
        raise HTTPException(422, detail="incomplete `en` translation")

    if question.kind == QuestionKind.free_text and not any(
        point.strip() for point in question.key_points
    ):
        raise HTTPException(422, detail="a free_text question needs key points")

    for choice in choices:
        t = await db.scalar(
            select(ChoiceTranslation).where(
                ChoiceTranslation.choice_id == choice.id,
                ChoiceTranslation.locale == "en",
            )
        )
        if t is None or not t.text.strip():
            raise HTTPException(422, detail=f"choice {choice.position} has no `en` text")
