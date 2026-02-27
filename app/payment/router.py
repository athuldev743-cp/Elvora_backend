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

BASE_URL     = os.getenv("INSTAMOJO_BASE_URL", "https://www.instamojo.com/api/1.1/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL  = os.getenv("BACKEND_URL",  "http://localhost:8000")


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
# 1. CREATE PAYMENT
# ─────────────────────────────────────────────────────
@router.post("/payment/create")
def create_payment(data: PaymentInitRequest, db: Session = Depends(get_db)):
    api_key    = os.getenv("INSTAMOJO_API_KEY")
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")

    if not api_key or not auth_token:
        raise HTTPException(status_code=500, detail="Instamojo credentials not configured")

    headers = {
        "X-Api-Key":    api_key,
        "X-Auth-Token": auth_token,
    }

    # Save pending order first to get an order ID
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

    # Clean phone — Instamojo needs exactly 10 digits
    clean_phone = data.customer_phone.replace("+91", "").replace(" ", "").strip()

    # Unique purpose to avoid Instamojo duplicate rejection
    unique_purpose = f"Order #{order.id} - {datetime.utcnow().strftime('%f')}"

    payload = {
        "purpose":                 unique_purpose,
        "amount":                  f"{data.total_amount:.2f}",
        "buyer_name":              data.customer_name,
        "email":                   data.customer_email,
        "phone":                   clean_phone,
        "redirect_url":            f"{BACKEND_URL.rstrip('/')}/api/payment/callback?order_id={order.id}",
        "webhook":                 f"{BACKEND_URL.rstrip('/')}/api/payment/webhook",
        "send_email":              "True",
        "send_sms":                "True",
        "allow_repeated_payments": "True",
    }

    print(f"[PAYMENT] Creating order={order.id} amount={payload['amount']} phone={clean_phone}")

    try:
        response = requests.post(
            f"{BASE_URL}payment-requests/",
            data=payload,
            headers=headers
        )
        res_data = response.json()
    except Exception as e:
        db.delete(order)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Instamojo connection error: {str(e)}")

    if not res_data.get("success"):
        print(f"[PAYMENT] Instamojo rejected: {res_data}")
        db.delete(order)
        db.commit()
        raise HTTPException(status_code=400, detail=res_data)

    payment_request_id = res_data["payment_request"]["id"]
    payment_url        = res_data["payment_request"]["longurl"]

    order.notes = f"{order.notes}\n[INSTAMOJO] request_id={payment_request_id}".strip()
    db.commit()

    print(f"[PAYMENT] ✅ Created payment_request_id={payment_request_id}")

    return {
        "success":            True,
        "payment_url":        payment_url,
        "payment_request_id": payment_request_id,
        "order_id":           order.id,
    }


# ─────────────────────────────────────────────────────
# 2. CALLBACK — Instamojo redirects user here after payment
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

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        print(f"[CALLBACK] Order {order_id} not found")
        return RedirectResponse(url=f"{FRONTEND_URL}/?payment=failed&reason=order_not_found")

    try:
        response = requests.get(
            f"{BASE_URL}payment-requests/{payment_request_id}/{payment_id}/",
            headers=headers
        )
        res_data = response.json()
        print(f"[CALLBACK] Instamojo response: {res_data}")
    except Exception as e:
        print(f"[CALLBACK] Error verifying: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?payment=failed&reason=verification_error")

    payment = res_data.get("payment_request", {}).get("payment", {})
    status  = payment.get("status", "")

    print(f"[CALLBACK] payment_id={payment_id} status={status}")

    if status == "Credit":
        order.payment_status = "paid"
        order.status         = "confirmed"
        order.notes          = f"{order.notes}\n[PAID] payment_id={payment_id}".strip()
        order.updated_at     = datetime.utcnow()
        db.commit()
        print(f"[CALLBACK] ✅ Order {order_id} confirmed")
        return RedirectResponse(url=f"{FRONTEND_URL}/account?payment=success")
    else:
        order.payment_status = "failed"
        order.status         = "cancelled"
        order.updated_at     = datetime.utcnow()
        db.commit()
        print(f"[CALLBACK] ❌ Order {order_id} failed status={status}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?payment=failed")


# ─────────────────────────────────────────────────────
# 3. WEBHOOK — Instamojo POSTs here in background
# ─────────────────────────────────────────────────────
@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    form_data  = await request.form()
    data       = dict(form_data)
    auth_token = os.getenv("INSTAMOJO_AUTH_TOKEN")

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

    print(f"[WEBHOOK] status={payment_status} payment_id={payment_id} email={buyer_email} amount=₹{amount}")

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
            print(f"[WEBHOOK] ✅ Order {order.id} marked as paid")

    return {"status": "ok"}