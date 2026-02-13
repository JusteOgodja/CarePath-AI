from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthRole, create_access_token
from app.core.config import get_admin_credentials, get_viewer_credentials
from app.core.rate_limit import rate_limit
from app.services.schemas import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    _: None = Depends(rate_limit("auth_login", limit=10, window_seconds=60)),
) -> LoginResponse:
    username = payload.username.strip()
    password = payload.password

    admin_user, admin_pass = get_admin_credentials()
    viewer_user, viewer_pass = get_viewer_credentials()

    role: AuthRole | None = None
    if username == admin_user and password == admin_pass:
        role = "admin"
    elif username == viewer_user and password == viewer_pass:
        role = "viewer"

    if role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(username=username, role=role)
    return LoginResponse(access_token=token, role=role, username=username)
