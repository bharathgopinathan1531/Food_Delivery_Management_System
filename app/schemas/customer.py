from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str

    class Config:
        from_attributes = True


class AddressCreate(BaseModel):
    address_line: str = Field(..., min_length=5, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=4, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_type: str = Field(default="Home", max_length=30)
    is_default: bool = False


class AddressUpdate(BaseModel):
    address_line: Optional[str] = Field(
        None,
        min_length=5,
        max_length=255
    )
    city: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100
    )
    pincode: Optional[str] = Field(
        None,
        min_length=4,
        max_length=10
    )
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_type: Optional[str] = Field(
        None,
        max_length=30
    )
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    id: int
    customer_id: int
    address_line: str
    city: str
    pincode: str
    latitude: Optional[float]
    longitude: Optional[float]
    address_type: str
    is_default: bool

    class Config:
        from_attributes = True


class CustomerWithAddresses(CustomerResponse):
    addresses: list[AddressResponse] = []