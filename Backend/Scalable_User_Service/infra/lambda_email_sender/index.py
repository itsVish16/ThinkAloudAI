import json
import os
import resend
from templates import get_welcome_email_html, get_verification_email_html, get_password_reset_email_html

resend.api_key = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("EMAIL_FROM", "noreply@thinkaloudai.tech")

def handler(event, context):
    """
    AWS Lambda handler triggered by SQS.
    """
    for record in event.get('Records', []):
        body = json.loads(record['body'])
        task_type = body.get('type')
        email = body.get('email')
        payload = body.get('payload', {})

        print(f"Processing task: {task_type} for {email}")

        try:
            if task_type == 'welcome_email':
                full_name = payload.get('full_name', '')
                send_welcome_email(email, full_name)
            elif task_type == 'verification_email':
                otp = payload.get('otp', '')
                send_verification_email(email, otp)
            elif task_type == 'password_reset_email':
                otp = payload.get('otp', '')
                send_password_reset_email(email, otp)
            else:
                print(f"Unknown task type: {task_type}")
        except Exception as e:
            print(f"Failed to process record for {email}: {str(e)}")
            raise e

def send_welcome_email(email, full_name):
    html = get_welcome_email_html(full_name)
    send_email(email, "Welcome to ThinkAloudAI", html)

def send_verification_email(email, otp):
    html = get_verification_email_html(otp)
    send_email(email, "Verify your email - ThinkAloudAI", html)

def send_password_reset_email(email, otp):
    html = get_password_reset_email_html(otp)
    send_email(email, "Reset your password - ThinkAloudAI", html)

def send_email(to_email, subject, html):
    if not resend.api_key:
        print("RESEND_API_KEY is not set. Skipping email delivery.")
        return

    params = {
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": html,
    }
    
    response = resend.Emails.send(params)
    print(f"Email sent successfully. Response: {response}")
