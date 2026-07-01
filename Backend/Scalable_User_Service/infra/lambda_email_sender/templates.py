from datetime import datetime

def get_base_html(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #080810;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #e2e8f0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            .card {{
                background-color: #111118;
                border: 1px solid #2a2a35;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 32px;
                letter-spacing: -0.5px;
            }}
            .logo span {{
                color: #3b82f6;
            }}
            .heading {{
                font-size: 22px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 16px;
            }}
            .text {{
                font-size: 16px;
                line-height: 1.6;
                color: #94a3b8;
                margin-bottom: 24px;
            }}
            .otp-box {{
                background-color: #080810;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 16px 24px;
                font-size: 32px;
                font-weight: 700;
                color: #3b82f6;
                letter-spacing: 6px;
                margin: 32px auto;
                display: inline-block;
            }}
            .footer {{
                margin-top: 32px;
                font-size: 12px;
                color: #475569;
                text-align: center;
                line-height: 1.5;
            }}
            .button {{
                display: inline-block;
                background-color: #3b82f6;
                color: #ffffff;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-weight: 600;
                margin-top: 16px;
                font-size: 15px;
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #080810;">
            <tr>
                <td align="center">
                    <div class="container">
                        <div class="card">
                            <div class="logo">ThinkAloud<span>.AI</span></div>
                            {content}
                        </div>
                        <div class="footer">
                            &copy; {datetime.now().year} ThinkAloudAI. All rights reserved.<br>
                            If you did not request this email, you can safely ignore it.
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
        <a href="https://thinkaloudai.tech" class="button">Start Practicing Now</a>
    """
    return get_base_html(content)

def get_verification_email_html(otp: str) -> str:
    content = f"""
        <div class="heading">Verify your email address</div>
        <div class="text">
            To complete your registration, please enter the following verification code in the app. This code will expire in 15 minutes.
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
