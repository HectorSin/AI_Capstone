import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://capstone_user:capstone_password@postgres:5432/capstone_db")
    
    # Redis 설정
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT 설정
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # API 키 설정
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    naver_clova_client_id: str = os.getenv("NAVER_CLOVA_CLIENT_ID", "")
    naver_clova_client_secret: str = os.getenv("NAVER_CLOVA_CLIENT_SECRET", "")
    
    # 파일 업로드 설정
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    
    # CORS 설정
    allowed_origins: Union[str, List[str]] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    
    @field_validator('allowed_origins')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 환경 설정
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    allow_http: bool = os.getenv("ALLOW_HTTP", "false").lower() == "true"
    
    # Redis 캐시 설정
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1시간
    session_ttl: int = int(os.getenv("SESSION_TTL", "1800"))  # 30분
    
    # Airflow 설정
    airflow_host: str = os.getenv("AIRFLOW_HOST", "http://localhost:8080")
    airflow_username: str = os.getenv("AIRFLOW_USERNAME", "admin")
    airflow_password: str = os.getenv("AIRFLOW_PASSWORD", "admin")
    
    # WebSocket 설정
    websocket_port: int = int(os.getenv("WEBSOCKET_PORT", "8001"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
settings = Settings()