from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas
from app.database import models
from app.utils.audio import resolve_podcast_path

router = APIRouter(prefix="/podcasts", tags=["Podcasts"])


def _build_difficulty_order(preferred: Optional[models.DifficultyLevel]) -> List[str]:
    base_order = ["intermediate", "beginner", "advanced"]
    ordered: List[str] = []
    if preferred:
        preferred_value = preferred.value
        ordered.append(preferred_value)
    for level in base_order:
        if level not in ordered:
            ordered.append(level)
    return ordered


def _select_audio_payload(
    audio_data: Optional[Dict[str, Dict[str, Optional[float]]]],
    preferred: Optional[models.DifficultyLevel],
) -> Tuple[Optional[str], Optional[float]]:
    if not audio_data:
        return None, None

    for level in _build_difficulty_order(preferred):
        payload = audio_data.get(level)
        if payload and payload.get("audio_file"):
            return level, payload.get("duration")
    return None, None


@router.get("/daily", response_model=List[schemas.DailyPodcastSummary])
async def get_daily_podcasts(
    start_date: Optional[date] = Query(None, description="조회 시작 날짜 (기본: 제한 없음)"),
    end_date: Optional[date] = Query(None, description="조회 종료 날짜 (기본: 오늘)"),
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    today = date.today()
    resolved_end = end_date or today
    # 기본값을 충분히 과거로 설정하여 모든 팟캐스트 조회
    resolved_start = start_date or date(2020, 1, 1)

    if resolved_start > resolved_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than end_date",
        )

    user_topics = await crud.list_topics_for_user(db, user_id=current_user.id)
    if not user_topics:
        return []

    topic_ids = [topic.id for topic in user_topics]
    rows = await crud.list_articles_with_audio_for_topics(
        db,
        topic_ids=topic_ids,
        start_date=resolved_start,
        end_date=resolved_end,
    )

    if not rows:
        return []

    grouped: Dict[date, Dict[str, object]] = defaultdict(
        lambda: {
            "segments": [],
            "topics": set(),
            "total_duration": 0.0,
        }
    )

    preferred_level = current_user.difficulty_level

    for article, topic in rows:
        chosen_level, duration = _select_audio_payload(article.audio_data or {}, preferred_level)
        if not chosen_level or duration is None:
            continue

        entry = grouped[article.date]
        entry["topics"].add(topic.name)
        entry["total_duration"] = float(entry["total_duration"]) + float(duration or 0)

        segment = schemas.PodcastSegment(
            article_id=article.id,
            topic_id=topic.id,
            topic_name=topic.name,
            title=article.title,
            difficulty=chosen_level,
            audio_url=f"/podcasts/files/{article.id}?difficulty={chosen_level}",
            duration_seconds=float(duration or 0),
            source_url=article.source_url,
        )
        entry["segments"].append(segment)

    summaries: List[schemas.DailyPodcastSummary] = []
    for day in sorted(grouped.keys(), reverse=True):
        payload = grouped[day]
        segments: List[schemas.PodcastSegment] = payload["segments"]  # type: ignore[assignment]
        # skip days without valid segments
        if not segments:
            continue
        summary = schemas.DailyPodcastSummary(
            date=day,
            article_count=len(segments),
            total_duration_seconds=float(payload["total_duration"]),  # type: ignore[arg-type]
            topics=sorted(payload["topics"]),  # type: ignore[arg-type]
            segments=segments,
        )
        summaries.append(summary)

    return summaries


@router.get(
    "/files/{article_id}",
    response_class=FileResponse,
    responses={
        200: {"content": {"audio/mpeg": {}}},
        404: {"description": "audio_not_found"},
    },
)
async def serve_podcast_audio(
    article_id: UUID,
    difficulty: Optional[str] = Query(None, description="difficulty level (beginner/intermediate/advanced)"),
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    article = await crud.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article_not_found")

    user_topic_ids = {topic.id for topic in await crud.list_topics_for_user(db, user_id=current_user.id)}
    if article.topic_id not in user_topic_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_allowed")

    audio_data = article.audio_data or {}
    preferred_order = _build_difficulty_order(current_user.difficulty_level)
    if difficulty and difficulty in preferred_order:
        preferred_order = [difficulty] + [level for level in preferred_order if level != difficulty]

    file_path = None
    for level in preferred_order:
        payload = audio_data.get(level)
        path = payload.get("audio_file") if payload else None
        if path:
            resolved = resolve_podcast_path(path)
            if resolved:
                file_path = resolved
                break

    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audio_not_found")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=file_path.name,
    )
