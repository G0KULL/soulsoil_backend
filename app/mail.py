import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timezone

# Explicitly load .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

print(f"DEBUG: Mail Config - Username: {MAIL_USERNAME}, Password Configured: {'Yes' if MAIL_PASSWORD else 'No'}")

async def send_email(email: str, subject: str, html_content: str):
    """
    Sends an HTML email to the specified address.
    """
    if not MAIL_PASSWORD or MAIL_USERNAME == "your-email@gmail.com":
        print(f"DEBUG: Email sending is not configured. Target: {email}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = f"SoulSoil <{MAIL_USERNAME}>"
        msg['To'] = email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email to {email}: {e}")
        return False

async def send_otp_email(email: str, otp: str, type: str = "verification"):
    """
    Sends an OTP email for either verification or password reset.
    """
    subjects = {
        "verification": f"{otp} is your SoulSoil verification code",
        "password_reset": f"{otp} is your SoulSoil reset code"
    }
    
    titles = {
        "verification": "Account Verification",
        "password_reset": "Password Reset Request"
    }
    
    messages = {
        "verification": "To complete your registration, please use the following code:",
        "password_reset": "We received a request to reset your password. Use the following code to proceed:"
    }

    subject = subjects.get(type, subjects["verification"])
    title = titles.get(type, titles["verification"])
    message = messages.get(type, messages["verification"])

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #3b82f6;">{title}</h2>
                <p>Hello,</p>
                <p>{message}</p>
                <div style="background: #f3f4f6; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #1e3a8a; border-radius: 8px; margin: 20px 0;">
                    {otp}
                </div>
                <p>This code will expire in 10 minutes. If you didn't request this, you can safely ignore this email.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                <p style="font-size: 12px; color: #6b7280;">SoulSoil Team - Sustainable Agricultural Ecosystem</p>
            </div>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content)
