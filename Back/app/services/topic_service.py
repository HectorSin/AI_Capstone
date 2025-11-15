"""
Topic 관리 서비스

Topic을 찾거나 생성하는 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional
from app.database.models import Topic, TopicType
import logging

logger = logging.getLogger(__name__)


class TopicService:
    """Topic 관리 서비스"""

    @staticmethod
    async def get_or_create_topic(
        db: AsyncSession,
        topic_name: str,
        keywords: Optional[List[str]] = None,
        topic_type: TopicType = TopicType.company
    ) -> UUID:
        """
        Topic을 이름으로 찾거나 없으면 생성

        Args:
            db: AsyncSession (비동기 세션)
            topic_name: 토픽 이름 (예: "GOOGLE")
            keywords: 키워드 리스트
            topic_type: 토픽 타입 (company 또는 keyword)

        Returns:
            topic_id (UUID)
        """
        # 1. Topic 찾기
        stmt = select(Topic).where(Topic.name == topic_name)
        result = await db.execute(stmt)
        topic = result.scalars().first()

        # 2. 없으면 생성
        if not topic:
            logger.info(f"Topic '{topic_name}' 생성 중...")
            topic = Topic(
                name=topic_name,
                type=topic_type,
                keywords=keywords or [],
                image_uri="https://placeholder.com/default.png"  # 기본 이미지
            )
            db.add(topic)
            await db.commit()
            await db.refresh(topic)
            logger.info(f"Topic '{topic_name}' 생성 완료 (ID: {topic.id})")
        else:
            logger.info(f"Topic '{topic_name}' 이미 존재 (ID: {topic.id})")

        return topic.id
