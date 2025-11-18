from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import Topic as TopicSchema, Article as ArticleSchema, TopicBase, TopicCreate
from app.auth import get_current_admin_user
from app.database import models
from app import crud
from app.config import settings
from typing import List, Optional
from uuid import UUID
import os
import re
import shutil
from pathlib import Path

router = APIRouter()

# 이미지 저장 디렉토리 설정
IMAGES_DIR = Path("/app/database/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """파일명에서 특수문자 제거 및 안전한 이름 생성"""
    # 공백을 언더스코어로
    name = name.replace(' ', '_')
    # 알파벳, 숫자, 언더스코어, 하이픈만 허용 (한글 포함)
    name = re.sub(r'[^\w\-]', '', name, flags=re.UNICODE)
    return name

@router.get("/", response_model=List[TopicSchema], summary="토픽 목록 조회")
async def get_topics_list(
    name: Optional[str] = Query(None, description="토픽 이름으로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession 비동기 쿼리로 수정 (relationships 포함)
    stmt = select(Topic).options(
        selectinload(Topic.sources),
        selectinload(Topic.articles)
    ).order_by(Topic.created_at.desc())
    if name:
        stmt = stmt.where(Topic.name.ilike(f"%{name}%"))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    topics = result.scalars().all()
    return topics

@router.post("/", response_model=TopicSchema, summary="새 토픽 생성", status_code=201)
async def create_new_topic(
    topic_data: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """새로운 토픽을 생성합니다."""
    try:
        new_topic = await crud.create_topic(db=db, topic=topic_data)
        return new_topic
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"토픽 생성 실패: {str(e)}")


@router.get("/{topic_id}", response_model=TopicSchema, summary="토픽 상세 정보 조회")
async def get_topic_details(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession 비동기 쿼리로 수정 (relationships 포함)
    stmt = select(Topic).options(
        selectinload(Topic.sources),
        selectinload(Topic.articles)
    ).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    topic = result.scalars().first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic


@router.get("/{topic_id}/articles", response_model=List[ArticleSchema], summary="토픽별 아티클 목록 조회")
async def get_topic_articles(
    topic_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """특정 토픽의 아티클 목록을 조회합니다."""
    # 토픽 존재 확인
    stmt = select(Topic).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    topic = result.scalars().first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 해당 토픽의 아티클 조회 (최신순)
    articles_stmt = select(Article).where(
        Article.topic_id == topic_id
    ).order_by(
        Article.created_at.desc()
    ).offset(skip).limit(limit)

    articles_result = await db.execute(articles_stmt)
    articles = articles_result.scalars().all()

    return articles


@router.put("/{topic_id}/", response_model=TopicSchema, summary="토픽 정보 수정")
async def update_topic(
    topic_id: UUID,
    topic_data: TopicBase,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """토픽 정보를 수정합니다."""
    updated_topic = await crud.update_topic(
        db=db,
        topic_id=topic_id,
        topic_update=topic_data
    )

    if not updated_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return updated_topic


@router.post("/{topic_id}/image/", summary="토픽 이미지 업로드")
async def upload_topic_image(
    topic_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """
    토픽 이미지를 업로드합니다.
    - 파일명: {토픽이름}.{확장자}
    - 기존 파일이 있으면 덮어쓰기
    """
    # 토픽 조회
    topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 파일 확장자 추출
    file_extension = file.filename.split('.')[-1].lower()
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
        )

    # 안전한 파일명 생성 (토픽 이름 기반)
    safe_topic_name = sanitize_filename(topic.name)
    filename = f"{safe_topic_name}.{file_extension}"
    file_path = IMAGES_DIR / filename

    # 파일 저장 (기존 파일 덮어쓰기)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")

    # image_uri 생성 및 DB 업데이트 (절대 URL)
    image_uri = f"{settings.server_url}/images/{filename}"
    topic.image_uri = image_uri
    await db.commit()
    await db.refresh(topic)

    return {"image_uri": image_uri, "filename": filename}


@router.delete("/{topic_id}/image/", summary="토픽 이미지 삭제")
async def delete_topic_image(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """
    토픽 이미지를 삭제합니다.
    - 서버의 실제 파일 삭제
    - DB의 image_uri를 NULL로 설정
    """
    # 토픽 조회
    topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if not topic.image_uri:
        raise HTTPException(status_code=404, detail="이미지가 없습니다")

    # 파일명 추출
    filename = topic.image_uri.split('/')[-1]
    file_path = IMAGES_DIR / filename

    # 실제 파일 삭제
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {str(e)}")

    # DB에서 image_uri 제거 (빈 문자열로 설정)
    topic.image_uri = ""
    await db.commit()
    await db.refresh(topic)

    return {"message": "이미지가 삭제되었습니다"}
