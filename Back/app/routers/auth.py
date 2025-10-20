from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas
from app.database import models

router = APIRouter(
    tags=["Authentication"],
)


def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")
    if len(password) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be 128 characters or less.")
    has_alpha = any(ch.isalpha() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    if not (has_alpha and has_digit):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must include both letters and numbers.")


def _resolve_nickname(
    preferred: Optional[str],
    fallback: Optional[str],
    provider: models.SocialProviderType,
) -> str:
    base = preferred or fallback or f"{provider.value}_user"
    return base


@router.post("/register/local", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_local_user(
    payload: schemas.LocalRegisterRequest,
    db: AsyncSession = Depends(auth.get_db),
):
    existing_email = await crud.get_user_by_email(db, email=payload.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    existing_nickname = await crud.get_user_by_nickname(db, nickname=payload.nickname)
    if existing_nickname:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname is already in use.")

    _validate_password_strength(payload.password)

    password_hash = auth.hash_password(payload.password)
    try:
        user = await crud.create_local_user(
            db,
            email=payload.email,
            nickname=payload.nickname,
            password_hash=password_hash,
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User could not be created due to a conflict.")

    return schemas.User(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        plan=schemas.PlanType(user.plan.value),
        social_provider=schemas.SocialProviderType(user.social_provider.value),
        social_id=user.social_id,
        notification_time=user.notification_time,
        created_at=user.created_at,
        topics=[],
    )


@router.post("/login/local", response_model=schemas.Token)
async def login_local(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(auth.get_db),
):
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or user.social_provider != models.SocialProviderType.none:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    if not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    access_token = auth.create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/google", response_model=schemas.Token)
async def login_google(
    payload: schemas.GoogleLoginRequest,
    db: AsyncSession = Depends(auth.get_db),
):
    try:
        profile = auth.verify_google_id_token(payload.id_token)
    except auth.SocialAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = await crud.get_user_by_social(
        db,
        provider=models.SocialProviderType.google,
        social_id=profile.social_id,
    )

    if user is None:
        conflicting_user = await crud.get_user_by_email(db, email=profile.email)
        if conflicting_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is associated with another account.",
            )

        desired_nickname = _resolve_nickname(payload.nickname, profile.nickname, models.SocialProviderType.google)
        nickname = await crud.generate_unique_nickname(db, desired_nickname)

        try:
            user = await crud.create_social_user(
                db,
                email=profile.email,
                nickname=nickname,
                provider=models.SocialProviderType.google,
                social_id=profile.social_id,
            )
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.") from exc

    access_token = auth.create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/kakao", response_model=schemas.Token)
async def login_kakao(
    payload: schemas.KakaoLoginRequest,
    db: AsyncSession = Depends(auth.get_db),
):
    try:
        profile = await auth.fetch_kakao_profile(payload.access_token)
    except auth.SocialAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = await crud.get_user_by_social(
        db,
        provider=models.SocialProviderType.kakao,
        social_id=profile.social_id,
    )

    if user is None:
        conflicting_user = await crud.get_user_by_email(db, email=profile.email)
        if conflicting_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is associated with another account.",
            )

        fallback_nickname = f"kakao_{profile.social_id[-6:]}"
        desired_nickname = _resolve_nickname(payload.nickname, profile.nickname or fallback_nickname, models.SocialProviderType.kakao)
        nickname = await crud.generate_unique_nickname(db, desired_nickname)

        try:
            user = await crud.create_social_user(
                db,
                email=profile.email,
                nickname=nickname,
                provider=models.SocialProviderType.kakao,
                social_id=profile.social_id,
            )
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.") from exc

    access_token = auth.create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
