# app/routes/payments.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.razorpay_client import client

router = APIRouter(prefix="/payments", tags=["payments"])

class CreateOrderIn(BaseModel):
    amount: float  # rupees

@router.post("/create-razorpay-order")
def create_razorpay_order(payload: CreateOrderIn):
    order = client.order.create({
        "amount": int(round(payload.amount * 100)),  # rupees -> paise
        "currency": "INR",
        "payment_capture": 1
    })
    return order

class VerifyPaymentIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/verify")
def verify_payment(payload: VerifyPaymentIn):
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": payload.razorpay_order_id,
            "razorpay_payment_id": payload.razorpay_payment_id,
            "razorpay_signature": payload.razorpay_signature,
        })
        return {"ok": True}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment signature")