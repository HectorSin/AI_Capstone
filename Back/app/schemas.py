from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr, field_validator


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


class DifficultyLevel(str, Enum):
    beginner = "beginner"  # 하 (초급)
    intermediate = "intermediate"  # 중 (중급)
    advanced = "advanced"  # 상 (고급)


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
    difficulty_level: DifficultyLevel = DifficultyLevel.intermediate
    social_provider: SocialProviderType = SocialProviderType.none
    social_id: Optional[str] = None
    notification_time: Optional[Dict[str, Any]] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    plan: Optional[PlanType] = None
    difficulty_level: Optional[DifficultyLevel] = None
    social_provider: Optional[SocialProviderType] = None
    social_id: Optional[str] = None
    notification_time: Optional[Dict[str, Any]] = None


class LocalRegisterRequest(BaseModel):
    email: EmailStr
    nickname: str
    password: constr(min_length=8, max_length=32)
    difficulty_level: Optional[DifficultyLevel] = DifficultyLevel.intermediate
    topic_ids: List[UUID] = Field(default_factory=list, description="선택한 토픽 ID 목록")


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=32)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None  # Refresh Token 추가 (기존 코드 호환성 위해 Optional)


class TokenData(BaseModel):
    user_id: Optional[UUID] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AvailabilityResponse(BaseModel):
    available: bool


class NotificationPreferenceBase(BaseModel):
    allowed: bool
    time_enabled: bool
    hour: Optional[int] = Field(default=None, ge=0, le=23)
    minute: Optional[int] = Field(default=None, ge=0, le=59)
    days_of_week: List[int] = Field(default_factory=list)
    prompted: bool = False

    @field_validator('days_of_week')
    @classmethod
    def validate_days(cls, value: List[int]) -> List[int]:
        for day in value:
            if day < 0 or day > 6:
                raise ValueError('days_of_week values must be between 0 (Monday) and 6 (Sunday).')
        return value


