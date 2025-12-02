from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import Article as ArticleSchema
from app.auth import get_current_admin_user
from app.database import models
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate/{topic_id}", summary="토픽 기반 팟캐스트 생성")
async def generate_podcast_for_topic(
    topic_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """
    특정 토픽에 대해 팟캐스트를 생성합니다.
    백그라운드에서 비동기적으로 처리됩니다.
    """
    from app.services.podcast_service import podcast_service
    from app import crud

    try:
        # 토픽 조회
        topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # 백그라운드 작업으로 팟캐스트 생성
        async def create_podcast_bg():
            async with get_db() as session:
                try:
                    logger.info(f"팟캐스트 생성 시작: {topic.name}")
                    result = await podcast_service.create_podcast(
                        topic=topic.name,
                        keywords=topic.keywords,
                        db=session
                    )
                    logger.info(f"팟캐스트 생성 완료: {topic.name}")
                except Exception as e:
                    logger.error(f"팟캐스트 생성 실패: {e}")

        background_tasks.add_task(create_podcast_bg)

        return {
            "message": f"팟캐스트 생성 작업이 시작되었습니다: {topic.name}",
            "topic_id": str(topic_id),
            "topic_name": topic.name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"팟캐스트 생성 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{topic_id}", summary="토픽별 팟캐스트 생성 상태 조회")
async def get_podcast_status(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """
    특정 토픽의 팟캐스트 생성 상태를 조회합니다.
    """
    try:
        # 토픽의 Article 상태 조회
        stmt = select(Article).where(
            Article.topic_id == topic_id
        ).order_by(Article.created_at.desc()).limit(50)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        # 상태별 집계
        status_counts = {}
        for article in articles:
            status = article.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "topic_id": str(topic_id),
            "total_articles": len(articles),
            "status_counts": status_counts,
            "recent_articles": [
                {
                    "id": str(article.id),
                    "title": article.title,
                    "status": article.status,
                    "created_at": article.created_at.isoformat() if article.created_at else None,
                    "error_message": article.error_message
                }
                for article in articles[:10]
            ]
        }

    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{topic_id}", summary="토픽별 생성된 파일 목록 조회")
async def get_generated_files(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """
    특정 토픽의 생성된 파일 목록을 조회합니다.
    """
    import os
    from pathlib import Path

    try:
        # 토픽 조회
        from app import crud
        topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # 파일 시스템에서 파일 찾기
        base_path = Path("/app/podcasts")
        files = []

        if base_path.exists():
            # 모든 팟캐스트 디렉토리 탐색
            for podcast_dir in base_path.iterdir():
                if podcast_dir.is_dir():
                    # metadata.json 확인
                    metadata_file = podcast_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            import json
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)

                                # 토픽 이름으로 필터링
                                if metadata.get('topic') == topic.name:
                                    # 디렉토리 내 파일 수집
                                    for file_path in podcast_dir.rglob('*'):
                                        if file_path.is_file():
                                            files.append({
                                                "path": str(file_path.relative_to(base_path)),
                                                "name": file_path.name,
                                                "size": file_path.stat().st_size,
                                                "modified": file_path.stat().st_mtime,
                                                "type": file_path.suffix
                                            })
                        except Exception as e:
                            logger.error(f"메타데이터 읽기 실패: {e}")

        return {
            "topic_id": str(topic_id),
            "topic_name": topic.name,
            "total_files": len(files),
            "files": sorted(files, key=lambda x: x['modified'], reverse=True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
