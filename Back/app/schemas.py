from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr


# ==========================================================
# 공통 열거형(Enum)
# ==========================================================
class PlanType(str, Enum):
    free = "free"
    premium = "premium"


class SocialProviderType(str, Enum):
    google = "google"
    kakao = "kakao"
    none = "none"


class TopicType(str, Enum):
    company = "company"
    keyword = "keyword"


# ==========================================================
# 사용자(User) 스키마
# ==========================================================
class UserBase(BaseModel):
    email: EmailStr
    nickname: str
    plan: PlanType = PlanType.free
    social_provider: SocialProviderType = SocialProviderType.none
    social_id: Optional[str] = None
    notification_time: Optional[Dict[str, Any]] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    plan: Optional[PlanType] = None
    social_provider: Optional[SocialProviderType] = None
    social_id: Optional[str] = None
    notification_time: Optional[Dict[str, Any]] = None


class LocalRegisterRequest(BaseModel):
    email: EmailStr
    nickname: str
    password: constr(min_length=8, max_length=32)


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=32)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[UUID] = None


class AvailabilityResponse(BaseModel):
    available: bool


class GoogleLoginRequest(BaseModel):
    id_token: str
    nickname: Optional[str] = None


class KakaoLoginRequest(BaseModel):
    access_token: str
    nickname: Optional[str] = None


# Topic 관련 스키마에서 사용되므로 선행 선언
class TopicBase(BaseModel):
    name: str
    type: TopicType
    summary: Optional[str] = None
    image_uri: str
    keywords: List[str] = Field(default_factory=list)


class TopicSourceBase(BaseModel):
    source_name: str
    source_url: HttpUrl
    is_active: bool = True


class TopicSourceCreate(TopicSourceBase):
    pass


class TopicSource(TopicSourceBase):
    id: UUID
    topic_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PodcastScriptBase(BaseModel):
    data: Dict[str, Any]


class PodcastBase(BaseModel):
    audio_uri: str
    duration: Optional[int] = None


class ArticleBase(BaseModel):
    title: str
    summary: str
    content: str
    source_url: Optional[HttpUrl] = None
    date: date
    json_data: Optional[Dict[str, Any]] = None


class PodcastScript(PodcastScriptBase):
    id: UUID
    article_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class Podcast(PodcastBase):
    id: UUID
    article_id: UUID
    script_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Article(ArticleBase):
    id: UUID
    topic_id: UUID
    created_at: datetime
    podcast_script: Optional[PodcastScript] = None
    podcast: Optional[Podcast] = None

    class Config:
        from_attributes = True


class TopicCreate(TopicBase):
    sources: List[TopicSourceCreate] = Field(default_factory=list)


class Topic(TopicBase):
    id: UUID
    created_at: datetime
    sources: List[TopicSource] = Field(default_factory=list)
    articles: List[Article] = Field(default_factory=list)

    class Config:
        from_attributes = True


class User(UserBase):
    id: UUID
    created_at: datetime
    topics: List[Topic] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==========================================================
# 사용자와 토픽 사이 관계 스키마
# ==========================================================
class UserTopicLink(BaseModel):
    user_id: UUID
    topic_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================================
# 기존 서비스에서 사용하던 AI Job 관련 스키마 (선택적 유지)
# ==========================================================
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    URL_ANALYSIS = "url_analysis"
    TOPIC_GENERATION = "topic_generation"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_GENERATION = "audio_generation"
    FULL_PIPELINE = "full_pipeline"


class AIJobBase(BaseModel):
    job_type: JobType
    user_id: UUID
    topic_id: Optional[UUID] = None
    input_data: Dict[str, Any]
    priority: int = 0


class AIJobCreate(AIJobBase):
    pass


class AIJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AIJob(AIJobBase):
    id: UUID
    status: JobStatus
    progress: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==========================================================
# WebSocket 메시지 스키마
# ==========================================================
class WebSocketMessage(BaseModel):
    type: str
    job_id: UUID
    data: Dict[str, Any]
    timestamp: datetime


class JobStatusUpdate(BaseModel):
    job_id: UUID
    status: JobStatus
    progress: int
    message: Optional[str] = None
    timestamp: datetime


# ==========================================================
# Forward reference 초기화
# ==========================================================
try:
    User.model_rebuild()
    Topic.model_rebuild()
    Article.model_rebuild()
    Podcast.model_rebuild()
    PodcastScript.model_rebuild()
except AttributeError:
    User.update_forward_refs()
    Topic.update_forward_refs()
    Article.update_forward_refs()
    Podcast.update_forward_refs()
    PodcastScript.update_forward_refs()
