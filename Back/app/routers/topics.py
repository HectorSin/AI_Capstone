from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import schemas
from app import auth
from app import crud

router = APIRouter(
    tags=["Topics"],
    prefix="/topics",
)

@router.post("/", response_model=schemas.AnalysisTopic, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic: schemas.AnalysisTopicCreate,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db)
):
    """새로운 분석 주제 생성"""
    return await crud.create_topic_for_user(db=db, topic=topic, user_id=current_user.user_id)

@router.get("/", response_model=List[schemas.AnalysisTopic])
async def get_user_topics(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db)
):
    """사용자의 분석 주제 목록 조회"""
    # TODO: 사용자의 주제 목록을 조회하는 CRUD 함수 구현 필요
    return []

@router.get("/{topic_id}", response_model=schemas.AnalysisTopic)
async def get_topic(
    topic_id: int,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db)
):
    """특정 분석 주제 조회"""
    # TODO: 주제 조회 CRUD 함수 구현 필요
    raise HTTPException(status_code=404, detail="Topic not found")
