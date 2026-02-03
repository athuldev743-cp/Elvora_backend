# app/routes/payments.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.razorpay_client import client

router = APIRouter(prefix="/payments", tags=["payments"])

class CreateOrderIn(BaseModel):
    amount: float  # rupees

@router.post("/create-razorpay-order")
def create_razorpay_order(payload: CreateOrderIn):
    order = client.order.create({
        "amount": int(payload.amount * 100),  # rupees → paise
        "currency": "INR",
        "payment_capture": 1
    })
    return order
