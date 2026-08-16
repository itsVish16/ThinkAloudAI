import logging
from datetime import datetime
from typing import Any, Dict, Optional
import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


def get_base_html(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0; padding: 0; background-color: #080810;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #f3f4f6;
            }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{
                background-color: #12121a; 
                border: 1px solid #1f1f2e;
                border-radius: 12px; padding: 48px 40px; text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            }}
            .logo-text {{
                font-size: 26px; font-weight: 800; color: #ffffff;
                letter-spacing: -0.5px; text-decoration: none; display: inline-block; margin-bottom: 24px;
            }}
            .logo-text span {{ color: #FF6B00; }}
            .heading {{
                font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 16px;
            }}
            .text {{
                font-size: 15px; line-height: 1.6; color: #a0a0b0; margin-bottom: 28px;
            }}
            .otp-box {{
                background-color: #080810; border: 1px solid #333344;
                border-radius: 8px; padding: 16px 28px; font-size: 32px;
                font-family: 'Courier New', Courier, monospace;
                font-weight: 700; color: #FF6B00; letter-spacing: 8px;
                margin: 20px auto; display: inline-block;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }}
            .footer {{
                margin-top: 36px; font-size: 13px; color: #9ca3af; text-align: center; line-height: 1.6;
            }}
            .footer a {{ color: #FF6B00; text-decoration: none; }}
            .button {{
                display: inline-block; background: #FF6B00;
                color: #ffffff !important; text-decoration: none; padding: 12px 28px;
                border-radius: 8px; font-weight: 600; font-size: 15px;
                box-shadow: 0 4px 15px rgba(255, 107, 0, 0.3);
            }}
        </style>
    </head>
    <body style="background-color: #080810;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #080810;">
            <tr>
                <td align="center">
                    <div class="container">
                        <div class="card">
                            <div class="logo-text">ThinkAloud<span>.ai</span></div>
                            {content}
                        </div>
                        <div class="footer">
                            &copy; {datetime.now().year} ThinkAloudAI. All rights reserved.<br>
                            Need assistance? Contact <a href="mailto:support@thinkaloudai.tech">support@thinkaloudai.tech</a>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def get_verification_email_html(otp: str) -> str:
    content = f"""
        <div class="heading">Verify your email address ✉️</div>
        <div class="text">
            To finish setting up your account, please enter the following 6-digit verification code. This code expires in 15 minutes.
        </div>
        <div class="otp-box">{otp}</div>
        <div class="text" style="font-size: 13px; margin-top: 20px; color: #71717a;">
            If you did not request this code, you can safely ignore this email.
        </div>
    """
    return get_base_html(content)


def get_password_reset_email_html(otp: str) -> str:
    content = f"""
        <div class="heading">Reset your password 🔐</div>
        <div class="text">
            We received a request to reset your password. Use the following code to complete your password reset:
        </div>
        <div class="otp-box">{otp}</div>
        <div class="text" style="font-size: 13px; margin-top: 20px; color: #71717a;">
            If you did not request a password reset, your account is secure and you can disregard this email.
        </div>
    """
    return get_base_html(content)


def get_welcome_email_html(full_name: str) -> str:
    content = f"""
        <div class="heading">Welcome to ThinkAloudAI, {full_name or 'there'}! 🎉</div>
        <div class="text">
            Your email has been verified. You can now practice real-time coding and system design mock interviews with our AI interviewer.
        </div>
        <a href="{settings.frontend_base_url}" class="button">Start Practicing</a>
    """
    return get_base_html(content)


async def send_email_via_resend(to_email: str, subject: str, html_content: str) -> Optional[Dict[str, Any]]:
    """
    Sends an email using Resend's REST API asynchronously via httpx.
    """
    api_key = settings.resend_api_key.strip() if settings.resend_api_key else ""
    from_email = settings.email_from or "onboarding@resend.dev"

    if not settings.email_delivery_enabled or not api_key:
        logger.info(
            "email_delivery_simulated",
            to_email=to_email,
            subject=subject,
            delivery_enabled=settings.email_delivery_enabled,
        )
        return {"status": "simulated", "to": to_email}

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            logger.info("email_sent_successfully", message_id=data.get("id"), to=to_email, subject=subject)
            return data
    except Exception as e:
        logger.error("email_send_failed", error=str(e), to=to_email, subject=subject)
        raise e


async def process_email(task_type: str, to_email: str, payload: dict) -> None:
    """
    Renders appropriate HTML template and sends the email.
    """
    otp = payload.get("otp", "")
    full_name = payload.get("full_name", "")

    if task_type == "verification_email":
        subject = f"Your ThinkAloudAI verification code: {otp}"
        html = get_verification_email_html(otp)
    elif task_type == "password_reset_email":
        subject = f"Your ThinkAloudAI password reset code: {otp}"
        html = get_password_reset_email_html(otp)
    elif task_type == "welcome_email":
        subject = "Welcome to ThinkAloudAI!"
        html = get_welcome_email_html(full_name)
    else:
        logger.warning("unknown_email_task_type", task_type=task_type, to=to_email)
        return

    await send_email_via_resend(to_email, subject, html)