class NotificationPreference(NotificationPreferenceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    pass


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


class ArticleBase(BaseModel):
    title: str
    date: date
    source_url: Optional[str] = None


class Article(ArticleBase):
    id: UUID
    topic_id: UUID
    status: str
    crawled_data: Optional[Dict[str, Any]] = None
    article_data: Optional[Dict[str, Any]] = None
    script_data: Optional[Dict[str, Any]] = None
    audio_data: Optional[Dict[str, Any]] = None
    storage_path: Optional[str] = None
    error_message: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DifficultyAudioInfo(BaseModel):
    """난이도별 오디오 정보"""
    audio_file: Optional[str] = None
    duration: Optional[float] = None


class ArticlePodcastResponse(BaseModel):
    """개별 팟캐스트(Article) 정보"""
    article_id: UUID
    title: str
    date: str
    source_url: Optional[str]
    status: str
    # 난이도별 오디오 정보
    audio_beginner: Optional[DifficultyAudioInfo] = None
    audio_intermediate: Optional[DifficultyAudioInfo] = None
    audio_advanced: Optional[DifficultyAudioInfo] = None
    error_message: Optional[str] = None


class PodcastBatchCreateResponse(BaseModel):
    """여러 팟캐스트 생성 응답"""
    topic: str
    topic_id: UUID
    keywords: List[str]
    total_crawled: int
    successful: int
    failed: int
    processing: int
    articles: List[ArticlePodcastResponse]
    created_at: str


# ==========================================================
# Article 피드 API 스키마 (Phase 5)
# ==========================================================
class ArticleFeedItem(BaseModel):
    """프론트엔드 FeedItem 타입과 호환되는 응답"""
    id: UUID
    title: str
    date: str  # "2024. 03. 20" 형식
    summary: str
    content: str
    imageUri: str  # topic.image_uri
    topic: str     # topic.name
    topicId: Optional[UUID] = None  # topic.id

    @classmethod
    def from_article(cls, article, topic, difficulty_level: str = "intermediate") -> "ArticleFeedItem":
        """Article + Topic 모델에서 FeedItem 생성

        Args:
            article: Article 모델 인스턴스
            topic: Topic 모델 인스턴스
            difficulty_level: 사용자 난이도 ('beginner', 'intermediate', 'advanced')
                            기본값은 'intermediate'
        """
        from app.config import settings

        # date를 "YYYY. MM. DD" 형식으로 변환
        formatted_date = article.date.strftime("%Y. %m. %d")

        # article_data JSONB에서 피드용 공통 summary 추출
        feed_summary = ""
        article_content = ""

        if article.article_data:
            feed_summary = article.article_data.get("summary", "")
            # 사용자 난이도에 맞는 content 사용, 없으면 intermediate로 fallback
            difficulty_data = article.article_data.get(difficulty_level, {})
            if not difficulty_data or not isinstance(difficulty_data, dict):
                # fallback: intermediate -> beginner -> advanced 순서
                for fallback_level in ["intermediate", "beginner", "advanced"]:
                    difficulty_data = article.article_data.get(fallback_level, {})
                    if difficulty_data and isinstance(difficulty_data, dict):
                        break
            article_content = difficulty_data.get("content", "") if isinstance(difficulty_data, dict) else ""

        # image_uri를 절대 URL로 변환
        image_uri = topic.image_uri
        if image_uri and not image_uri.startswith('http'):
            # 상대 경로면 절대 URL로 변환
            image_uri = f"{settings.server_url}{image_uri}"

        return cls(
            id=article.id,
            title=article.title,
            date=formatted_date,
            summary=feed_summary,
            content=article_content,
            imageUri=image_uri,
            topic=topic.name,
            topicId=topic.id
        )


class ArticleFeedResponse(BaseModel):
    """페이지네이션이 포함된 피드 응답"""
    items: List[ArticleFeedItem]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        from_attributes = True


class TopicCreate(TopicBase):
    sources: List[TopicSourceCreate] = Field(default_factory=list)


class Topic(TopicBase):
    id: UUID
    created_at: datetime
    sources: List[TopicSource] = Field(default_factory=list)
    articles: List[Article] = Field(default_factory=list)

    @field_validator('image_uri', mode='after')
    @classmethod
    def convert_image_uri_to_absolute(cls, value: str) -> str:
        """image_uri를 절대 URL로 변환"""
        from app.config import settings

        if value and not value.startswith('http'):
            # 상대 경로면 절대 URL로 변환
            return f"{settings.server_url}{value}"
        return value

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
# Archive / Podcast 요약 스키마
# ==========================================================
class PodcastSegment(BaseModel):
    article_id: UUID
    topic_id: UUID
    topic_name: str
    title: str
    difficulty: str
    audio_url: str
    duration_seconds: float
    source_url: Optional[str] = None


class DailyPodcastSummary(BaseModel):
    date: date
    article_count: int
    total_duration_seconds: float
    topics: List[str]
    segments: List[PodcastSegment]


class SelectTopicRequest(BaseModel):
    topic_id: UUID


class SelectTopicResponse(BaseModel):
    user_id: UUID
    topic_id: UUID


class PreferredTopic(BaseModel):
    topic_id: UUID
    name: str


# ==========================================================
# 팟캐스트 생성 관련 스키마
# ==========================================================
class PodcastCreate(BaseModel):
    """팟캐스트 생성 요청 스키마"""
    topic: str = Field(..., description="팟캐스트 주제")
    keywords: List[str] = Field(default_factory=list, description="관련 키워드 목록")
    user_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None


class PodcastCreateResponse(BaseModel):
    """팟캐스트 생성 응답 스키마"""
    podcast_id: str
    topic: str
    keywords: List[str]
    status: str
    article: Dict[str, Any]
    script: str
    audio: Dict[str, Any]


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
# 관리자(Admin) 스키마
# ==========================================================
class AdminRegisterRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================================
# Forward reference 초기화
# ==========================================================
try:
    User.model_rebuild()
    Topic.model_rebuild()
    Article.model_rebuild()
except AttributeError:
    User.update_forward_refs()
    Topic.update_forward_refs()
    Article.update_forward_refs()
