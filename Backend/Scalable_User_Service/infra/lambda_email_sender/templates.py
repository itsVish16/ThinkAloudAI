from datetime import datetime

def get_base_html(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
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
            .logo-container {{
                margin-bottom: 40px;
            }}
            .logo-text {{
                font-family: 'Outfit', sans-serif;
                font-size: 28px; font-weight: 800; color: #ffffff;
                letter-spacing: -0.5px; text-decoration: none;
            }}
            .logo-text span {{ color: #FF6B00; }}
            .heading {{
                font-family: 'Outfit', sans-serif;
                font-size: 24px; font-weight: 700; color: #ffffff; margin-bottom: 16px;
            }}
            .text {{
                font-size: 16px; line-height: 1.6; color: #a0a0b0; margin-bottom: 32px;
            }}
            .otp-box {{
                background-color: #080810; border: 1px solid #333344;
                border-radius: 8px; padding: 20px 32px; font-size: 36px;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 700; color: #fff; letter-spacing: 12px;
                margin: 24px auto; display: inline-block;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            }}
            .footer {{
                margin-top: 40px; font-size: 13px; color: #9ca3af; text-align: center; line-height: 1.6;
            }}
            .footer a {{ color: #FF6B00; text-decoration: none; }}
            .button {{
                display: inline-block; background: #FF6B00;
                color: #ffffff; text-decoration: none; padding: 12px 28px;
                border-radius: 8px; font-weight: 600; font-size: 15px;
                box-shadow: 0 4px 15px rgba(255, 107, 0, 0.2);
            }}
        </style>
    </head>
    <body style="background-color: #080810;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #080810;">
            <tr>
                <td align="center">
                    <div class="container">
                        <div class="card">
                            <div class="logo-container">
                                <img src="https://thinkaloudai.tech/logo.png" height="40" alt="ThinkAloud.AI" style="display: block; margin: 0 auto;">
                            </div>
                            {content}
                        </div>
                        <div class="footer">
                            &copy; {datetime.now().year} ThinkAloudAI. All rights reserved.<br>
                            Need help? Contact us at <a href="mailto:support@thinkaloudai.tech">support@thinkaloudai.tech</a><br>
                            <span style="font-size: 11px; margin-top: 8px; display: block;">If you didn't request this, you can safely ignore this email.</span>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_welcome_email_html(full_name: str) -> str:
    content = f"""
        <div class="heading">Welcome to the future of interviewing, {full_name}!</div>
        <div class="text">
            We are thrilled to have you on board. ThinkAloudAI is designed to help you master Data Structures, Algorithms, and System Design through interactive, AI-driven mock interviews.
        </div>
        <a href="https://thinkaloudai.tech" class="button" style="color: white; text-decoration: none;">Start Practicing Now</a>
    """
    return get_base_html(content)

def get_verification_email_html(otp: str) -> str:
    content = f"""
        <div class="heading">Verify your email address</div>
        <div class="text">
            To complete your registration, please enter the following verification code. This code will expire in 15 minutes.
        </div>
        <div class="otp-box">{otp}</div>
    """
    return get_base_html(content)

def get_password_reset_email_html(otp: str) -> str:
    content = f"""
        <div class="heading">Reset your password</div>
        <div class="text">
            We received a request to reset your password. Enter the code below to securely change it. This code will expire in 15 minutes.
        </div>
        <div class="otp-box">{otp}</div>
    """
    return get_base_html(content)
