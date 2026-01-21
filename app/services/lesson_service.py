"""Lesson service orchestration and telemetry logging."""

import logging
from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import uuid4

from pydantic import ValidationError

from app.core import config
from app.models.api import LessonRequest, LessonResponse, LessonSection
from app.models.db import LessonRun, LessonFailure
from app.services.mongo import insert_lesson_run, insert_lesson_failure
from app.services.static_lessons import build_static_lesson
from app.services.markdown_renderer import render_blocks_to_markdown
from app.agents.planner import PlannerAgent
from app.agents.content import ContentAgent
from app.agents.content_llm import ContentAgentLLM
from app.agents.validator import ValidatorAgent

logger = logging.getLogger(__name__)

# ---------------------------
# Agent instantiation
# ---------------------------
planner_agent = PlannerAgent()
content_agent = (
    ContentAgentLLM() if config.USE_LLM_CONTENT else ContentAgent()
)
validator_agent = ValidatorAgent()


async def generate_lesson(request: LessonRequest) -> LessonResponse:
    """Generate a lesson and record telemetry (best-effort)."""

    session_id = str(request.session_id) if request.session_id else str(uuid4())

    def _summarize_schema_errors(errors: Sequence[Mapping[str, object]]) -> str:
        if not errors:
            return "Unknown schema validation error."
        first = errors[0]
        location = ".".join(str(part) for part in first.get("loc", [])) or "unknown"
        message = first.get("msg", "invalid value")
        return f"{location}: {message}"

    # ---------------------------
    # Static lesson mode (demo)
    # ---------------------------
    if config.STATIC_LESSON_MODE:
        response = build_static_lesson(request.topic, request.level)

    # ---------------------------
    # Agentic pipeline (full mode)
    # ---------------------------
    else:
        planned_sections = planner_agent.plan(
            request.topic,
            request.level,
        )

        try:
            generated_sections = await content_agent.generate(
                topic=request.topic,
                planned_sections=planned_sections,
            )

            validated_sections = validator_agent.validate(generated_sections)

            response = LessonResponse(
                objective=f"Learn {request.topic} at a {request.level} level in 15 minutes.",
                total_minutes=15,
                sections=[
                    LessonSection(
                        id=s.id,
                        title=s.title,
                        minutes=s.minutes,
                        content_markdown=render_blocks_to_markdown(s.blocks),
                    )
                    for s in validated_sections
                ],
            )

        except ValidationError as exc:
            summary = _summarize_schema_errors(exc.errors())
            _record_failure(
                session_id=session_id,
                request=request,
                error_type="schema_validation",
                error_message=summary,
                error_details=exc.errors(),
                exc=exc,
            )
            raise

        except ValueError as exc:
            summary = str(exc) or "Unknown content validation error."
            _record_failure(
                session_id=session_id,
                request=request,
                error_type="content_validation",
                error_message=summary,
                exc=exc,
            )
            raise

        except Exception as exc:
            _record_failure(
                session_id=session_id,
                request=request,
                error_type=type(exc).__name__,
                error_message=str(exc) or "Unknown error.",
                exc=exc,
            )
            raise

    # ---------------------------
    # Telemetry (best-effort)
    # ---------------------------
    telemetry = LessonRun(
        run_id=str(uuid4()),
        session_id=session_id,
        topic=request.topic,
        level=request.level,
        created_at=datetime.now(timezone.utc),
        total_minutes=response.total_minutes,
        objective=response.objective,
        section_ids=[s.id for s in response.sections],
    )

    try:
        insert_lesson_run(telemetry.to_mongo())
        logger.info(
            "telemetry_written",
            extra={
                "run_id": telemetry.run_id,
                "topic": telemetry.topic,
                "difficulty": telemetry.level,
                "sections": len(telemetry.section_ids),
            },
        )
    except Exception as exc:
        logger.warning(
            "Telemetry insert failed run_id=%s session_id=%s",
            telemetry.run_id,
            session_id,
            exc_info=exc,
        )

    return response


def _record_failure(
    *,
    session_id: str,
    request: LessonRequest,
    error_type: str,
    error_message: str,
    error_details=None,
    exc: Exception | None = None,
) -> None:
    """Best-effort failure telemetry."""

    failure = LessonFailure(
        run_id=str(uuid4()),
        session_id=session_id,
        topic=request.topic,
        level=request.level,
        created_at=datetime.now(timezone.utc),
        error_type=error_type,
        error_message=error_message,
        error_details=error_details,
    )

    try:
        insert_lesson_failure(failure.to_mongo())
    except Exception as insert_exc:
        logger.warning(
            "Failure insert failed run_id=%s session_id=%s",
            failure.run_id,
            session_id,
            exc_info=insert_exc,
        )

    logger.error(
        "Lesson generation failed",
        extra={
            "topic": request.topic,
            "difficulty": request.level,
            "error_type": error_type,
        },
        exc_info=exc,
    )
