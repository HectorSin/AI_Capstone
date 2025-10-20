from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, ForeignKey,
    Enum as SQLEnum, ARRAY, Date, func, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .database import Base
import enum

# ==========================================================
# ENUM 정의
# ==========================================================
class PlanType(enum.Enum):
    free = "free"
    premium = "premium"

class SocialProviderType(enum.Enum):
    google = "google"
    kakao = "kakao"
    none = "none"

class TopicType(enum.Enum):
    company = "company"
    keyword = "keyword"


# ==========================================================
# User 테이블
# ==========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True)
    nickname = Column(String(100), unique=True, nullable=False)
    plan = Column(SQLEnum(PlanType, name="plan_type"), nullable=False, server_default="free")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    social_provider = Column(SQLEnum(SocialProviderType, name="social_provider_type"), server_default="none")
    social_id = Column(String(255))
    password_hash = Column(Text)
    notification_time = Column(JSONB)

    topics = relationship("UserTopic", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname}, plan={self.plan})>"


# ==========================================================
# Topic 테이블
# ==========================================================
class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(100), unique=True, nullable=False)
    type = Column(SQLEnum(TopicType, name="topic_type"), nullable=False)
    summary = Column(Text)
    image_uri = Column(Text, nullable=False)
    keywords = Column(ARRAY(Text))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    users = relationship("UserTopic", back_populates="topic", cascade="all, delete-orphan")
    sources = relationship("TopicSource", back_populates="topic", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name}, type={self.type})>"


# ==========================================================
# UserTopic (다대다 관계)
# ==========================================================
class UserTopic(Base):
    __tablename__ = "user_topic"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="topics")
    topic = relationship("Topic", back_populates="users")


# ==========================================================
# TopicSources
# ==========================================================
class TopicSource(Base):
    __tablename__ = "topic_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    topic = relationship("Topic", back_populates="sources")

    def __repr__(self):
        return f"<TopicSource(id={self.id}, source_name={self.source_name}, active={self.is_active})>"


# ==========================================================
# Article
# ==========================================================
class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(Text)
    date = Column(Date, nullable=False)
    json_data = Column(JSONB)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    topic = relationship("Topic", back_populates="articles")
    podcast_script = relationship("PodcastScript", back_populates="article", uselist=False, cascade="all, delete-orphan")
    podcast = relationship("Podcast", back_populates="article", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title[:30]}...)>"


# ==========================================================
# PodcastScript
# ==========================================================
class PodcastScript(Base):
    __tablename__ = "podcast_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    article = relationship("Article", back_populates="podcast_script")
    podcast = relationship("Podcast", back_populates="script", uselist=False)

    def __repr__(self):
        return f"<PodcastScript(id={self.id}, article_id={self.article_id})>"


# ==========================================================
# Podcast
# ==========================================================
class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False)
    script_id = Column(UUID(as_uuid=True), ForeignKey("podcast_scripts.id", ondelete="CASCADE"), unique=True)
    audio_uri = Column(Text, nullable=False)
    duration = Column(Integer)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    article = relationship("Article", back_populates="podcast")
    script = relationship("PodcastScript", back_populates="podcast")

    def __repr__(self):
        return f"<Podcast(id={self.id}, duration={self.duration})>"
