import logging
from datetime import datetime
from typing import Any, Dict, Optional
import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


def get_base_html(content: str, preview_text: str = "") -> str:
    current_year = datetime.now().year
    app_url = settings.frontend_base_url.rstrip("/") if settings.frontend_base_url else "https://thinkaloudai.tech"

    return f"""<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <!--[if mso]>
    <xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
    <![endif]-->
    <title>ThinkAloudAI</title>
    <style>
        body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
        table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
        img {{ -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
        body {{
            margin: 0 !important;
            padding: 0 !important;
            background-color: #07070D !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #E2E8F0;
        }}
        @media only screen and (max-width: 620px) {{
            .email-container {{ width: 100% !important; padding: 16px 8px !important; }}
            .content-card {{ padding: 28px 20px !important; }}
            .otp-code {{ font-size: 30px !important; letter-spacing: 6px !important; padding: 14px 20px !important; }}
            .feature-col {{ display: block !important; width: 100% !important; margin-bottom: 12px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #07070D; color: #E2E8F0;">
    <!-- Hidden Preheader text -->
    <div style="display: none; font-size: 1px; color: #07070D; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        {preview_text}
    </div>

    <!-- Main Wrapper Table -->
    <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#07070D" style="background-color: #07070D;">
        <tr>
            <td align="center" style="padding: 36px 12px;">
                <!-- Container (600px max) -->
                <table class="email-container" width="100%" border="0" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto;">
                    
                    <!-- BRAND HEADER -->
                    <tr>
                        <td align="center" style="padding-bottom: 28px;">
                            <table border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <a href="{app_url}" target="_blank" style="text-decoration: none; display: inline-block;">
                                            <table border="0" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="background: linear-gradient(135deg, #FF6B00 0%, #FF8533 100%); padding: 1px; border-radius: 12px;">
                                                        <div style="background: #0E0E17; border-radius: 11px; padding: 10px 20px; display: inline-block;">
                                                            <span style="font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">ThinkAloud<span style="color: #FF6B00;">.ai</span></span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            </table>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- MAIN CARD -->
                    <tr>
                        <td>
                            <table class="content-card" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #0F0F1A; border: 1px solid #1E1E2E; border-radius: 16px; padding: 40px 36px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);">
                                <tr>
                                    <td>
                                        {content}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                        <td align="center" style="padding-top: 32px; padding-bottom: 24px; text-align: center;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" style="padding-bottom: 16px;">
                                        <a href="{app_url}" style="color: #94A3B8; text-decoration: none; font-size: 13px; font-weight: 500; margin: 0 10px;">Platform</a>
                                        <span style="color: #334155;">&bull;</span>
                                        <a href="{app_url}/practice" style="color: #94A3B8; text-decoration: none; font-size: 13px; font-weight: 500; margin: 0 10px;">DSA Practice</a>
                                        <span style="color: #334155;">&bull;</span>
                                        <a href="{app_url}/roadmaps" style="color: #94A3B8; text-decoration: none; font-size: 13px; font-weight: 500; margin: 0 10px;">Roadmaps</a>
                                        <span style="color: #334155;">&bull;</span>
                                        <a href="mailto:support@thinkaloudai.tech" style="color: #FF6B00; text-decoration: none; font-size: 13px; font-weight: 500; margin: 0 10px;">Support</a>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="font-size: 12px; line-height: 1.6; color: #64748B;">
                                        &copy; {current_year} ThinkAloudAI. The AI-Powered Technical Interview & Practice Platform.<br>
                                        You received this automated transactional message for your ThinkAloudAI account.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def get_verification_email_html(otp: str) -> str:
    preview = f"Your ThinkAloudAI verification code is {otp}. It expires in 15 minutes."
    content = f"""
        <!-- Badge -->
        <table border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 18px;">
            <tr>
                <td style="background-color: rgba(255, 107, 0, 0.12); border: 1px solid rgba(255, 107, 0, 0.3); border-radius: 20px; padding: 4px 14px;">
                    <span style="color: #FF8533; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Account Verification</span>
                </td>
            </tr>
        </table>

        <!-- Heading -->
        <h1 style="margin: 0 0 12px 0; font-size: 24px; font-weight: 700; color: #FFFFFF; line-height: 1.3;">
            Verify your email address ✉️
        </h1>

        <!-- Subtitle -->
        <p style="margin: 0 0 28px 0; font-size: 15px; line-height: 1.6; color: #94A3B8;">
            Welcome to <strong style="color: #FFFFFF;">ThinkAloudAI</strong>! Please enter the 6-digit verification code below in your browser to activate your account and start practicing.
        </p>

        <!-- OTP Display Box -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin: 28px 0;">
            <tr>
                <td align="center">
                    <div style="background: #07070D; border: 1px solid #2D2D42; border-radius: 12px; padding: 20px 32px; display: inline-block; box-shadow: inset 0 2px 8px rgba(0,0,0,0.6);">
                        <div class="otp-code" style="font-family: 'SF Mono', Monaco, 'Courier New', monospace; font-size: 36px; font-weight: 800; color: #FF6B00; letter-spacing: 10px; text-indent: 10px;">
                            {otp}
                        </div>
                    </div>
                </td>
            </tr>
            <tr>
                <td align="center" style="padding-top: 12px;">
                    <span style="font-size: 12px; color: #64748B;">⏱️ Valid for <strong style="color: #94A3B8;">15 minutes</strong>. Do not share this code.</span>
                </td>
            </tr>
        </table>

        <!-- Features Teaser -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #141422; border-radius: 12px; padding: 20px; margin-top: 24px; border: 1px solid #1E1E2E;">
            <tr>
                <td style="padding-bottom: 12px;">
                    <strong style="color: #F8FAFC; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">What you can do with ThinkAloudAI:</strong>
                </td>
            </tr>
            <tr>
                <td style="font-size: 13px; line-height: 1.8; color: #94A3B8;">
                    🎙️ <strong style="color: #E2E8F0;">Voice AI Interviewer</strong>: Realistic spoken technical & behavioral mock rounds.<br>
                    💻 <strong style="color: #E2E8F0;">Monaco DSA IDE</strong>: 30+ curated algorithm problems with real-time test judging.<br>
                    🏗️ <strong style="color: #E2E8F0;">System Design Studio</strong>: Visual diagram grading and scalability feedback.
                </td>
            </tr>
        </table>

        <!-- Security Disclaimer -->
        <p style="margin: 24px 0 0 0; font-size: 12px; line-height: 1.5; color: #64748B; text-align: center;">
            If you did not sign up for ThinkAloudAI, you can safely disregard this email.
        </p>
    """
    return get_base_html(content, preview_text=preview)


def get_password_reset_email_html(otp: str) -> str:
    preview = f"Your ThinkAloudAI password reset code is {otp}. It expires in 15 minutes."
    content = f"""
        <!-- Badge -->
        <table border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 18px;">
            <tr>
                <td style="background-color: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 20px; padding: 4px 14px;">
                    <span style="color: #F87171; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Security & Password</span>
                </td>
            </tr>
        </table>

        <!-- Heading -->
        <h1 style="margin: 0 0 12px 0; font-size: 24px; font-weight: 700; color: #FFFFFF; line-height: 1.3;">
            Reset your password 🔐
        </h1>

        <!-- Subtitle -->
        <p style="margin: 0 0 28px 0; font-size: 15px; line-height: 1.6; color: #94A3B8;">
            We received a request to reset the password for your <strong style="color: #FFFFFF;">ThinkAloudAI</strong> account. Use the 6-digit code below to set a new password.
        </p>

        <!-- OTP Display Box -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin: 28px 0;">
            <tr>
                <td align="center">
                    <div style="background: #07070D; border: 1px solid #2D2D42; border-radius: 12px; padding: 20px 32px; display: inline-block; box-shadow: inset 0 2px 8px rgba(0,0,0,0.6);">
                        <div class="otp-code" style="font-family: 'SF Mono', Monaco, 'Courier New', monospace; font-size: 36px; font-weight: 800; color: #FF6B00; letter-spacing: 10px; text-indent: 10px;">
                            {otp}
                        </div>
                    </div>
                </td>
            </tr>
            <tr>
                <td align="center" style="padding-top: 12px;">
                    <span style="font-size: 12px; color: #64748B;">⏱️ Valid for <strong style="color: #94A3B8;">15 minutes</strong>. Never share this code with anyone.</span>
                </td>
            </tr>
        </table>

        <!-- Security Warning -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 18px; margin-top: 24px;">
            <tr>
                <td style="font-size: 13px; line-height: 1.6; color: #CBD5E1;">
                    🛡️ <strong style="color: #F87171;">Did not request a password reset?</strong><br>
                    Your account is secure. You can safely ignore this email — your existing password will remain unchanged.
                </td>
            </tr>
        </table>
    """
    return get_base_html(content, preview_text=preview)


def get_welcome_email_html(full_name: str) -> str:
    app_url = settings.frontend_base_url.rstrip("/") if settings.frontend_base_url else "https://thinkaloudai.tech"
    name = full_name.strip() if full_name else "there"
    preview = f"Welcome to ThinkAloudAI, {name}! Your account is ready for AI mock interviews."

    content = f"""
        <!-- Badge -->
        <table border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 18px;">
            <tr>
                <td style="background-color: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 20px; padding: 4px 14px;">
                    <span style="color: #4ADE80; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Account Ready</span>
                </td>
            </tr>
        </table>

        <!-- Heading -->
        <h1 style="margin: 0 0 12px 0; font-size: 26px; font-weight: 800; color: #FFFFFF; line-height: 1.3;">
            Welcome to ThinkAloudAI, {name}! 🚀
        </h1>

        <!-- Subtitle -->
        <p style="margin: 0 0 28px 0; font-size: 15px; line-height: 1.6; color: #94A3B8;">
            Your email has been verified. You're all set to prepare for technical interviews with our low-latency AI interviewer and interactive practice workspace.
        </p>

        <!-- Feature Cards -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 28px;">
            <tr>
                <td style="padding-bottom: 12px;">
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background: #141422; border: 1px solid #1E1E2E; border-radius: 12px; padding: 16px;">
                        <tr>
                            <td width="36" valign="top" style="font-size: 22px;">🎙️</td>
                            <td style="padding-left: 12px;">
                                <strong style="color: #FFFFFF; font-size: 14px;">Real-Time Voice Mock Interviews</strong>
                                <p style="margin: 4px 0 0 0; font-size: 13px; color: #94A3B8; line-height: 1.5;">
                                    Converse naturally with Aarav, your AI interviewer. Practice DSA, System Design, and Behavioral rounds with live feedback.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="padding-bottom: 12px;">
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background: #141422; border: 1px solid #1E1E2E; border-radius: 12px; padding: 16px;">
                        <tr>
                            <td width="36" valign="top" style="font-size: 22px;">⚡</td>
                            <td style="padding-left: 12px;">
                                <strong style="color: #FFFFFF; font-size: 14px;">Curated DSA Platform & Monaco IDE</strong>
                                <p style="margin: 4px 0 0 0; font-size: 13px; color: #94A3B8; line-height: 1.5;">
                                    Write Python & C++ solutions with instant sandbox test execution, edge case checks, and complexity analysis.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td>
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background: #141422; border: 1px solid #1E1E2E; border-radius: 12px; padding: 16px;">
                        <tr>
                            <td width="36" valign="top" style="font-size: 22px;">🗺️</td>
                            <td style="padding-left: 12px;">
                                <strong style="color: #FFFFFF; font-size: 14px;">Personalized Learning Roadmaps</strong>
                                <p style="margin: 4px 0 0 0; font-size: 13px; color: #94A3B8; line-height: 1.5;">
                                    Generate customized week-by-week study roadmaps tailored to your dream company and target seniority level.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Primary CTA Button -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin: 32px 0 16px 0;">
            <tr>
                <td align="center">
                    <a href="{app_url}/dashboard" target="_blank" style="background: linear-gradient(135deg, #FF6B00 0%, #FF8533 100%); color: #FFFFFF; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 36px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 20px rgba(255, 107, 0, 0.4); letter-spacing: 0.2px;">
                        Start Practicing Now &rarr;
                    </a>
                </td>
            </tr>
        </table>
    """
    return get_base_html(content, preview_text=preview)


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
