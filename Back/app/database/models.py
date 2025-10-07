from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Table, func, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .database import Base
import enum

# AnalysisTopic과 SourceURL의 다대다(Many-to-Many) 관계를 위한 중간 테이블
TopicURL = Table(
    'topic_url',  # <-- 'topicURL'에서 'topic_url'로 수정
    Base.metadata,
    Column('topic_id', Integer, ForeignKey('analysis_topic.topic_id'), primary_key=True),
    Column('url_id', Integer, ForeignKey('source_url.url_id'), primary_key=True)
)

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    social_id = Column(String, unique=True, index=True)
    provider = Column(String)  # 'google', 'kakao'
    email = Column(String, unique=True, index=True)
    nickname = Column(String)
    profile_image_url = Column(String, nullable=True)
    plan = Column(String, default='free')  # 'free', 'premium'
    created_at = Column(DateTime, default=func.now())

    # User와 다른 테이블들의 관계 정의
    topics = relationship("AnalysisTopic", back_populates="user")
    preferences = relationship("UserVoicePreference", back_populates="user")
    # foreign_keys를 실제 Column 객체로 지정하도록 수정
    subscriptions = relationship("Subscription", foreign_keys="[Subscription.user_id]", back_populates="subscriber")
    subscribers = relationship("Subscription", foreign_keys="[Subscription.creator_id]", back_populates="creator")

    def __str__(self):
        return self.nickname

# --- 이하 코드는 모두 올바르게 작성되어 수정할 필요가 없습니다. ---

class AnalysisTopic(Base):
    __tablename__ = "analysis_topic"

    topic_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    title = Column(String)
    one_line_summary = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="topics")
    source_urls = relationship("SourceURL", secondary=TopicURL, back_populates="topics")
    result = relationship("TopicResult", back_populates="topic", uselist=False)
    schedules = relationship("Schedule", back_populates="topic")

    def __str__(self):
        return self.title


class SourceURL(Base):
    __tablename__ = "source_url"

    url_id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())

    topics = relationship("AnalysisTopic", secondary=TopicURL, back_populates="source_urls")

    def __str__(self):
        return self.original_url


class TopicResult(Base):
    __tablename__ = "topic_result"

    result_id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey('analysis_topic.topic_id'), unique=True)
    status = Column(String)
    combined_summary_text = Column(Text, nullable=True)
    podcast_script = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    topic = relationship("AnalysisTopic", back_populates="result")
    podcasts = relationship("GeneratedPodcast", back_populates="result")


class GeneratedPodcast(Base):
    __tablename__ = "generated_podcast"

    podcast_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey('topic_result.result_id'))
    voice_id = Column(Integer, ForeignKey('voice.voice_id'))
    episode_number = Column(Integer, nullable=True)
    podcast_url = Column(String)
    podcast_duration_sec = Column(Integer)
    
    result = relationship("TopicResult", back_populates="podcasts")
    voice = relationship("Voice", back_populates="podcasts")


class Voice(Base):
    __tablename__ = "voice"

    voice_id = Column(Integer, primary_key=True, index=True)
    voice_name = Column(String, unique=True)
    language = Column(String)
    gender = Column(String)

    podcasts = relationship("GeneratedPodcast", back_populates="voice")
    preferences = relationship("UserVoicePreference", back_populates="voice")

    def __str__(self):
        return self.voice_name


class UserVoicePreference(Base):
    __tablename__ = "user_voice_preference"

    preference_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    voice_id = Column(Integer, ForeignKey('voice.voice_id'))
    play_order = Column(Integer)
    is_default = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="preferences")
    voice = relationship("Voice", back_populates="preferences")


class Subscription(Base):
    __tablename__ = "subscription"

    subscription_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    creator_id = Column(Integer, ForeignKey('user.user_id'))
    created_at = Column(DateTime, default=func.now())

    subscriber = relationship("User", foreign_keys=[user_id], back_populates="subscriptions")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="subscribers")


class Schedule(Base):
    __tablename__ = "schedule"

    schedule_id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey('analysis_topic.topic_id'))
    cron_expression = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    topic = relationship("AnalysisTopic", back_populates="schedules")


# =================================================================
# AI Job Management Models
# =================================================================
class JobStatusEnum(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobTypeEnum(enum.Enum):
    URL_ANALYSIS = "url_analysis"
    TOPIC_GENERATION = "topic_generation"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_GENERATION = "audio_generation"
    FULL_PIPELINE = "full_pipeline"

class AIJob(Base):
    __tablename__ = "ai_job"

    job_id = Column(Integer, primary_key=True, index=True)
    job_type = Column(SQLEnum(JobTypeEnum), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    topic_id = Column(Integer, ForeignKey('analysis_topic.topic_id'), nullable=True)
    status = Column(SQLEnum(JobStatusEnum), default=JobStatusEnum.PENDING)
    progress = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    airflow_dag_run_id = Column(String, nullable=True)
    airflow_task_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    topic = relationship("AnalysisTopic")

    def __str__(self):
        return f"AIJob {self.job_id} - {self.job_type.value} - {self.status.value}"


class JobLog(Base):
    __tablename__ = "job_log"

    log_id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('ai_job.job_id'), nullable=False)
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    job = relationship("AIJob")

    def __str__(self):
        return f"JobLog {self.log_id} - {self.level} - {self.job_id}"