import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger("uvicorn")


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via Gmail SMTP. Returns True if sent, False if failed."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"HaqDesk AI <{settings.MAIL_FROM}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_email_as_business(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    from_password: str,
    from_name: str = "TechSuru Support"
) -> bool:
    """Send email using the business's own Gmail credentials."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.starttls()
            server.login(from_email, from_password)
            server.sendmail(from_email, to_email, msg.as_string())

        logger.info(f"Email sent from {from_email} to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email from {from_email} to {to_email}: {e}")
        return False


def send_invite_email(to_email: str, invite_url: str, business_name: str, role: str, inviter_name: str) -> bool:
    """Send a team invitation email."""
    subject = f"You've been invited to join {business_name} on HaqDesk AI"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #6D4AE2; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">HaqDesk AI</h1>
        </div>
        <div style="background: #f9f9f9; padding: 32px; border-radius: 0 0 12px 12px;">
            <h2 style="color: #1a1a2e; margin-top: 0;">You're invited!</h2>
            <p style="color: #444; font-size: 15px; line-height: 1.6;">
                <strong>{inviter_name}</strong> has invited you to join
                <strong>{business_name}</strong> as a <strong>{role}</strong> on HaqDesk AI —
                an AI-powered customer support platform.
            </p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{invite_url}"
                   style="background: #6D4AE2; color: white; padding: 14px 32px;
                          border-radius: 10px; text-decoration: none; font-weight: bold;
                          display: inline-block;">
                    Accept Invitation
                </a>
            </div>
            <p style="color: #888; font-size: 13px; line-height: 1.5;">
                This invite link expires in 7 days. If you weren't expecting this email,
                you can safely ignore it.
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 24px;">
                Or copy this link: <br>
                <span style="color: #6D4AE2;">{invite_url}</span>
            </p>
        </div>
        <p style="text-align: center; color: #aaa; font-size: 11px; margin-top: 16px;">
            © 2026 HaqDesk AI. All rights reserved.
        </p>
    </div>
    """

    return send_email(to_email, subject, html_body)


def send_password_reset_email(to_email: str, reset_url: str, user_name: str) -> bool:
    """Send a password reset email."""
    subject = "Reset your HaqDesk AI password"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #6D4AE2; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">HaqDesk AI</h1>
        </div>
        <div style="background: #f9f9f9; padding: 32px; border-radius: 0 0 12px 12px;">
            <h2 style="color: #1a1a2e; margin-top: 0;">Reset your password</h2>
            <p style="color: #444; font-size: 15px; line-height: 1.6;">
                Hi {user_name},<br><br>
                We received a request to reset your HaqDesk AI password. Click the button
                below to set a new password.
            </p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_url}"
                   style="background: #6D4AE2; color: white; padding: 14px 32px;
                          border-radius: 10px; text-decoration: none; font-weight: bold;
                          display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #888; font-size: 13px; line-height: 1.5;">
                This link expires in 1 hour. If you didn't request this, you can safely
                ignore this email — your password will not be changed.
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 24px;">
                Or copy this link: <br>
                <span style="color: #6D4AE2;">{reset_url}</span>
            </p>
        </div>
        <p style="text-align: center; color: #aaa; font-size: 11px; margin-top: 16px;">
            © 2026 HaqDesk AI. All rights reserved.
        </p>
    </div>
    """

    return send_email(to_email, subject, html_body)