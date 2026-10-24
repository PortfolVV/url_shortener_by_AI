"""Authentication endpoints."""

import logging

from fastapi import APIRouter, Request, status

from src.api.deps import AuthServiceDep, CurrentUser
from src.config import settings
from src.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut
from src.utils.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(settings.register_rate_limit)
async def register(
    request: Request,
    payload: UserCreate,
    service: AuthServiceDep,
) -> UserOut:
    user = await service.register(payload)
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request,
    payload: UserLogin,
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(payload)


@router.get("/me", response_model=UserOut, summary="Current user profile")
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
