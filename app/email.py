# app/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")  # app password

def send_order_confirmation_email(to_email, customer_name, order_id, product_name, total_amount):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL / SMTP_APP_PASSWORD missing in env")

    subject = "✅ Your EkaBhumi Order is Confirmed"
    body = f"""Hi {customer_name},

Your order has been confirmed 🎉

Order ID: #{order_id}
Product: {product_name}
Total Amount: ₹{total_amount:.2f}

Thank you for choosing EkaBhumi 🌿
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
