import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "EkaBhumi <onboarding@resend.dev>")  # or your verified sender

def send_order_confirmation_email(to_email, customer_name, order_id, product_name, total_amount):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY missing in env")

    subject = "✅ Your EkaBhumi Order is Confirmed"
    body = f"""Hi {customer_name},

Your order has been confirmed 🎉

Order ID: #{order_id}
Product: {product_name}
Total Amount: ₹{total_amount:.2f}

Thank you for choosing EkaBhumi 🌿
"""

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": body,
        },
        timeout=20,
    )

    if resp.status_code >= 300:
        raise RuntimeError(f"Resend failed: {resp.status_code} {resp.text}")
