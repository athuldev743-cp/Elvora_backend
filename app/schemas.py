# app/schemas.py - For Pydantic v1
from pydantic import BaseModel, EmailStr
from typing import Optional

# -------- Google Auth Input --------
class GoogleAuthRequest(BaseModel):
    id_token: str   # token received from Google frontend

# -------- User Output --------
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True  # Use orm_mode for Pydantic v1

# -------- Auth Response --------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# -------- Product Schemas --------
class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    priority: Optional[int] = 100

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    
    class Config:
        orm_mode = True  # Use orm_mode for Pydantic v1

# -------- Order Schemas --------
class OrderBase(BaseModel):
    user_email: str
    product_name: str
    quantity: Optional[int] = 1
    total_price: Optional[float] = 0

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    status: str
    
    class Config:
        orm_mode = True  # Use orm_mode for Pydantic v1