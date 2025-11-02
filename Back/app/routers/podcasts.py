"""
팟캐스트 아카이브 및 다운로드를 위한 API 엔드포인트
"""
import logging
import os
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/podcasts",
    tags=["Podcasts"],
)


@router.get(
    "/archive",
    response_model=List[schemas.ArchiveItem],
    summary="아카이브 목록 조회",
    description="로그인한 사용자의 아카이브 팟캐스트 목록을 조회합니다.",
)
async def get_archive(
    limit: int = Query(50, ge=1, le=100, description="조회 개수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    """사용자의 아카이브 팟캐스트 목록을 조회합니다."""
    try:
        podcasts = await crud.list_user_podcasts(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        
        archive_items = []
        for podcast in podcasts:
            if podcast.article:
                # 아티클의 토픽에서 키워드 추출 (토픽 이름을 키워드로 사용)
                keywords = []
                if podcast.article.topic:
                    keywords = [podcast.article.topic.name]
                
                archive_item = schemas.ArchiveItem(
                    id=podcast.id,
                    date=podcast.article.date,
                    keywords=keywords,
                    duration=podcast.duration,
                    audio_uri=podcast.audio_uri,
                    title=podcast.article.title,
                    created_at=podcast.created_at,
                )
                archive_items.append(archive_item)
        
        return archive_items
    except Exception as e:
        logger.error(f"아카이브 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{podcast_id}/download",
    summary="팟캐스트 다운로드",
    description="팟캐스트 오디오 파일을 다운로드합니다.",
    response_class=FileResponse,
)
async def download_podcast(
    podcast_id: UUID,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    """팟캐스트 오디오 파일을 다운로드합니다."""
    try:
        from sqlalchemy import select
        from app.database import models
        
        # 팟캐스트 조회
        stmt = select(models.Podcast).where(models.Podcast.id == podcast_id)
        result = await db.execute(stmt)
        podcast = result.scalars().first()
        
        if not podcast:
            raise HTTPException(status_code=404, detail="팟캐스트를 찾을 수 없습니다")
        
        # 사용자 권한 확인 (사용자가 구독한 토픽의 팟캐스트인지 확인)
        if podcast.article and podcast.article.topic:
            from app.database.models import UserTopic
            user_topic_stmt = select(UserTopic).where(
                UserTopic.user_id == current_user.id,
                UserTopic.topic_id == podcast.article.topic.id,
            )
            user_topic_result = await db.execute(user_topic_stmt)
            user_topic = user_topic_result.scalars().first()
            
            if not user_topic:
                raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 파일 경로 확인
        audio_path = podcast.audio_uri
        
        # audio_uri가 상대 경로인 경우 절대 경로로 변환
        if not os.path.isabs(audio_path):
            # 기본 저장 경로 사용
            base_path = getattr(settings, 'upload_dir', '/app/database')
            audio_path = os.path.join(base_path, audio_path)
        
        if not os.path.exists(audio_path):
            logger.error(f"파일을 찾을 수 없습니다: {audio_path}")
            raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다")
        
        # 파일명 추출
        filename = os.path.basename(audio_path)
        if not filename:
            filename = f"podcast_{podcast_id}.mp3"
        
        return FileResponse(
            path=audio_path,
            filename=filename,
            media_type="audio/mpeg",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"팟캐스트 다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

