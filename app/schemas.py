# app/schemas.py - Complete version
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# -------- Google Auth Input --------
class GoogleAuthRequest(BaseModel):
    id_token: str   # token received from Google frontend

# -------- User Output --------
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        orm_mode = True

# -------- Auth Response --------
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# -------- Optional: Admin Creation --------
class AdminCreate(BaseModel):
    name: str
    email: str

# -------- Product Schemas --------
class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    priority: Optional[int] = 100

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    priority: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# -------- Order Schemas --------
class OrderBase(BaseModel):
    product_id: int
    product_name: str
    quantity: int = 1
    unit_price: float
    total_amount: float
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    notes: Optional[str] = None
    status: Optional[str] = "pending"
    payment_status: Optional[str] = "pending"

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None

class OrderResponse(OrderBase):
    id: int
    order_date: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True