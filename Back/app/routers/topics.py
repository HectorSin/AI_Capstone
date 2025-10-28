from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas

router = APIRouter(
    tags=["Topics"],
    prefix="/topics",
)


@router.post("/", response_model=schemas.Topic, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_in: schemas.TopicCreate,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    topic = await crud.create_topic_for_user(db=db, user_id=current_user.id, topic=topic_in)
    return topic


@router.get("/", response_model=List[schemas.Topic])
async def list_topics(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    topics = await crud.list_topics_for_user(db=db, user_id=current_user.id)
    return topics


@router.get("/{topic_id}", response_model=schemas.Topic)
async def get_topic(
    topic_id: UUID,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    if not any(link.user_id == current_user.id for link in topic.users):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return topic
