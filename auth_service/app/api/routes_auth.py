from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_uc, get_current_user, require_admin_user
from app.db.models import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> User:
    return await auth_uc.register(email=str(data.email), password=data.password)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> TokenResponse:
    access_token = await auth_uc.login(email=form.username, password=form.password)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/admin/ping")
async def admin_ping(admin: User = Depends(require_admin_user)) -> dict[str, str]:
    """Служебная ручка: доступна только пользователям с role=admin в JWT/БД."""
    return {"status": "ok", "role": admin.role}
