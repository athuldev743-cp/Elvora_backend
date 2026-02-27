# app/payment/router.py
import hmac
import hashlib
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Order
import os

router = APIRouter()

# ── Credentials from .env ──
BASE_URL     = os.getenv("INSTAMOJO_BASE_URL", "https://www.instamojo.com/api/1.1/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")



# ── Request schema from Buy.jsx ──
class PaymentInitRequest(BaseModel):
    product_id:       int
    product_name:     str
    quantity:         int
    unit_price:       float
    total_amount:     float
    customer_name:    str
    customer_email:   str
    customer_phone:   str
    shipping_address: str
    notes:            str = ""


# ─────────────────────────────────────────────────────
# 1. CREATE PAYMENT REQUEST
#    Frontend calls this → gets back a payment_url
#    Buy.jsx does: window.location.href = payment_url
# ─────────────────────────────────────────────────────
@router.post("/payment/create")
def create_payment(data: PaymentInitRequest, db: Session = Depends(get_db)):
    # Read fresh from env every request (fixes None on Render)
    api_key    = os.getenv("INSTAMOJO_API_KEY")
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")

    if not api_key or not auth_token:
        raise HTTPException(status_code=500, detail="Instamojo credentials not configured in .env")

    headers = {
        "X-Api-Key":    api_key,
        "X-Auth-Token": auth_token,
    }
    print(f"[PAYMENT] Key loaded: {api_key[:6]}... Token loaded: {auth_token[:6]}...")

    # Save a PENDING order to DB first so we have an order_id
    order = Order(
        product_id       = data.product_id,
        product_name     = data.product_name,
        quantity         = data.quantity,
        unit_price       = data.unit_price,
        total_amount     = data.total_amount,
        customer_name    = data.customer_name,
        customer_email   = data.customer_email,
        customer_phone   = data.customer_phone,
        shipping_address = data.shipping_address,
        notes            = data.notes or "",
        status           = "pending",
        payment_status   = "pending",
        order_date       = datetime.utcnow(),
        updated_at       = datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Clean phone — Instamojo needs exactly 10 digits, no +91 or spaces
    clean_phone = data.customer_phone.replace("+91", "").replace(" ", "").strip()

    # Backend URL for callbacks
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Create payment request on Instamojo
    payload = {
        "purpose":                 f"Order #{order.id} - {data.product_name}",
        "amount":                  f"{data.total_amount:.2f}",
        "buyer_name":              data.customer_name,
        "email":                   data.customer_email,
        "phone":                   clean_phone,
        "redirect_url":            f"{BACKEND_URL.rstrip('/')}/api/payment/callback?order_id={order.id}",
        "webhook":                 f"{BACKEND_URL.rstrip('/')}/api/payment/webhook",
        "send_email":              "True",
        "send_sms":                "True",
        "allow_repeated_payments": "False",
    }
    print(f"[PAYMENT] Instamojo payload: amount={payload['amount']} phone={clean_phone} redirect={payload['redirect_url']}")

    try:
        response = requests.post(
            f"{BASE_URL}payment-requests/",
            data=payload,
            headers=headers
        )
        res_data = response.json()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Instamojo connection error: {str(e)}")

    if not res_data.get("success"):
    # Clean up the pending order if Instamojo rejected
     db.delete(order)
    db.commit()
    print(f"[PAYMENT] Instamojo rejected: {res_data}")  # ← BEFORE raise
    raise HTTPException(status_code=400, detail=res_data)
    

    payment_request_id = res_data["payment_request"]["id"]
    payment_url        = res_data["payment_request"]["longurl"]

    # Save the Instamojo payment_request_id in notes for reference
    order.notes = f"{order.notes}\n[INSTAMOJO] request_id={payment_request_id}".strip()
    db.commit()

    return {
        "success":            True,
        "payment_url":        payment_url,
        "payment_request_id": payment_request_id,
        "order_id":           order.id,
    }


# ─────────────────────────────────────────────────────
# 2. CALLBACK — Instamojo redirects user here after payment
#    Verifies payment → updates order → sends user to frontend
# ─────────────────────────────────────────────────────
@router.get("/payment/callback")
def payment_callback(
    payment_id:         str,
    payment_request_id: str,
    order_id:           int,
    db:                 Session = Depends(get_db)
):
    api_key    = os.getenv("INSTAMOJO_API_KEY")
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")
    headers    = {"X-Api-Key": api_key, "X-Auth-Token": auth_token}

    # Find the pending order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url=f"{FRONTEND_URL}/?payment=failed&reason=order_not_found")

    # Verify payment status with Instamojo
    try:
        response = requests.get(
            f"{BASE_URL}payment-requests/{payment_request_id}/{payment_id}/",
            headers=headers
        )
        res_data = response.json()
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/?payment=failed&reason=verification_error")

    payment = res_data.get("payment_request", {}).get("payment", {})
    status  = payment.get("status", "")

    if status == "Credit":
        # ✅ Payment successful — update order
        order.payment_status = "paid"
        order.status         = "confirmed"
        order.notes          = f"{order.notes}\n[PAID] payment_id={payment_id}".strip()
        order.updated_at     = datetime.utcnow()
        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/account?payment=success"
        )
    else:
        # ❌ Payment failed — update order
        order.payment_status = "failed"
        order.status         = "cancelled"
        order.updated_at     = datetime.utcnow()
        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/?payment=failed"
        )


# ─────────────────────────────────────────────────────
# 3. WEBHOOK — Instamojo POSTs here silently in background
#    Extra safety net to update payment status
# ─────────────────────────────────────────────────────
@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    data      = dict(form_data)

    # Read fresh from env
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")

    # Verify MAC signature
    mac_provided = data.pop("mac", None)
    if mac_provided and auth_token:
        message        = "|".join(str(data[k]) for k in sorted(data.keys()))
        mac_calculated = hmac.new(
            auth_token.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha1
        ).hexdigest()

        if mac_provided != mac_calculated:
            raise HTTPException(status_code=403, detail="Invalid MAC signature")

    payment_status = data.get("status")
    payment_id     = data.get("payment_id")
    buyer_email    = data.get("buyer")
    amount         = data.get("amount")

    print(f"[WEBHOOK] status={payment_status} | payment_id={payment_id} | email={buyer_email} | amount=₹{amount}")

    # Find order by email + amount as fallback update
    if payment_status == "Credit" and buyer_email:
        order = (
            db.query(Order)
            .filter(
                Order.customer_email == buyer_email,
                Order.payment_status == "pending"
            )
            .order_by(Order.order_date.desc())
            .first()
        )
        if order:
            order.payment_status = "paid"
            order.status         = "confirmed"
            order.notes          = f"{order.notes}\n[WEBHOOK] payment_id={payment_id}".strip()
            order.updated_at     = datetime.utcnow()
            db.commit()
            print(f"✅ [WEBHOOK] Order {order.id} marked as paid")

    return {"status": "ok"}