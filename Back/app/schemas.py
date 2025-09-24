from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional
from datetime import datetime

# =================================================================
# 1. User Schemas
# =================================================================
class UserBase(BaseModel):
    email: EmailStr
    nickname: str

class UserCreate(UserBase):
    social_id: str
    provider: str

class User(UserBase):
    user_id: int
    plan: str
    profile_image_url: Optional[HttpUrl] = None

    class Config:
        from_attributes = True

# =================================================================
# 2. Token Schemas
# =================================================================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# =================================================================
# 3. SourceURL Schemas
# =================================================================
class SourceURLBase(BaseModel):
    original_url: HttpUrl

class SourceURLCreate(SourceURLBase):
    pass

class SourceURL(SourceURLBase):
    url_id: int

    class Config:
        from_attributes = True

# =================================================================
# 4. Voice Schemas
# =================================================================
class VoiceBase(BaseModel):
    voice_name: str
    gender: str

class Voice(VoiceBase):
    voice_id: int

    class Config:
        from_attributes = True

# =================================================================
# 5. GeneratedPodcast Schemas
# =================================================================
class GeneratedPodcastBase(BaseModel):
    episode_number: Optional[int] = None
    podcast_url: HttpUrl
    podcast_duration_sec: int

class GeneratedPodcast(GeneratedPodcastBase):
    podcast_id: int
    voice: Voice  # Voice 스키마를 중첩하여 목소리 정보 포함

    class Config:
        from_attributes = True

# =================================================================
# 6. TopicResult Schemas
# =================================================================
class TopicResultBase(BaseModel):
    status: str
    combined_summary_text: Optional[str] = None
    podcast_script: Optional[str] = None
    completed_at: Optional[datetime] = None

class TopicResult(TopicResultBase):
    result_id: int
    podcasts: List[GeneratedPodcast] = [] # 생성된 팟캐스트 목록을 포함

    class Config:
        from_attributes = True

# =================================================================
# 7. AnalysisTopic Schemas
# =================================================================
class AnalysisTopicBase(BaseModel):
    title: str
    one_line_summary: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None

class AnalysisTopicCreate(AnalysisTopicBase):
    # 주제를 생성할 때 참고할 URL 목록을 함께 받음
    source_urls: List[HttpUrl] 

# API 응답으로 나갈 최종 분석 주제 스키마
class AnalysisTopic(AnalysisTopicBase):
    topic_id: int
    user: User  # User 스키마를 중첩하여 작성자 정보 포함
    source_urls: List[SourceURL] = [] # 참고한 URL 목록 정보 포함
    result: Optional[TopicResult] = None # 분석 결과 정보 포함
    
    class Config:
        from_attributes = True

# =================================================================
# 8. Subscription & Schedule Schemas
# =================================================================
class SubscriptionCreate(BaseModel):
    creator_id: int

class ScheduleCreate(BaseModel):
    cron_expression: str
    is_active: bool = True