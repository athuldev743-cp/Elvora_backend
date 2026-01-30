# app/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def send_order_confirmation_email(to_email, customer_name, order_id, product_name, total_amount):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")  # Gmail app password

    if not smtp_email or not smtp_password:
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
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
