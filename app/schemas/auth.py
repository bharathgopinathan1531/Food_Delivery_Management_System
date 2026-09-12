from pydantic import BaseModel, ConfigDict, EmailStr, Field


ALLOWED_ROLES = {
    "Admin",
    "Restaurant Owner",
    "Restaurant Staff",
    "Delivery Partner",
    "Customer",
}


class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    password: str = Field(
        min_length=8,
        max_length=128
    )

    role: str = "Customer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class ChangePasswordRequest(BaseModel):
    current_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128
    )