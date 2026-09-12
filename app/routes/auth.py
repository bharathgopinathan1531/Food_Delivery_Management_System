from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import (
    create,
    get_by_email,
    get_by_id,
)
from app.schemas.auth import (
    ALLOWED_ROLES,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    if data.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    email = data.email.lower()

    existing_user = get_by_email(
        db,
        email
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    user = User(
        name=data.name.strip(),
        email=email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role,
    )

    return create(db, user)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = get_by_email(
        db,
        data.email.lower()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.role
        ),
        refresh_token=create_refresh_token(
            user.id,
            user.role
        )
    )


@router.post(
    "/refresh",
    response_model=TokenResponse
)
def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):

    payload = decode_token(
        data.refresh_token
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Refresh token required"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user = get_by_id(
        db,
        int(user_id)
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    return TokenResponse(
        access_token=create_access_token(
            user.id,
            user.role
        ),
        refresh_token=create_refresh_token(
            user.id,
            user.role
        )
    )


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):

    return current_user


@router.put(
    "/change-password"
)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not verify_password(
        data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    current_user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }