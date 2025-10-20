"""인증 및 보안 유틸리티 모음."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.config import settings
from app.database import database, models

logger = logging.getLogger(__name__)

try:  # Google OAuth2 토큰 검증 라이브러리 (설치 여부 대비)
    from google.auth.exceptions import GoogleAuthError
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except Exception:  # pragma: no cover - 라이브러리 미설치 대비
    GoogleAuthError = Exception  # type: ignore
    google_requests = None  # type: ignore
    google_id_token = None  # type: ignore

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/local")

KAKAO_USERINFO_ENDPOINT = "https://kapi.kakao.com/v2/user/me"


class AuthenticationError(RuntimeError):
    """일반 인증 오류."""


class SocialAuthenticationError(AuthenticationError):
    """소셜 로그인 검증 실패 시 사용."""

    def __init__(self, provider: models.SocialProviderType, message: str):
        self.provider = provider
        super().__init__(message)


@dataclass
class SocialProfile:
    """소셜 계정으로부터 얻은 핵심 정보."""

    social_id: str
    email: str
    nickname: Optional[str] = None


# ==========================================================
# 비밀번호 해싱 & JWT 토큰 생성 유틸
# ==========================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def create_access_token(
    *,
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    claims: Dict[str, Any] = dict(additional_claims or {})
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    claims.update({"sub": subject, "exp": expire})
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return token


# ==========================================================
# FastAPI 의존성
# ==========================================================
async def get_db():
    async with database.AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = UUID(str(subject))
        token_data = schemas.TokenData(user_id=user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await crud.get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


# ==========================================================
# 소셜 로그인 토큰 검증
# ==========================================================

def verify_google_id_token(id_token: str) -> SocialProfile:
    if not settings.google_client_id:
        raise SocialAuthenticationError(
            models.SocialProviderType.google,
            "Google OAuth client ID is not configured.",
        )
    if google_requests is None or google_id_token is None:
        raise SocialAuthenticationError(
            models.SocialProviderType.google,
            "Google authentication libraries are unavailable.",
        )

    try:
        request = google_requests.Request()
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            request,
            settings.google_client_id,
        )

        issuer = id_info.get("iss")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            raise ValueError("Invalid issuer")

        email = id_info.get("email")
        if not email:
            raise ValueError("Email claim missing")
        if not id_info.get("email_verified", False):
            raise ValueError("Email is not verified")

        return SocialProfile(
            social_id=str(id_info.get("sub")),
            email=email,
            nickname=id_info.get("name"),
        )
    except (ValueError, GoogleAuthError) as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise SocialAuthenticationError(
            models.SocialProviderType.google,
            "Invalid Google identity token.",
        ) from exc


async def fetch_kakao_profile(access_token: str) -> SocialProfile:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(KAKAO_USERINFO_ENDPOINT, headers=headers)

    if response.status_code != status.HTTP_200_OK:
        logger.warning(
            "Kakao profile request failed: %s %s",
            response.status_code,
            response.text,
        )
        raise SocialAuthenticationError(
            models.SocialProviderType.kakao,
            "Failed to verify Kakao access token.",
        )

    data: Dict[str, Any] = response.json()
    social_id = data.get("id")
    if social_id is None:
        raise SocialAuthenticationError(
            models.SocialProviderType.kakao,
            "Kakao response does not include an id field.",
        )

    account: Dict[str, Any] = data.get("kakao_account", {})
    email = account.get("email")
    if not email:
        raise SocialAuthenticationError(
            models.SocialProviderType.kakao,
            "Kakao account email permission is required.",
        )

    is_valid = account.get("is_email_valid")
    is_verified = account.get("is_email_verified")
    if not (is_valid and is_verified):
        raise SocialAuthenticationError(
            models.SocialProviderType.kakao,
            "Kakao email is not verified.",
        )

    nickname = account.get("profile", {}).get("nickname")

    return SocialProfile(
        social_id=str(social_id),
        email=email,
        nickname=nickname,
    )
